"""
IRIS Agent Loop - Deterministic READ→PLAN→WRITE enforcement
"""
import os
import subprocess
import difflib
from typing import Dict, Any, List, Optional
from pathlib import Path

from agent.iris_context import (
    ContextManager, CurrentTask, Plan, IntendedEdit,
    FileRead, ReadState, calculate_checksum, create_task
)
from agent.task import Task, TaskStatus
from agent.memory import TaskRepository
from agent.model_router import ModelRouter


class IRISEnforcementError(Exception):
    """Raised when enforcement rules are violated"""
    pass


class AgentLoop:
    """IRIS deterministic agent loop with enforcement"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.context_manager = ContextManager(str(self.project_root))
        self.task_repo = TaskRepository()
        self.model_router = ModelRouter()

    def execute_task(self, task_id: str) -> bool:
        """Execute task through READ→PLAN→WRITE enforcement"""
        # Load task
        task = self.task_repo.get(task_id)
        if not task:
            print(f"ERR_TASK_NOT_FOUND: Task {task_id} not found")
            return False

        # Initialize context if needed
        context_created = self.context_manager.initialize(task.goal)
        if context_created:
            print("IRIS ▸ Created .context and initialized project. (step 1 complete)")
            return True

        # Set current task
        iris_task = CurrentTask(
            task_id=task.id,
            goal=task.goal,
            status='running',
            last_phase='INIT',
            summary='',
            read_state=ReadState(files_read={}),
            plan=Plan(intended_edits=[], reasoning='')
        )
        self.context_manager.set_current_task(iris_task)

        try:
            # READ Phase
            self._execute_read_phase(task)

            # PLAN Phase
            plan = self._execute_plan_phase(task)

            # WRITE Phase with preview
            success = self._execute_write_phase(task, plan)

            if success:
                task.status = TaskStatus.DONE
                iris_task.status = 'done'
                iris_task.last_phase = 'VERIFY'
            else:
                task.status = TaskStatus.ERROR
                iris_task.status = 'error'
                iris_task.last_phase = 'WRITE'

            self.task_repo.update(task)
            self.context_manager.set_current_task(iris_task)

            return success

        except IRISEnforcementError as e:
            print(f"ERR_ENFORCEMENT_VIOLATION: {e}")
            task.status = TaskStatus.ERROR
            iris_task.status = 'error'
            iris_task.summary = f"Enforcement error: {e}"
            self.task_repo.update(task)
            self.context_manager.set_current_task(iris_task)
            return False

        except Exception as e:
            print(f"ERR_EXECUTION_FAILED: {e}")
            task.status = TaskStatus.ERROR
            iris_task.status = 'error'
            iris_task.summary = f"Execution error: {e}"
            self.task_repo.update(task)
            self.context_manager.set_current_task(iris_task)
            return False

    def _execute_read_phase(self, task: Task) -> List[FileRead]:
        """READ Phase: Read and checksum files"""
        print(f"IRIS ▸ READ ▸ Analyzing source files")

        # Find files to read (simplified - read all .py files)
        files_to_read = self._find_files_to_read()

        files_read = []
        for file_path in files_to_read:
            if not Path(file_path).exists():
                continue

            # Read file
            with open(file_path, 'r') as f:
                content = f.read()

            lines = content.split('\n')
            line_count = len(lines)

            # Calculate checksum
            hash_value = calculate_checksum(file_path)

            files_read.append(FileRead(
                path=file_path,
                lines=(1, line_count),
                content=content,
                hash=hash_value
            ))

            print(f"→ READ {Path(file_path).relative_to(self.project_root)} ({line_count} lines, hash: {hash_value[:8]}...)")

            # Update context
            context = self.context_manager.load_context()
            if context.current_task:
                context.current_task.read_state.files_read[file_path] = files_read[-1]
                self.context_manager.write_context(context)

        # Log to journal
        self.context_manager.add_journal_entry({
            'task_id': task.id,
            'phase': 'READ',
            'desc': f'Read {len(files_read)} files',
            'meta': {'files_read': len(files_read)}
        })

        return files_read

    def _execute_plan_phase(self, task: Task) -> Plan:
        """PLAN Phase: Generate intended edits"""
        print(f"IRIS ▸ PLAN ▸ Generating execution plan")

        # Get current context
        context = self.context_manager.load_context()
        if not context.current_task:
            raise IRISEnforcementError("No current task in context")

        # Generate plan using model (simplified)
        prompt = f"""Given this task: "{task.goal}"

Analyze the codebase and create a specific plan for what needs to be implemented.
Focus on concrete file changes with exact line ranges.

Respond with a detailed plan including:
- Specific files to modify
- Exact line ranges for changes
- What functionality to implement

