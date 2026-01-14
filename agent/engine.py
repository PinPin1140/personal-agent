"""Main agent engine loop for task execution."""
from typing import Optional, Dict, Any
import time

from .task import Task, TaskStatus
from .memory import TaskRepository
from .models import ModelProvider, ProviderRegistry
from .executor import ToolExecutor


class AgentEngine:
    """Deterministic main loop for task execution."""

    def __init__(
        self,
        task_repo: TaskRepository,
        model_provider: ModelProvider,
        working_dir: Optional[str] = None
    ):
        self.task_repo = task_repo
        self.model_provider = model_provider
        self.executor = ToolExecutor(working_dir=working_dir)
        self._running = False

    def run_single_task(self, task_id: Optional[int] = None) -> Optional[Task]:
        """
        Run one task from start to completion.

        If task_id provided, run that specific task.
        Otherwise, pick next runnable task.
        """
        if task_id:
            task = self.task_repo.get(task_id)
            if not task:
                print(f"Task {task_id} not found")
                return None
        else:
            task = self._pick_next_task()
            if not task:
                print("No runnable tasks")
                return None

        return self._execute_task(task)

    def _pick_next_task(self) -> Optional[Task]:
        """Pick the next pending task by ID order."""
        for task in self.task_repo.list_all():
            if task.status == TaskStatus.PENDING:
                return task
        return None

    def _execute_task(self, task: Task) -> Task:
        """Execute a single task step by step."""
        task.update_status(TaskStatus.RUNNING)
        self.task_repo.update(task)

        try:
            self._run_task_loop(task)
        except Exception as e:
            task.add_step("error", error=str(e))
            task.update_status(TaskStatus.ERROR)
            self.task_repo.update(task)
            print(f"Task {task.id} failed: {e}")

        return task

    def _run_task_loop(self, task: Task, max_steps: int = 10):
        """Run task through decision and execution loop."""
        step_count = 0

        while step_count < max_steps and task.status == TaskStatus.RUNNING:
            step_count += 1

            context = self._build_context(task)
            decision = self.model_provider.generate(
                prompt=f"Task goal: {task.goal}\nCurrent step: {step_count}",
                context=context
            )

            task.add_step("decision", result=decision)
            self.task_repo.update(task)

            if self._is_complete(decision):
                task.update_status(TaskStatus.DONE)
                self.task_repo.update(task)
                print(f"Task {task.id} completed")
                break

            action_result = self._execute_action(decision, task)
            if action_result.get("error"):
                raise Exception(action_result["error"])

            task.add_step("action", result=action_result.get("output", ""))
            self.task_repo.update(task)

        if task.status == TaskStatus.RUNNING:
            task.update_status(TaskStatus.DONE)
            self.task_repo.update(task)
            print(f"Task {task.id} completed (max steps reached)")

    def _build_context(self, task: Task) -> Dict[str, Any]:
        """Build context for model from task state."""
        return {
            "task_id": task.id,
            "goal": task.goal,
            "status": task.status.value,
            "steps": task.steps[-3:],
            "memory": task.memory
        }

    def _is_complete(self, decision: str) -> bool:
        """Check if decision indicates task completion."""
        complete_markers = ["done", "complete", "finished", "finished", "success"]
        return any(
            marker.lower() in decision.lower()
            for marker in complete_markers
        )

    def _execute_action(self, decision: str, task: Task) -> Dict[str, Any]:
        """Parse and execute action from decision."""
        if "shell:" in decision.lower():
            cmd = decision.split("shell:", 1)[1].strip()
            exit_code, stdout, stderr = self.executor.execute_shell(cmd)

            if stderr:
                return {"error": stderr, "output": stdout}
            return {"output": stdout}

        return {"output": "No action executed"}

    def pause_task(self, task_id: int) -> bool:
        """Pause a running task."""
        task = self.task_repo.get(task_id)
        if task and task.status == TaskStatus.RUNNING:
            task.update_status(TaskStatus.PAUSED)
            self.task_repo.update(task)
            print(f"Task {task_id} paused")
            return True
        print(f"Cannot pause task {task_id}")
        return False

    def resume_task(self, task_id: int) -> Optional[Task]:
        """Resume a paused task."""
        task = self.task_repo.get(task_id)
        if not task:
            print(f"Task {task_id} not found")
            return None

        if task.status != TaskStatus.PAUSED:
            print(f"Task {task_id} is not paused")
            return None

        return self._execute_task(task)
