"""Inspect task command - show detailed task information during execution."""
from typing import Dict, Any
from .base import Command, CommandResult


class InspectTaskCommand(Command):
    """Inspect current task details during execution."""

    def __init__(self):
        super().__init__(
                name="inspect_task",
                description="Show detailed information about current task"
        )
        self.triggers = ["/inspect task", "/inspect", "/task info", "/status"]

    def execute(self, context: Dict[str, Any], args: Dict[str, Any] = {}) -> CommandResult:
        """Execute task inspection."""
        try:
                task = context.get("task")
                if not task:
                        return CommandResult(False, "No active task to inspect")

                # Gather task information
                info_lines = []
                info_lines.append(f"Task ID: {task.id}")
                info_lines.append(f"Goal: {task.goal}")
                info_lines.append(f"Status: {task.status.value}")
                info_lines.append(f"Created: {task.created_at}")
                info_lines.append(f"Updated: {task.updated_at}")
                info_lines.append(f"Steps Completed: {len(task.steps)}")

                if hasattr(task, 'priority') and task.priority:
                        info_lines.append(f"Priority: {task.priority}")

                if task.steps:
                        info_lines.append("\nRecent Steps:")
                        # Show last 3 steps
                        for step in task.steps[-3:]:
                                timestamp = step.get('timestamp', 'unknown')[:19]  # Truncate ISO format
                                action = step.get('action', 'unknown')[:50]
                                info_lines.append(f"  [{timestamp}] {action}")
                                if step.get('result'):
                                        result_preview = step['result'][:100].replace('\n', ' ')
                                        info_lines.append(f"    Result: {result_preview}...")
                                if step.get('error'):
                                        info_lines.append(f"    Error: {step['error']}")

                # Add agent context if available
                agent = context.get("agent")
                if agent:
                        info_lines.append(f"\nAgent Status: {agent.get_status()}")

                # Add skill context if available
                skill_registry = context.get("skill_registry")
                if skill_registry:
                        available_skills = len(skill_registry.list_skills())
                        info_lines.append(f"Available Skills: {available_skills}")

                output = "\n".join(info_lines)

                return CommandResult(True, output)

        except Exception as e:
                return CommandResult(False, f"Task inspection failed: {str(e)}")
