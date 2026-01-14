"""Model provider abstraction for pluggable LLM backends."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Iterator
from enum import Enum


class AuthType(str, Enum):
    """Authentication types supported by providers."""
    APIKEY = "apikey"
    OAUTH = "oauth"
    HYBRID = "hybrid"


class ModelProvider(ABC):
    """Abstract base class for model providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate response from prompt."""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether provider supports streaming responses."""
        pass

    @property
    @abstractmethod
    def auth_type(self) -> AuthType:
        """Authentication type required."""
        pass


class DummyProvider(ModelProvider):
    """Dummy provider for testing and development without API keys."""

    def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a deterministic dummy response."""
        return f"[DUMMY] Processed: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"

    @property
    def supports_streaming(self) -> bool:
        return False

    @property
    def auth_type(self) -> AuthType:
        return AuthType.APIKEY


class ProviderRegistry:
    """Registry for model provider plugins."""

    def __init__(self):
        self._providers: Dict[str, ModelProvider] = {}

    def register(self, name: str, provider: ModelProvider):
        """Register a provider instance."""
        self._providers[name] = provider

    def get(self, name: str) -> Optional[ModelProvider]:
        """Get registered provider by name."""
        return self._providers.get(name)

    def list_available(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())
