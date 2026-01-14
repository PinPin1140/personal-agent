"""Base command system for system-level instructions during execution."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Command(ABC):
    """Abstract base class for executable commands during agent execution."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.triggers = []  # Command trigger patterns

    @abstractmethod
    def execute(self, context: Dict[str, Any], args: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Execute the command with given context and arguments.

        Args:
            context: Execution context (agent, task, tools, etc.)
            args: Parsed command arguments

        Returns:
            Dict containing command results and any state changes
        """
        pass

    def can_handle(self, text: str) -> bool:
        """Check if this command can handle the given text."""
        text_lower = text.lower()
        return any(trigger.lower() in text_lower for trigger in self.triggers)

    def parse_args(self, text: str) -> Dict[str, Any]:
        """Parse command arguments from text. Override for custom parsing."""
        return {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize command metadata."""
        return {
                "name": self.name,
                "description": self.description,
                "triggers": self.triggers
        }


class CommandResult:
    """Result of command execution."""

    def __init__(
                self,
                success: bool,
                output: str = "",
                state_changes: Optional[Dict[str, Any]] = None,
                interrupt_execution: bool = False
    ):
        self.success = success
        self.output = output
        self.state_changes = state_changes or {}
        self.interrupt_execution = interrupt_execution

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
                "success": self.success,
                "output": self.output,
                "state_changes": self.state_changes,
                "interrupt_execution": self.interrupt_execution
        }
