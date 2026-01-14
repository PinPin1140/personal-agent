"""Main agent engine orchestrating all systems for autonomous execution."""
import os
from typing import Optional, Dict, Any
from .task import Task, TaskStatus
from .memory import TaskRepository
from .model_router import ModelRouter
from .agents.supervisor import SupervisorAgent
from .tools.registry import ToolRegistry, ShellTool, FileReadTool, FileWriteTool, ListDirTool
from .skills.registry import SkillRegistry
from .commands.registry import CommandRegistry
from .profiles.registry import ProfileRegistry
from .model_metrics import ModelMetrics
from .router_policy import RouterPolicy
from .auth.accounts import AccountManager
from .auth.rotation import AccountRotator
from .remote.registry import NodeRegistry
from .plugins.registry import PluginRegistry
from .security.sandbox import ProcessSandbox
from .security.syscall import SyscallFilter


class AgentEngine:
    """Unified engine orchestrating all autonomous agent systems."""

    def __init__(
        self,
        task_repo: TaskRepository,
        working_dir: Optional[str] = None,
        max_workers: int = 3,
        enable_security: bool = True
    ):
        self.task_repo = task_repo
        self.working_dir = working_dir or os.getcwd()
        self.max_workers = max_workers
        self.enable_security = enable_security

        # Initialize core components in dependency order
        self._initialize_auth_systems()  # Must come before model systems
        self._initialize_model_systems()
        self._initialize_remote_systems()
        self._initialize_tool_systems()  # Must come before plugin systems
        self._initialize_plugin_systems()
        self._initialize_skill_systems()
        self._initialize_command_systems()
        self._initialize_profile_systems()
        self._initialize_security_systems()
        self._initialize_agent_systems()

    def _initialize_model_systems(self):
        """Initialize model routing and metrics systems."""
        self.model_metrics = ModelMetrics()
        self.router_policy = RouterPolicy(self.model_metrics)
        self.model_router = ModelRouter(
            model_metrics=self.model_metrics,
            router_policy=self.router_policy,
            account_rotator=self.account_rotator
        )

    def _initialize_auth_systems(self):
        """Initialize authentication and account management."""
        self.account_manager = AccountManager()
        self.account_rotator = AccountRotator(self.account_manager)

    def _initialize_remote_systems(self):
        """Initialize remote agent orchestration."""
        self.node_registry = NodeRegistry()

    def _initialize_plugin_systems(self):
        """Initialize plugin marketplace system."""
        self.plugin_registry = PluginRegistry(self.tool_registry)

    def _initialize_tool_systems(self):
        """Initialize tool registry with default tools."""
        self.tool_registry = ToolRegistry()
        self._register_default_tools()

    def _initialize_skill_systems(self):
        """Initialize skill system."""
        self.skill_registry = SkillRegistry()

    def _initialize_command_systems(self):
        """Initialize command system."""
        self.command_registry = CommandRegistry()

    def _initialize_profile_systems(self):
        """Initialize profile system."""
        self.profile_registry = ProfileRegistry()
        self.active_profile = self.profile_registry.get_active_profile()

    def _initialize_security_systems(self):
        """Initialize security and sandboxing systems."""
        if self.enable_security:
                self.sandbox = ProcessSandbox()
                self.syscall_filter = SyscallFilter()
        else:
                self.sandbox = None
                self.syscall_filter = None

    def _initialize_agent_systems(self):
        """Initialize multi-agent execution system."""
        self.supervisor = SupervisorAgent(
                tool_registry=self.tool_registry,
                model_router=self.model_router,
                task_repo=self.task_repo,
                skill_registry=self.skill_registry,
                command_registry=self.command_registry,
                profile=self.active_profile,
                max_workers=self.max_workers,
                # Integrated systems
                model_metrics=self.model_metrics,
                router_policy=self.router_policy,
                account_rotator=self.account_rotator,
                node_registry=self.node_registry,
                plugin_registry=self.plugin_registry,
                sandbox=self.sandbox,
                syscall_filter=self.syscall_filter
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

    def get_system_health(self) -> Dict[str, Any]:
        """Get health status of all integrated systems."""
        health = {
            "overall": "healthy",
            "systems": {},
            "issues": []
        }

        # Model metrics health
        if self.model_metrics:
            health["systems"]["model_metrics"] = {
                "status": "healthy",
                "providers_tracked": len(self.model_metrics._metrics),
                "total_requests": sum(
                    data.get("total_requests", 0)
                    for data in self.model_metrics._metrics.values()
                )
            }
        else:
            health["systems"]["model_metrics"] = {"status": "not_initialized"}
            health["issues"].append("Model metrics not initialized")

        # Auth system health
        if self.account_manager:
            # Get stats per provider
            providers = list(self.account_manager._accounts.keys()) if hasattr(self.account_manager, '_accounts') else []
            total_accounts = sum(len(accounts) for accounts in self.account_manager._accounts.values()) if hasattr(self.account_manager, '_accounts') else 0
            health["systems"]["auth"] = {
                "status": "healthy",
                "providers_configured": len(providers),
                "total_accounts": total_accounts
            }
        else:
            health["systems"]["auth"] = {"status": "not_initialized"}
            health["issues"].append("Auth system not initialized")

        # Remote nodes health
        if self.node_registry:
            nodes = self.node_registry.list_nodes()
            # For now, assume all listed nodes are available
            # In full implementation, would check actual connectivity
            health["systems"]["remote_nodes"] = {
                "status": "healthy" if nodes else "no_nodes",
                "total_nodes": len(nodes),
                "available_nodes": len(nodes)  # Placeholder
            }
        else:
            health["systems"]["remote_nodes"] = {"status": "not_initialized"}

        # Plugin system health
        if self.plugin_registry:
            try:
                tools = self.plugin_registry.get_all_tools()
                skills = self.plugin_registry.get_all_skills()
                health["systems"]["plugins"] = {
                    "status": "healthy",
                    "tools_loaded": len(tools),
                    "skills_loaded": len(skills)
                }
            except Exception as e:
                health["systems"]["plugins"] = {
                    "status": "error",
                    "error": str(e)
                }
                health["issues"].append(f"Plugin system error: {e}")
        else:
            health["systems"]["plugins"] = {"status": "not_initialized"}

        # Security systems health
        health["systems"]["security"] = {
            "sandbox": "enabled" if self.sandbox else "disabled",
            "syscall_filter": "enabled" if self.syscall_filter else "disabled"
        }

        # Supervisor health
        if self.supervisor:
            health["systems"]["supervisor"] = {
                "status": "healthy",
                "workers": len(self.supervisor._workers),
                "profile": self.active_profile.name if self.active_profile else "none"
            }
        else:
            health["systems"]["supervisor"] = {"status": "not_initialized"}
            health["issues"].append("Supervisor not initialized")

        # Determine overall health
        if health["issues"]:
            health["overall"] = "degraded"
        elif any(sys.get("status") in ["error", "not_initialized"] for sys in health["systems"].values()):
            health["overall"] = "warning"

        return health
