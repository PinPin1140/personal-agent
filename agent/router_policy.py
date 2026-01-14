"""Router policy system for intelligent provider selection."""
from typing import Dict, Any, Optional
from .model_metrics import ModelMetrics
from .models import ModelProvider


class RouterPolicy:
    """Policy-driven router for model provider selection."""

    def __init__(self, metrics: ModelMetrics):
        self.metrics = metrics

    def select_provider(
                self,
                task_goal: str,
                preferred_providers: list[str],
                allow_streaming: bool = True
    ) -> Optional[str]:
        """Select best provider based on policy."""

        available_providers = [
                provider for provider in preferred_providers
                if self.metrics.is_provider_available(provider)
        ]

        if not available_providers:
                return None

        # Score each provider
        scored_providers = []
        for provider_name in available_providers:
                score = self._score_provider(provider_name, task_goal, allow_streaming)
                scored_providers.append((score, provider_name))

        # Sort by score (descending)
        scored_providers.sort(key=lambda x: x[0], reverse=True)

        # Return highest-scoring provider
        if scored_providers:
                return scored_providers[0][1]

        return None

    def _score_provider(
                self,
                provider_name: str,
                task_goal: str,
                allow_streaming: bool
    ) -> float:
        """Calculate provider score (0-1)."""

        health = self.metrics.get_provider_health(provider_name)

        if not health["available"] or health["in_cooldown"]:
                return 0.0

        score = 0.0

        # Health score (weight: 0.4)
        score += health["health_score"] * 0.4

        # Latency score (weight: 0.3, lower is better)
        if health["avg_latency_ms"] < 2000:
                score += 0.3
        elif health["avg_latency_ms"] < 5000:
                score += 0.2
        elif health["avg_latency_ms"] < 10000:
                score += 0.1

        # Success rate (weight: 0.2)
        if health.get("success_rate", 0) > 0.9:
                score += 0.2
        elif health.get("success_rate", 0) > 0.7:
                score += 0.1

        # Streaming preference (weight: 0.1)
        if allow_streaming:
                provider = self._get_provider(provider_name)
                if provider and provider.supports_streaming:
                        score += 0.1

        # Rate limit penalty
        if health.get("rate_limited", False):
                score -= 0.3

        return min(score, 1.0)

    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Get detailed information about a provider."""
        health = self.metrics.get_provider_health(provider_name)

        return {
                "name": provider_name,
                "available": health["available"],
                "health_score": health["health_score"],
                "total_requests": health["total_requests"],
                "success_rate": health.get("success_rate", 0),
                "avg_latency_ms": health["avg_latency_ms"],
                "rate_limited": health.get("rate_limited", False),
                "in_cooldown": health["in_cooldown"]
        }

    def _get_provider(self, provider_name: str) -> Optional[ModelProvider]:
        """Get provider instance by name (stub)."""
        from .model_router import ModelRouter
        router = ModelRouter()
        return router.get_provider(provider_name)
