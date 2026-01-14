"""Supervisor agent for managing worker agents with concurrent execution."""
import threading
import time
from typing import Dict, Any, Optional, List, Set
from queue import Queue, PriorityQueue
from .base import BaseAgent
from .executor import WorkerAgent
from ..task import Task, TaskStatus
from ..memory import TaskRepository
from ..tools.registry import ToolRegistry
from ..model_router import ModelRouter
from ..skills.registry import SkillRegistry
from ..commands.registry import CommandRegistry
from ..profiles.base import AgentProfile


class SupervisorAgent(BaseAgent):
    """Supervisor that manages concurrent workers with task decomposition and collaboration."""

    def __init__(
                self,
                tool_registry: ToolRegistry,
                model_router: ModelRouter,
                task_repo: TaskRepository,
                skill_registry: Optional[SkillRegistry] = None,
                command_registry: Optional[CommandRegistry] = None,
                profile: Optional[AgentProfile] = None,
                max_workers: int = 3
    ):
        super().__init__(tool_registry)
        self.model_router = model_router
        self.task_repo = task_repo
        self.skill_registry = skill_registry
        self.command_registry = command_registry
        self.profile = profile
        self.max_workers = max_workers
        self._workers: List[WorkerAgent] = []
        self._worker_threads: List[threading.Thread] = []

        # Concurrent execution components
        self._task_queue: PriorityQueue = PriorityQueue()  # (priority, task_id, task)
        self._active_tasks: Dict[int, Task] = {}  # task_id -> task
        self._worker_assignments: Dict[int, int] = {}  # task_id -> worker_id
        self._subtask_relationships: Dict[int, Set[int]] = {}  # parent_task_id -> set of subtask_ids

        # Communication and coordination
        self._message_queue: Queue = Queue()
        self._shared_memory: Dict[str, Any] = {}
        self._locks: Dict[str, threading.Lock] = {}

        # Initialize workers and threads
        self._initialize_workers()
        self._start_worker_threads()

        self._status = "idle"
        return results

    def shutdown(self):
        """Shutdown all worker threads."""
        self._shutdown_event.set()
        self._status = "shutdown"

        # Wait for threads to finish
        for thread in self._worker_threads:
                thread.join(timeout=5.0)

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
        """Load all pending tasks into concurrent execution and wait for completion."""
        # Load pending tasks into queue
        queued = self.process_pending_tasks()

        results = {
                "total": queued,
                "completed": 0,
                "failed": 0,
                "queued": queued,
                "active_workers": len(self._workers)
        }

        self._status = "processing"

        # Wait for all tasks to complete
        start_time = time.time()
        timeout = 300  # 5 minutes timeout

        while not self._task_queue.empty() and (time.time() - start_time) < timeout:
                # Check active tasks periodically
                with self._get_lock("active_tasks"):
                        active_count = len(self._active_tasks)

                if active_count == 0 and self._task_queue.empty():
                        break

                time.sleep(1)  # Brief pause

        # Final status
        tasks = self.task_repo.list_all()
        results["completed"] = len([t for t in tasks if t.status == TaskStatus.DONE])
        results["failed"] = len([t for t in tasks if t.status == TaskStatus.ERROR])

        self._status = "idle"
        return results
