"""Auth status command - check authentication state during execution."""
from typing import Dict, Any
from .base import Command, CommandResult


class AuthStatusCommand(Command):
    """Check authentication status for providers."""

    def __init__(self):
        super().__init__(
                name="auth_status",
                description="Check authentication status for providers"
        )
        self.triggers = ["/auth status", "/auth check", "/check auth"]

    def execute(self, context: Dict[str, Any], args: Dict[str, Any] = {}) -> CommandResult:
        """Execute auth status check."""
        try:
                model_router = context.get("model_router")
                if not model_router:
                        return CommandResult(False, "Model router not available")

                provider_name = args.get("provider", model_router.get_default_provider())
                provider = model_router.get_provider(provider_name)

                if not provider:
                        return CommandResult(False, f"Provider '{provider_name}' not found")

                status_info = {
                        "provider": provider_name,
                        "auth_type": provider.auth_type,
                        "supports_streaming": provider.supports_streaming
                }

                # Check if we have metrics for this provider
                metrics = context.get("model_metrics")
                if metrics:
                        health = metrics.get_provider_health(provider_name)
                        status_info.update({
                                "available": health["available"],
                                "health_score": health["health_score"],
                                "total_requests": health["total_requests"],
                                "in_cooldown": health["in_cooldown"]
                        })

                output_lines = [f"Provider: {status_info['provider']}"]
                output_lines.append(f"Auth Type: {status_info['auth_type']}")
                output_lines.append(f"Streaming: {status_info['supports_streaming']}")

                if "available" in status_info:
                        output_lines.append(f"Available: {status_info['available']}")
                        output_lines.append(f"Health Score: {status_info['health_score']:.2f}")
                        output_lines.append(f"Total Requests: {status_info['total_requests']}")
                        if status_info.get("in_cooldown"):
                                output_lines.append("Status: In cooldown")

                output = "\n".join(output_lines)

                return CommandResult(True, output)

        except Exception as e:
                return CommandResult(False, f"Auth status check failed: {str(e)}")

    def parse_args(self, text: str) -> Dict[str, Any]:
        """Parse provider name from command text."""
        import re

        # Extract provider name: /auth status openai
        match = re.search(r'/auth\s+status\s+(\w+)', text.lower())
        if match:
                return {"provider": match.group(1)}

        return {}
