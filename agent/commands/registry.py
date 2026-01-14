"""Command registry for managing available commands during execution."""
from typing import Dict, Any, List, Optional
from .base import Command, CommandResult
from .auth_status import AuthStatusCommand
from .switch_model import SwitchModelCommand
from .pause_resume import PauseCommand, ResumeCommand
from .inspect_task import InspectTaskCommand
from .inject_context import InjectContextCommand


class CommandRegistry:
    """Registry for managing available commands during execution."""

    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._load_builtin_commands()

    def _load_builtin_commands(self):
        """Load built-in commands."""
        self.register(AuthStatusCommand())
        self.register(SwitchModelCommand())
        self.register(PauseCommand())
        self.register(ResumeCommand())
        self.register(InspectTaskCommand())
        self.register(InjectContextCommand())

    def register(self, command: Command):
        """Register a command instance."""
        self._commands[command.name] = command

    def unregister(self, command_name: str) -> bool:
        """Unregister a command by name."""
        if command_name in self._commands:
                del self._commands[command_name]
                return True
        return False

    def get_command(self, name: str) -> Optional[Command]:
        """Get command by name."""
        return self._commands.get(name)

    def list_commands(self) -> List[Command]:
        """List all registered commands."""
        return list(self._commands.values())

    def find_command_for_text(self, text: str) -> Optional[Command]:
        """Find the first command that can handle the given text."""
        for command in self._commands.values():
                if command.can_handle(text):
                        return command
        return None

    def execute_command(
                self,
                text: str,
                context: Dict[str, Any]
    ) -> Optional[CommandResult]:
        """Execute the appropriate command for the given text."""
        command = self.find_command_for_text(text)
        if not command:
                return None

        # Parse arguments from text
        args = command.parse_args(text)

        # Execute command
        try:
                result = command.execute(context, args)
                return result
        except Exception as e:
                # Return error result
                return CommandResult(False, f"Command execution failed: {str(e)}")

    def get_command_help(self) -> str:
        """Get help text for all available commands."""
        lines = ["Available Commands During Execution:"]
        for command in self.list_commands():
                lines.append(f"  {command.name}: {command.description}")
                for trigger in command.triggers:
                        lines.append(f"    Trigger: {trigger}")
                lines.append("")

        return "\n".join(lines)
