"""Inject context command - add additional context during execution."""
from typing import Dict, Any
from .base import Command, CommandResult


class InjectContextCommand(Command):
    """Inject additional context information during task execution."""

    def __init__(self):
        super().__init__(
                name="inject_context",
                description="Add additional context information to current task"
        )
        self.triggers = ["/inject context", "/add context", "/context"]

    def execute(self, context: Dict[str, Any], args: Dict[str, Any] = {}) -> CommandResult:
        """Execute context injection."""
        try:
                task = context.get("task")
                if not task:
                        return CommandResult(False, "No active task to inject context into")

                context_text = args.get("context", "").strip()
                if not context_text:
                        return CommandResult(False, "No context text provided")

                # Add context to task memory
                if not hasattr(task, 'memory') or task.memory is None:
                        task.memory = {}

                if 'injected_context' not in task.memory:
                        task.memory['injected_context'] = []

                task.memory['injected_context'].append({
                        'timestamp': context.get('timestamp', 'unknown'),
                        'context': context_text
                })

                # Limit to last 10 context injections
                if len(task.memory['injected_context']) > 10:
                        task.memory['injected_context'] = task.memory['injected_context'][-10:]

                output = f"Context injected: {context_text[:100]}{'...' if len(context_text) > 100 else ''}"

                return CommandResult(True, output)

        except Exception as e:
                return CommandResult(False, f"Context injection failed: {str(e)}")

    def parse_args(self, text: str) -> Dict[str, Any]:
        """Parse context text from command."""
        import re

        # Extract context: /inject context This is additional information
        match = re.search(r'/inject\s+context\s+(.+)', text, re.IGNORECASE | re.DOTALL)
        if match:
                return {"context": match.group(1).strip()}

        return {}
