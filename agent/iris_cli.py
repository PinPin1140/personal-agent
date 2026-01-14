"""
IRIS CLI Commands - Deterministic autonomous task execution
"""
import sys
from pathlib import Path

from agent.iris_context import ContextManager, create_task
from agent.iris_loop import AgentLoop
from agent.task import Task
from agent.memory import TaskRepository


class IRISNewCommand:
    """Create new IRIS task and initialize context"""

    def execute(self, goal: str):
        context_manager = ContextManager()
        task_repo = TaskRepository()

        try:
            # Initialize context if needed
            context_created = context_manager.initialize(goal)

            if context_created:
                print("IRIS ▸ Created .context and initialized project. (step 1 complete)")
                return

            # Create new task
            iris_task = create_task(goal)

            # Also create in personal-agent task repo for compatibility
            task = Task()
            task.id = iris_task.task_id
            task.goal = goal
            task.status = Task.Status.PENDING
            task_repo.save(task)

            # Set as current task in context
            context_manager.set_current_task(iris_task)

            print(f"IRIS ▸ Created task {task.id}: {task.goal}")

        except Exception as e:
            print(f"Failed to create IRIS task: {e}")
            sys.exit(1)


class IRISListCommand:
    """List IRIS tasks"""

    def execute(self):
        context_manager = ContextManager()

        try:
            context = context_manager.load_context()

            if not context.current_task:
                print("No current IRIS task.")
                return

            task = context.current_task
            status = f"[{task.status.upper()}]"
            print("Current IRIS Task:")
            print(f"  {status} {task.task_id}: {task.goal}")
            print(f"  Phase: {task.last_phase}")
            print(f"  Files read: {len(task.read_state.files_read)}")
            print(f"  Planned edits: {len(task.plan.intended_edits)}")

        except Exception as e:
            print(f"Failed to list IRIS tasks: {e}")
            sys.exit(1)


class IRISRunCommand:
    """Execute IRIS task with full enforcement"""

    def execute(self, task_id: str):
        agent_loop = AgentLoop()

        try:
            success = agent_loop.execute_task(task_id)

            if success:
                print("IRIS ▸ DONE ▸ Task finished (status: done)")
                sys.exit(0)
            else:
                print("IRIS ▸ ERROR ▸ Task failed")
                sys.exit(1)

        except Exception as e:
            print(f"Failed to run IRIS task: {e}")
            sys.exit(1)


class IRISAttachCommand:
    """Attach to running IRIS task with live UI"""

    def execute(self, task_id: str):
        context_manager = ContextManager()

        try:
            context = context_manager.load_context()

            if not context.current_task or context.current_task.task_id != task_id:
                print(f"Task {task_id} not found or not current task")
                sys.exit(1)

            task = context.current_task

            print(f"IRIS ▸ ATTACHED ▸ {task.goal}")
            print(f"Status: {task.status}")
            print(f"Phase: {task.last_phase}")
            print(f"Summary: {task.summary}")

            # Load and display recent journal entries
            journal = context_manager.load_journal()
            recent_entries = journal.entries[-5:]  # Last 5

            if recent_entries:
                print("\nRecent activity:")
                for entry in recent_entries:
                    print(f"  {entry.ts[:19]} [{entry.phase}] {entry.desc}")

            print("\n(Live attachment UI not fully implemented)")
            print("Task execution continues in background.")

        except Exception as e:
            print(f"Failed to attach to IRIS task: {e}")
            sys.exit(1)


class IRISLogsCommand:
    """View IRIS task execution logs"""

    def execute(self, task_id: str):
        context_manager = ContextManager()

        try:
            journal = context_manager.load_journal()

            # Filter entries for this task
            task_entries = [e for e in journal.entries if e.task_id == task_id]

            if not task_entries:
                print(f"No logs found for task {task_id}")
                return

            print(f"Task {task_id} execution logs:\n")

            for entry in task_entries:
                timestamp = entry.ts[:19]  # YYYY-MM-DDTHH:MM:SS
                print(f"[{entry.phase}] {timestamp}")
                print(f"  {entry.desc}")

                if entry.meta:
                    print(f"  Meta: {entry.meta}")

                print()

        except Exception as e:
            print(f"Failed to retrieve IRIS logs: {e}")
            sys.exit(1)