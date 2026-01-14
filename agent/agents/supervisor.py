"""Supervisor agent for managing worker agents."""
from typing import Dict, Any, Optional, List
from .base import BaseAgent
from .executor import WorkerAgent
from ..task import Task, TaskStatus
from ..memory import TaskRepository
from ..tools.registry import ToolRegistry
from ..model_router import ModelRouter
from ..skills.registry import SkillRegistry


class SupervisorAgent(BaseAgent):
    """Supervisor that assigns tasks to workers and monitors progress."""

    def __init__(
                self,
                tool_registry: ToolRegistry,
                model_router: ModelRouter,
                task_repo: TaskRepository,
                skill_registry: Optional[SkillRegistry] = None,
                max_workers: int = 1
    ):
        super().__init__(tool_registry)
        self.model_router = model_router
        self.task_repo = task_repo
        self.skill_registry = skill_registry
        self.max_workers = max_workers
        self._workers: List[WorkerAgent] = []

        # Initialize workers
        for i in range(max_workers):
                worker = WorkerAgent(tool_registry, model_router, skill_registry)
                self._workers.append(worker)

        self._task_queue: List[Task] = []
        self._status = "idle"

    def execute(self, task: Task) -> Dict[str, Any]:
        """Assign task to next available worker."""
        # Find available worker
        for worker in self._workers:
                if worker.get_status() == "idle":
                        self._status = "dispatching"
                        result = worker.execute(task)
                        self._status = "idle"
                        return result

        # No workers available
        self._task_queue.append(task)
        self._status = "queued"
        return {
                "success": False,
                "steps_completed": 0,
                "error": "No workers available, task queued"
        }

    def process_queue(self) -> int:
        """Process pending tasks in queue."""
        processed = 0

        while self._task_queue:
                for worker in self._workers:
                        if worker.get_status() == "idle":
                                task = self._task_queue.pop(0)
                                result = worker.execute(task)
                                processed += 1

                                if not result.get("success", False):
                                        print(f"[SUPERVISOR] Task {task.id} failed: {result.get('error')}")

                                break

                if not self._task_queue:
                        break

        return processed

    def get_status(self) -> str:
        """Get supervisor status."""
        return self._status

    def get_worker_status(self) -> list[Dict[str, Any]]:
        """Get status of all workers."""
        return [
                {
                        "worker_id": i,
                        "status": worker.get_status()
                }
                for i, worker in enumerate(self._workers)
        ]

    def run_all_pending(self, max_steps: int = 10) -> Dict[str, Any]:
        """Run all pending tasks through workers."""
        tasks = self.task_repo.list_all()
        pending = [t for t in tasks if t.status == TaskStatus.PENDING]

        results = {
                "total": len(pending),
                "completed": 0,
                "failed": 0,
                "queued": 0
        }

        self._status = "processing"

        for task in pending:
                task.update_status(TaskStatus.RUNNING)
                self.task_repo.update(task)

                result = self.execute(task)

                if result.get("success", False):
                        results["completed"] += 1
                        print(f"[SUPERVISOR] Task {task.id} completed")
                else:
                        results["failed"] += 1
                        task.update_status(TaskStatus.ERROR)
                        print(f"[SUPERVISOR] Task {task.id} failed: {result.get('error')}")

                self.task_repo.update(task)

        # Process any remaining queue
        queued = self.process_queue()
        results["queued"] = queued

        self._status = "idle"
        return results
