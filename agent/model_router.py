"""Model provider router for selecting and using providers."""
import os
from typing import Dict, Any, Optional
from .models import ModelProvider
from .providers.dummy import DummyProvider
from .providers.openai_provider import OpenAIProvider


class ModelRouter:
    """Router for model provider selection and delegation."""

    def __init__(self):
        self._providers: Dict[str, ModelProvider] = {}
        self._default_provider: Optional[str] = None

        # Auto-register built-in providers
        self.register("dummy", DummyProvider())
        self.register("openai", OpenAIProvider())

        # Set default: OpenAI if API key present, else dummy
        if os.getenv("OPENAI_API_KEY"):
            self._default_provider = "openai"
        else:
            self._default_provider = "dummy"

    def register(self, name: str, provider: ModelProvider):
        """Register a provider instance."""
        self._providers[name] = provider

    def get_provider(self, name: Optional[str] = None) -> ModelProvider:
        """Get provider by name, or default if none specified."""
        provider_name = name or self._default_provider
        if not provider_name or provider_name not in self._providers:
            return self._providers["dummy"]  # Fallback
        return self._providers[provider_name]

    def generate(
        self,
        prompt: str,
        context: Dict[str, Any] = {},
        provider_name: Optional[str] = None
    ) -> str:
        """Generate response using selected provider."""
        provider = self.get_provider(provider_name)
        return provider.generate(prompt, context)

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())

    def get_default_provider(self) -> Optional[str]:
        """Get the name of the default provider."""
        return self._default_provider