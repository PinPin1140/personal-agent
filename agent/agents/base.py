"""Multi-agent system for autonomous task execution."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..task import Task
from ..tools.registry import ToolRegistry


class BaseAgent(ABC):
    """Abstract base class for agents."""

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry

    @abstractmethod
    def execute(self, task: Task) -> Dict[str, Any]:
        """Execute task and return result."""
        pass

    @abstractmethod
    def get_status(self) -> str:
        """Get current agent status."""
        pass