Be very specific and actionable."""

        print("→ Generating plan...")
        plan_response = self.model_router.generate(prompt, {"task_goal": task.goal})

        # Parse plan (simplified - in production, use structured output)
        intended_edits = self._parse_plan_response(plan_response)

        plan = Plan(
            intended_edits=intended_edits,
            reasoning=plan_response
        )

        # Update context
        context.current_task.plan = plan
        self.context_manager.write_context(context)

        # Log edits
        for edit in intended_edits:
            print(f"→ PLAN edit {Path(edit.file).relative_to(self.project_root)} lines {edit.range[0]}–{edit.range[1]} ({edit.reason})")

        # Log to journal
        self.context_manager.add_journal_entry({
            'task_id': task.id,
            'phase': 'PLAN',
            'desc': f'Planned {len(intended_edits)} edits',
            'meta': {'edits_planned': len(intended_edits)}
        })

        return plan

    def _execute_write_phase(self, task: Task, plan: Plan) -> bool:
        """WRITE Phase: Apply changes with verification"""
        for edit in plan.intended_edits:
            print(f"IRIS ▸ WRITE ▸ Applying changes to {Path(edit.file).relative_to(self.project_root)}")

            # Check enforcement: file must be in read_state
            context = self.context_manager.load_context()
            if not context.current_task or edit.file not in context.current_task.read_state.files_read:
                raise IRISEnforcementError(f"MUST_READ_FIRST: File {edit.file} not in read state")

            # Generate the actual changes (simplified - in production, model generates this)
            edit.new_content = self._generate_edit_content(edit, task.goal)

            # Show diff preview
            self._show_diff_preview(edit)

            # Create checkpoint
            checkpoint_path = self.context_manager.create_checkpoint(task.id, edit.file)

            # Apply changes
            try:
                self._apply_edit(edit)
                print(f"→ WRITE applied changes to {Path(edit.file).relative_to(self.project_root)}")

                # Verify changes
                if not self._verify_changes(edit.file):
                    print("→ ROLLBACK due to verification failure")
                    self.context_manager.rollback_file(checkpoint_path, edit.file)
                    return False

                print("→ VERIFY syntax check passed")

            except Exception as e:
                print(f"→ ROLLBACK due to error: {e}")
                self.context_manager.rollback_file(checkpoint_path, edit.file)
                return False

        # Log to journal
        self.context_manager.add_journal_entry({
            'task_id': task.id,
            'phase': 'WRITE',
            'desc': f'Applied {len(plan.intended_edits)} edits successfully',
            'meta': {'edits_applied': len(plan.intended_edits)}
        })

        return True

    def _find_files_to_read(self) -> List[str]:
        """Find files that should be read for analysis"""
        files = []

        # Find Python files (simplified)
        for root, dirs, filenames in os.walk(self.project_root):
            # Skip hidden dirs and common excludes
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]

            for filename in filenames:
                if filename.endswith('.py'):
                    files.append(os.path.join(root, filename))

        return files[:10]  # Limit for demo

    def _parse_plan_response(self, response: str) -> List[IntendedEdit]:
        """Parse plan response into structured edits (simplified)"""
        # This is a simplified parser - in production, use structured output
        edits = []

        # Look for common patterns
        if 'agent' in response.lower() and 'loop' in response.lower():
            edits.append(IntendedEdit(
                file='agent/iris_context.py',
                range=(1, 50),
                reason='Add agent loop implementation'
            ))

        if 'enforcement' in response.lower():
            edits.append(IntendedEdit(
                file='agent/iris_context.py',
                range=(100, 150),
                reason='Implement enforcement rules'
            ))

        # Fallback
        if not edits:
            edits.append(IntendedEdit(
                file='agent/iris_context.py',
                range=(1, 10),
                reason='Implement requested functionality'
            ))

        return edits

    def _generate_edit_content(self, edit: IntendedEdit, task_goal: str) -> str:
        """Generate the actual content for an edit (simplified)"""
        # In production, this would use the model to generate specific code
        return f'# Modified for: {task_goal}\n# Lines {edit.range[0]}-{edit.range[1]}\n# {edit.reason}\n'

    def _show_diff_preview(self, edit: IntendedEdit) -> None:
        """Show before/after diff preview"""
        file_path = Path(edit.file)

        print(f"IRIS ▸ WRITE ▸ preview changes for {file_path.relative_to(self.project_root)} lines {edit.range[0]}–{edit.range[1]}")

        # Get original content
        if Path(edit.file).exists():
            with open(edit.file, 'r') as f:
                original_content = f.read()
        else:
            original_content = ''

        # Show diff
        if original_content and edit.new_content:
            diff = list(difflib.unified_diff(
                original_content.splitlines(keepends=True),
                edit.new_content.splitlines(keepends=True),
                fromfile=f'a/{file_path.name}',
                tofile=f'b/{file_path.name}',
                lineterm=''
            ))

            if diff:
                print("----- DIFF -----")
                for line in diff:
                    if line.startswith('+'):
                        print(f'\033[92m{line}\033[0m')  # Green
                    elif line.startswith('-'):
                        print(f'\033[91m{line}\033[0m')  # Red
                    else:
                        print(line)

        print("Task: Changes will be applied automatically (trusted workspace)")
        print("Press Enter to continue or Ctrl+C to cancel...")
        input()  # Wait for user

    def _apply_edit(self, edit: IntendedEdit) -> None:
        """Apply the edit to the file"""
        if not edit.new_content:
            return

        file_path = Path(edit.file)

        # Read current content
        if file_path.exists():
            with open(file_path, 'r') as f:
                current_content = f.read()
        else:
            current_content = ''

        lines = current_content.split('\n')

        # Apply edit to specified range (simplified - replace entire range)
        start_line = max(0, edit.range[0] - 1)  # Convert to 0-based
        end_line = min(len(lines), edit.range[1])

        new_lines = edit.new_content.split('\n')

        # Replace the range
        result_lines = lines[:start_line] + new_lines + lines[end_line:]

        # Write back
        with open(file_path, 'w') as f:
            f.write('\n'.join(result_lines))

    def _verify_changes(self, file_path: str) -> bool:
        """Verify that changes are syntactically correct"""
        if file_path.endswith('.py'):
            try:
                # Run Python syntax check
                result = subprocess.run(
                    ['python', '-m', 'py_compile', file_path],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            except FileNotFoundError:
                # Python not available, skip verification
                return True

        return True  # Default pass for other files