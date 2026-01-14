"""Model provider abstraction for pluggable LLM backends."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class ModelProvider(ABC):
    """Abstract base class for model providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        context: Dict[str, Any] = {}
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
    def auth_type(self) -> str:
        """Authentication type required: APIKEY, LOGIN, HYBRID."""
        pass
