"""Switch model command - change active model provider during execution."""
from typing import Dict, Any
from .base import Command, CommandResult


class SwitchModelCommand(Command):
    """Switch to a different model provider during execution."""

    def __init__(self):
        super().__init__(
                name="switch_model",
                description="Switch to a different model provider"
        )
        self.triggers = ["/switch model", "/switch provider", "/change model"]

    def execute(self, context: Dict[str, Any], args: Dict[str, Any] = {}) -> CommandResult:
        """Execute model switch."""
        try:
                model_router = context.get("model_router")
                if not model_router:
                        return CommandResult(False, "Model router not available")

                new_provider = args.get("provider")
                if not new_provider:
                        return CommandResult(False, "No provider specified for switch")

                # Check if provider exists
                if new_provider not in model_router.list_providers():
                        available = ", ".join(model_router.list_providers())
                        return CommandResult(False, f"Provider '{new_provider}' not found. Available: {available}")

                # Check if provider is available
                metrics = context.get("model_metrics")
                if metrics and not metrics.is_provider_available(new_provider):
                        return CommandResult(False, f"Provider '{new_provider}' is not currently available")

                # Get provider info
                provider = model_router.get_provider(new_provider)

                # Return state change to switch provider
                state_changes = {
                        "switch_provider": new_provider
                }

                output = f"Switched to provider: {new_provider}"
                output += f"\nAuth Type: {provider.auth_type}"
                output += f"\nStreaming: {provider.supports_streaming}"

                return CommandResult(True, output, state_changes)

        except Exception as e:
                return CommandResult(False, f"Model switch failed: {str(e)}")

    def parse_args(self, text: str) -> Dict[str, Any]:
        """Parse provider name from command text."""
        import re

        # Extract provider name: /switch model openai
        match = re.search(r'/switch\s+(?:model|provider)\s+(\w+)', text.lower())
        if match:
                return {"provider": match.group(1)}

        return {}
