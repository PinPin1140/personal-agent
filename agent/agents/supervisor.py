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
                max_workers: int = 3,
                # Integrated systems
                model_metrics=None,
                router_policy=None,
                account_rotator=None,
                node_registry=None,
                plugin_registry=None,
                sandbox=None,
                syscall_filter=None
    ):
        super().__init__(tool_registry)
        self.model_router = model_router
        self.task_repo = task_repo
        self.skill_registry = skill_registry
        self.command_registry = command_registry
        self.profile = profile
        self.max_workers = max_workers

        # Integrated systems
        self.model_metrics = model_metrics
        self.router_policy = router_policy
        self.account_rotator = account_rotator
        self.node_registry = node_registry
        self.plugin_registry = plugin_registry
        self.sandbox = sandbox
        self.syscall_filter = syscall_filter
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

    def _initialize_workers(self):
        """Initialize worker agents with all integrated systems."""
        for i in range(self.max_workers):
            worker = WorkerAgent(
                tool_registry=self.tool_registry,
                model_router=self.model_router,
                skill_registry=self.skill_registry,
                command_registry=self.command_registry,
                profile=self.profile,
                # Pass security systems
                sandbox=self.sandbox,
                syscall_filter=self.syscall_filter
            )
            self._workers.append(worker)

    def _should_delegate_to_remote(self, task: Task) -> Optional[str]:
        """Check if task should be delegated to remote node based on profile."""
        if not self.node_registry:
            return None

        # Profile-driven remote delegation decision
        if self.profile:
            # Conservative profiles avoid remote delegation
            if self.profile.risk_tolerance < 0.3:
                return None

            # Speed-focused profiles prefer local execution for lower latency
            if self.profile.speed_vs_accuracy > 0.7:
                return None

            # Cost-sensitive profiles may prefer remote if cheaper
            # (This would require cost comparison logic)

        # Find available remote node with required capabilities
        capabilities = ["general"]  # Basic capability requirement

        remote_node = self.node_registry.find_available(capabilities)
        if remote_node:
            return remote_node.node_id

        return None

    def _delegate_to_remote_node(self, task: Task, node_id: str) -> bool:
        """Delegate task execution to remote node."""
        if not self.node_registry:
            return False

        node = self.node_registry.get_node(node_id)
        if not node:
            return False

        try:
            # Send task to remote node via protocol
            # This is a placeholder for actual remote communication
            # In full implementation, would use the protocol module
            print(f"Delegating task {task.id} to remote node {node_id}")
            # node.send_task(task)
            return True
        except Exception as e:
            print(f"Failed to delegate task to remote node: {e}")
            return False

    def execute(self, task: Task) -> Dict[str, Any]:
        """Execute task with plugin hooks integration."""
        # Trigger before_task hooks
        if self.plugin_registry:
            self.plugin_registry.trigger_hooks("before_task", {
                "task": task,
                "supervisor": self
            })

        try:
            # Check for remote delegation first
            remote_node_id = self._should_delegate_to_remote(task)
            if remote_node_id:
                success = self._delegate_to_remote_node(task, remote_node_id)
                if success:
                    result = {"success": True, "remote_delegated": True}
                else:
                    # Fallback to local execution
                    result = self._execute_locally(task)
            else:
                result = self._execute_locally(task)

            # Trigger after_task hooks
            if self.plugin_registry:
                self.plugin_registry.trigger_hooks("after_task", {
                    "task": task,
                    "result": result,
                    "supervisor": self
                })

            return result

        except Exception as e:
            # Trigger after_task hooks even on failure
            if self.plugin_registry:
                self.plugin_registry.trigger_hooks("after_task", {
                    "task": task,
                    "error": str(e),
                    "supervisor": self
                })
            raise

    def _execute_locally(self, task: Task) -> Dict[str, Any]:
        """Execute task using local workers with profile-driven behavior."""
        if not self._workers:
            return {"success": False, "error": "No workers available"}

        # Profile-driven worker selection and execution
        if self.profile:
            # Collaboration mode affects execution strategy
            if self.profile.collaboration_mode == "cooperative":
                # Use multiple workers for cooperative execution
                return self._execute_cooperative(task)
            elif self.profile.collaboration_mode == "competitive":
                # Race workers against each other
                return self._execute_competitive(task)
            else:  # independent
                # Use single worker
                return self._workers[0].execute(task)
        else:
            # Default: single worker execution
            return self._workers[0].execute(task)

    def _execute_cooperative(self, task: Task) -> Dict[str, Any]:
        """Execute task cooperatively across multiple workers."""
        # Placeholder for cooperative execution
        # In full implementation, would break task into subtasks
        if self.profile and self.profile.task_decomposition:
            # Decompose task and assign to multiple workers
            pass

        # Fallback to single worker
        return self._workers[0].execute(task) if self._workers else {"success": False, "error": "No workers available"}

    def _execute_competitive(self, task: Task) -> Dict[str, Any]:
        """Execute task competitively across workers."""
        # Placeholder for competitive execution
        # Race multiple workers and return best result
        return self._workers[0].execute(task) if self._workers else {"success": False, "error": "No workers available"}

    def get_status(self) -> str:
        """Get current supervisor status."""
        if not self._workers:
            return "no_workers"

        active_tasks = len(self._active_tasks)
        if active_tasks > 0:
            return f"active_{active_tasks}_tasks"
        else:
            return "idle"

    def _start_worker_threads(self):
        """Start worker threads."""
        # Implementation will be added in concurrent execution
        # For now, just set status
        self._status = "idle"

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
