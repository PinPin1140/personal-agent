"""Dummy provider for testing and development without API keys."""
from typing import Dict, Any
from ..models import ModelProvider


class DummyProvider(ModelProvider):
    """Dummy provider for testing and development without API keys."""

    def generate(
        self,
        prompt: str,
        context: Dict[str, Any] = {}
    ) -> str:
        """Generate a deterministic dummy response."""
        return f"[DUMMY] Processed: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"

    @property
    def supports_streaming(self) -> bool:
        return False

    @property
    def auth_type(self) -> str:
        return "APIKEY"