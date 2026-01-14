"""Base skill abstraction for composable, reusable skill patterns."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
from ..task import Task


class Skill(ABC):
    """Abstract base class for skills that can be executed by agents."""

    def __init__(
                self,
                name: str,
                description: str,
                version: str = "1.0.0",
                author: str = "system",
                trigger_patterns: Optional[List[str]] = None,
                required_tools: Optional[List[str]] = None,
                constraints: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.version = version
        self.author = author
        self.trigger_patterns = trigger_patterns or []
        self.required_tools = required_tools or []
        self.constraints = constraints or {}

        # Runtime state
        self._context: Dict[str, Any] = {}
        self._subtasks: List[Task] = []

    @abstractmethod
    def execute(self, task: Task, context: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Execute the skill on a task.

        Args:
            task: The task to execute the skill on
            context: Additional context for execution

        Returns:
            Dict containing execution results
        """
        pass

    def can_handle_task(self, task: Task) -> bool:
        """Check if this skill can handle the given task."""
        task_description = f"{task.goal} {task.description if hasattr(task, 'description') else ''}"

        # Check trigger patterns
        for pattern in self.trigger_patterns:
                if pattern.lower() in task_description.lower():
                        return True

        return False

    def validate_requirements(self, available_tools: Set[str]) -> bool:
        """Validate that required tools are available."""
        missing_tools = set(self.required_tools) - available_tools
        return len(missing_tools) == 0

    def get_required_tools(self) -> List[str]:
        """Get list of tools required by this skill."""
        return self.required_tools.copy()

    def add_subtask(self, goal: str, priority: str = "normal") -> Task:
        """Create and track a subtask."""
        from ..memory import TaskRepository
        from datetime import datetime

        # Create subtask (in-memory only, not persisted)
        subtask = Task(
                id=len(self._subtasks) + 1,
                goal=goal,
                status="pending",
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                priority=priority
        )

        self._subtasks.append(subtask)
        return subtask

    def get_subtasks(self) -> List[Task]:
        """Get all subtasks created by this skill."""
        return self._subtasks.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize skill metadata for storage."""
        return {
                "name": self.name,
                "description": self.description,
                "version": self.version,
                "author": self.author,
                "trigger_patterns": self.trigger_patterns,
                "required_tools": self.required_tools,
                "constraints": self.constraints
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Create skill from serialized data (for built-in skills)."""
        # This would be overridden by concrete skill classes
        return cls(
                name=data.get("name", "unknown"),
                description=data.get("description", ""),
                version=data.get("version", "1.0.0"),
                author=data.get("author", "unknown"),
                trigger_patterns=data.get("trigger_patterns", []),
                required_tools=data.get("required_tools", []),
                constraints=data.get("constraints", {})
        )
