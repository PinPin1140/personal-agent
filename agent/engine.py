"""Main agent engine loop for task execution."""
from typing import Optional
from .task import Task, TaskStatus
from .memory import TaskRepository
from .model_router import ModelRouter
from .agents.supervisor import SupervisorAgent
from .tools.registry import ToolRegistry, ShellTool, FileReadTool, FileWriteTool, ListDirTool
from .skills.registry import SkillRegistry


class AgentEngine:
    """Deterministic main loop for task execution with multi-agent support."""

    def __init__(
        self,
        task_repo: TaskRepository,
        model_router: ModelRouter,
        working_dir: Optional[str] = None,
        max_workers: int = 1
    ):
        self.task_repo = task_repo
        self.model_router = model_router

        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self._register_default_tools()

        # Initialize skill registry
        self.skill_registry = SkillRegistry()

        # Initialize supervisor with workers
        self.supervisor = SupervisorAgent(
                tool_registry=self.tool_registry,
                model_router=model_router,
                task_repo=task_repo,
                skill_registry=self.skill_registry,
                max_workers=max_workers
        )

    def _register_default_tools(self):
        """Register default tools."""
        self.tool_registry.register(ShellTool())
        self.tool_registry.register(FileReadTool())
        self.tool_registry.register(FileWriteTool())
        self.tool_registry.register(ListDirTool())

    def run_single_task(self, task_id: Optional[int] = None) -> Optional[Task]:
        """Run one task using multi-agent system."""
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

        return self._execute_task_with_supervisor(task)

    def run_all_pending(self) -> dict:
        """Run all pending tasks through multi-agent system."""
        results = self.supervisor.run_all_pending()
        print(f"\nResults: {results['completed']} completed, {results['failed']} failed, {results['queued']} queued")
        return results

    def _pick_next_task(self) -> Optional[Task]:
        """Pick next pending task by ID order."""
        for task in self.task_repo.list_all():
                if task.status == TaskStatus.PENDING:
                        return task
        return None

    def _execute_task_with_supervisor(self, task: Task) -> Task:
        """Execute task using supervisor agent."""
        try:
                result = self.supervisor.execute(task)

                if result.get("success", False):
                        task.update_status(TaskStatus.DONE)
                        print(f"Task {task.id} completed")
                else:
                        task.update_status(TaskStatus.ERROR)
                        error_msg = result.get("error", "Unknown error")
                        print(f"Task {task.id} failed: {error_msg}")

                self.task_repo.update(task)
                return task

        except Exception as e:
                task.add_step("error", error=str(e))
                task.update_status(TaskStatus.ERROR)
                self.task_repo.update(task)
                print(f"Task {task.id} failed: {e}")
                return task

    def pause_task(self, task_id: int) -> bool:
        """Pause a running task (not supported in multi-agent mode)."""
        print("Pause not supported in multi-agent autonomous mode")
        return False

    def resume_task(self, task_id: int) -> Optional[Task]:
        """Resume a paused task (not supported in multi-agent mode)."""
        print("Resume not supported in multi-agent autonomous mode")
        return None

    def get_worker_status(self) -> list[dict]:
        """Get status of all worker agents."""
        return self.supervisor.get_worker_status()
