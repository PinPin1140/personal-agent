"""Agent profile system for behavioral configuration."""
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AgentProfile:
    """Configuration profile that influences agent behavior."""

    name: str
    description: str

    # Decision-making preferences (0.0 to 1.0)
    creativity_vs_precision: float = 0.5  # 0 = precise, 1 = creative
    speed_vs_accuracy: float = 0.5       # 0 = accurate, 1 = fast
    risk_tolerance: float = 0.5          # 0 = conservative, 1 = aggressive

    # Tool usage preferences
    prefer_tools_over_model: bool = False  # Use tools instead of model calls when possible
    max_tools_per_step: int = 3            # Maximum tools to use in one step
    tool_retry_limit: int = 2              # How many times to retry failed tools

    # Model selection preferences
    preferred_providers: list[str] = None  # List of preferred providers
    avoid_slow_providers: bool = True      # Avoid providers with high latency
    cost_sensitivity: float = 0.5          # 0 = cost-insensitive, 1 = cost-aware

    # Error handling
    aggressive_error_recovery: bool = False  # Try risky recovery methods
    max_retries: int = 3                    # Maximum execution retries
    give_up_after_errors: int = 5           # Stop after this many consecutive errors

    # Skill preferences
    enable_skill_system: bool = True       # Allow skill usage
    prefer_skills_over_tools: bool = False # Use skills instead of raw tools

    # Command preferences
    enable_commands: bool = True           # Allow command execution during tasks
    auto_pause_on_errors: bool = False     # Automatically pause on errors

    # Multi-agent preferences
    collaboration_mode: str = "independent"  # "independent", "cooperative", "competitive"
    task_decomposition: bool = True          # Break tasks into subtasks

    def __post_init__(self):
        """Validate profile parameters."""
        if self.creativity_vs_precision < 0.0 or self.creativity_vs_precision > 1.0:
            raise ValueError("creativity_vs_precision must be between 0.0 and 1.0")
        if self.speed_vs_accuracy < 0.0 or self.speed_vs_accuracy > 1.0:
            raise ValueError("speed_vs_accuracy must be between 0.0 and 1.0")
        if self.risk_tolerance < 0.0 or self.risk_tolerance > 1.0:
            raise ValueError("risk_tolerance must be between 0.0 and 1.0")
        if self.cost_sensitivity < 0.0 or self.cost_sensitivity > 1.0:
            raise ValueError("cost_sensitivity must be between 0.0 and 1.0")

        if self.collaboration_mode not in ["independent", "cooperative", "competitive"]:
            raise ValueError("collaboration_mode must be 'independent', 'cooperative', or 'competitive'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentProfile":
        """Create profile from dictionary."""
        return cls(**data)

    def get_model_selection_score(self, provider_name: str, metrics: Dict[str, Any]) -> float:
        """Calculate score for provider selection based on profile preferences."""
        score = 0.0

        # Check preferred providers
        if self.preferred_providers and provider_name in self.preferred_providers:
            score += 0.5

        # Cost sensitivity
        if self.cost_sensitivity > 0.7 and metrics.get("cost_estimate", 0) > 0.01:
            score -= 0.3  # Penalize expensive providers

        # Speed preference
        if self.speed_vs_accuracy > 0.7:
            latency = metrics.get("avg_latency_ms", 1000)
            if latency > 2000:
                score -= 0.2  # Penalize slow providers

        # Risk tolerance (prefer stable providers)
        if self.risk_tolerance < 0.3:
            error_rate = metrics.get("error_rate", 0)
            if error_rate > 0.1:
                score -= 0.4  # Strongly penalize unreliable providers

        return score

    def should_retry_on_error(self, error_count: int, error_type: str) -> bool:
        """Determine if task should be retried based on profile."""
        if error_count >= self.max_retries:
            return False

        # Aggressive recovery for certain profiles
        if self.aggressive_error_recovery:
            return error_count < self.give_up_after_errors

        # Conservative approach
        return error_count < min(2, self.max_retries)

    def get_tool_usage_preference(self, available_tools: list[str]) -> str:
        """Determine preferred approach for tool usage."""
        if self.prefer_tools_over_model and available_tools:
            return "tools"
        elif self.prefer_skills_over_tools and self.enable_skill_system:
            return "skills"
        else:
            return "model"
