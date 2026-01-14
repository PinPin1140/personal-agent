"""Model provider router for selecting and using providers."""
import os
from typing import Dict, Any, Optional, Iterator
from .models import ModelProvider
from .providers.dummy import DummyProvider
from .providers.openai_provider import OpenAIProvider


class ModelRouter:
    """Router for model provider selection and delegation."""

    def __init__(
        self,
        model_metrics=None,
        router_policy=None,
        account_rotator=None
    ):
        self._providers: Dict[str, ModelProvider] = {}
        self._default_provider: Optional[str] = None

        # Integrated systems
        self.model_metrics = model_metrics
        self.router_policy = router_policy
        self.account_rotator = account_rotator

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
        """Generate response using selected provider with intelligent routing."""
        import time

        # Use intelligent routing if available
        if self.router_policy and not provider_name:
            # Get available providers
            available = self.list_providers()
            # Select best provider based on task goal
            task_goal = context.get("task_goal", prompt[:100])
            provider_name = self.router_policy.select_provider(
                task_goal=task_goal,
                preferred_providers=available
            )
            if not provider_name:
                provider_name = self._default_provider

        provider = self.get_provider(provider_name)

        # Track account selection if rotator available
        account_id = None
        if self.account_rotator and hasattr(provider, 'requires_auth') and provider.requires_auth:
            account_id = self.account_rotator.select_account(provider_name)

        # Track metrics
        start_time = time.time()
        try:
            response = provider.generate(prompt, context)
            latency = int((time.time() - start_time) * 1000)

            # Record success metrics
            if self.model_metrics:
                self.model_metrics.record_request(
                    provider_name=provider_name,
                    account_id=account_id,
                    success=True,
                    latency_ms=latency,
                    tokens_in=len(prompt.split()),
                    tokens_out=len(response.split())
                )

            return response

        except Exception as e:
            latency = int((time.time() - start_time) * 1000)

            # Record failure metrics
            if self.model_metrics:
                self.model_metrics.record_request(
                    provider_name=provider_name,
                    account_id=account_id,
                    success=False,
                    latency_ms=latency,
                    error=str(e)
                )

            raise

    def generate_stream(
        self,
        prompt: str,
        context: Dict[str, Any] = {},
        provider_name: Optional[str] = None
    ) -> Iterator[str]:
        """Generate streaming response if supported, else fallback."""
        provider = self.get_provider(provider_name)

        if provider.supports_streaming:
                return provider.generate_stream(prompt, context)

        # Fallback: yield full response as single chunk
        response = provider.generate(prompt, context)
        yield response

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())

    def get_default_provider(self) -> Optional[str]:
        """Get name of default provider."""
        return self._default_provider