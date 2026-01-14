"""Pause command - pause current task execution."""
from typing import Dict, Any
from .base import Command, CommandResult


class PauseCommand(Command):
    """Pause current task execution."""

    def __init__(self):
        super().__init__(
                name="pause",
                description="Pause current task execution"
        )
        self.triggers = ["/pause", "/stop", "/halt"]

    def execute(self, context: Dict[str, Any], args: Dict[str, Any] = {}) -> CommandResult:
        """Execute pause command."""
        try:
                task = context.get("task")
                if not task:
                        return CommandResult(False, "No active task to pause")

                # Set state change to pause execution
                state_changes = {
                        "pause_execution": True
                }

                output = f"Pausing task: {task.goal}"

                return CommandResult(True, output, state_changes, interrupt_execution=True)

        except Exception as e:
                return CommandResult(False, f"Pause command failed: {str(e)}")


class ResumeCommand(Command):
    """Resume paused task execution."""

    def __init__(self):
        super().__init__(
                name="resume",
                description="Resume paused task execution"
        )
        self.triggers = ["/resume", "/continue", "/start"]

    def execute(self, context: Dict[str, Any], args: Dict[str, Any] = {}) -> CommandResult:
        """Execute resume command."""
        try:
                task = context.get("task")
                if not task:
                        return CommandResult(False, "No active task to resume")

                # Set state change to resume execution
                state_changes = {
                        "resume_execution": True
                }

                output = f"Resuming task: {task.goal}"

                return CommandResult(True, output, state_changes)

        except Exception as e:
                return CommandResult(False, f"Resume command failed: {str(e)}")
