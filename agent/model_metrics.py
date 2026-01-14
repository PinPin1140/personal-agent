"""Model metrics tracking for cost, latency, and health."""
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ModelMetrics:
    """Track model usage metrics."""

    def __init__(self, metrics_path: str = "data/model_metrics.json"):
        self.metrics_path = Path(metrics_path)
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        """Load metrics from disk."""
        if self.metrics_path.exists():
                try:
                        with open(self.metrics_path, "r", encoding="utf-8") as f:
                                self._metrics = json.load(f)
                except (json.JSONDecodeError, IOError):
                        self._metrics = {}

    def _save(self):
        """Atomically save metrics to disk."""
        temp_path = self.metrics_path.with_suffix(".tmp")
        try:
                with open(temp_path, "w", encoding="utf-8") as f:
                        json.dump(self._metrics, f, indent=2)
                temp_path.replace(self.metrics_path)
        except (IOError, OSError):
                if temp_path.exists():
                        temp_path.unlink()
                raise

    def record_generation(
                self,
                provider: str,
                prompt_tokens: int,
                completion_tokens: int,
                latency_ms: float,
                success: bool = True
    ):
        """Record a model generation event."""
        if provider not in self._metrics:
                self._metrics[provider] = {
                        "total_requests": 0,
                        "successful_requests": 0,
                        "failed_requests": 0,
                        "total_prompt_tokens": 0,
                        "total_completion_tokens": 0,
                        "total_latency_ms": 0.0,
                        "avg_latency_ms": 0.0,
                        "last_request_at": None,
                        "rate_limit_hit": False,
                        "cooldown_until": None
                }

        metrics = self._metrics[provider]

        # Update counters
        metrics["total_requests"] += 1
        if success:
                metrics["successful_requests"] += 1
        else:
                metrics["failed_requests"] += 1

        metrics["total_prompt_tokens"] += prompt_tokens
        metrics["total_completion_tokens"] += completion_tokens

        # Calculate rolling average latency
        total_latency = metrics["total_latency_ms"] + latency_ms
        metrics["total_latency_ms"] = total_latency
        metrics["avg_latency_ms"] = total_latency / metrics["total_requests"]

        metrics["last_request_at"] = time.time()

        self._metrics[provider] = metrics
        self._save()

    def check_rate_limit(self, provider: str, response_headers: Dict[str, str]) -> bool:
        """Check if response indicates rate limiting."""
        rate_limit_indicators = [
                "429",
                "rate_limit",
                "rate limit",
                "quota",
                "limit"
        ]

        for key, value in response_headers.items():
                if any(indicator in value.lower() for indicator in rate_limit_indicators):
                        self._metrics[provider]["rate_limit_hit"] = True

                        # Set cooldown: 2 minutes
                        self._metrics[provider]["cooldown_until"] = time.time() + 120
                        self._save()
                        return True

        return False

    def get_provider_health(self, provider: str) -> Dict[str, Any]:
        """Get health score for provider."""
        if provider not in self._metrics:
                return {
                        "provider": provider,
                        "available": True,
                        "health_score": 1.0,
                        "total_requests": 0
                }

        metrics = self._metrics[provider]

        # Calculate health score (0-1)
        success_rate = metrics["successful_requests"] / max(metrics["total_requests"], 1)

        # Penalize for failures
        if metrics["rate_limit_hit"]:
                score = max(0.1, success_rate) * 0.5
        elif metrics["failed_requests"] / metrics["total_requests"] > 0.2:
                score = max(0.1, success_rate * 0.7)
        else:
                score = success_rate

        # Check if in cooldown
        if metrics.get("cooldown_until", 0) and time.time() < metrics["cooldown_until"]:
                score *= 0.5

        # Check latency penalty
        if metrics["avg_latency_ms"] > 5000:
                score *= 0.8

        return {
                "provider": provider,
                "available": score > 0.5,
                "health_score": score,
                "total_requests": metrics["total_requests"],
                "success_rate": success_rate,
                "avg_latency_ms": metrics["avg_latency_ms"],
                "rate_limited": metrics["rate_limit_hit"],
                "in_cooldown": time.time() < metrics.get("cooldown_until", 0) if metrics.get("cooldown_until") else False
        }

    def is_provider_available(self, provider: str) -> bool:
        """Check if provider is available for use."""
        health = self.get_provider_health(provider)
        return health["available"] and not health["in_cooldown"]
