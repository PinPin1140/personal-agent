"""Built-in agent profiles for different behavioral styles."""

from ..profiles.base import AgentProfile


# Conservative, precise profile
CONSERVATIVE_PROFILE = AgentProfile(
    name="conservative",
    description="Precise and careful execution with strong error checking",
    creativity_vs_precision=0.1,      # Very precise
    speed_vs_accuracy=0.2,            # Prioritize accuracy
    risk_tolerance=0.1,               # Very conservative
    prefer_tools_over_model=False,    # Use models when appropriate
    max_tools_per_step=2,             # Limited tool usage
    tool_retry_limit=3,               # Retry failed tools
    aggressive_error_recovery=False,  # Safe error recovery
    max_retries=2,                    # Limited retries
    give_up_after_errors=3,           # Give up after few errors
    enable_skill_system=True,         # Use skills
    prefer_skills_over_tools=False,   # Prefer models over skills
    enable_commands=True,             # Allow commands
    auto_pause_on_errors=True,        # Pause on errors
    collaboration_mode="independent", # Work independently
    task_decomposition=False          # Don't break tasks down
)

# Creative, fast profile
CREATIVE_PROFILE = AgentProfile(
    name="creative",
    description="Creative and fast execution with risk-taking approach",
    creativity_vs_precision=0.9,      # Very creative
    speed_vs_accuracy=0.9,            # Prioritize speed
    risk_tolerance=0.9,               # Very aggressive
    prefer_tools_over_model=True,     # Use tools extensively
    max_tools_per_step=5,             # Many tools per step
    tool_retry_limit=1,               # Quick retries
    aggressive_error_recovery=True,   # Risky recovery
    max_retries=5,                    # Many retries
    give_up_after_errors=10,          # Persistent
    enable_skill_system=True,         # Use skills
    prefer_skills_over_tools=True,    # Prefer skills
    enable_commands=True,             # Allow commands
    auto_pause_on_errors=False,       # Don't pause on errors
    collaboration_mode="cooperative", # Work cooperatively
    task_decomposition=True           # Break tasks down
)

# Balanced profile
BALANCED_PROFILE = AgentProfile(
    name="balanced",
    description="Balanced approach with reasonable trade-offs",
    creativity_vs_precision=0.5,      # Balanced creativity/precision
    speed_vs_accuracy=0.5,            # Balanced speed/accuracy
    risk_tolerance=0.5,               # Moderate risk
    prefer_tools_over_model=False,    # Use models primarily
    max_tools_per_step=3,             # Moderate tool usage
    tool_retry_limit=2,               # Standard retries
    aggressive_error_recovery=False,  # Safe recovery
    max_retries=3,                    # Standard retries
    give_up_after_errors=5,           # Reasonable persistence
    enable_skill_system=True,         # Use skills
    prefer_skills_over_tools=False,   # Balance skills/tools
    enable_commands=True,             # Allow commands
    auto_pause_on_errors=False,       # Don't auto-pause
    collaboration_mode="independent", # Work independently
    task_decomposition=True           # Break tasks down
)

# Minimal profile (for testing/safe environments)
MINIMAL_PROFILE = AgentProfile(
    name="minimal",
    description="Minimal, safe execution with basic features",
    creativity_vs_precision=0.3,      # Slightly precise
    speed_vs_accuracy=0.3,            # Slightly accurate
    risk_tolerance=0.2,               # Conservative
    prefer_tools_over_model=False,    # Use models
    max_tools_per_step=1,             # One tool at a time
    tool_retry_limit=1,               # Minimal retries
    aggressive_error_recovery=False,  # Safe recovery
    max_retries=1,                    # Minimal retries
    give_up_after_errors=2,           # Give up quickly
    enable_skill_system=False,        # No skills
    prefer_skills_over_tools=False,   # No skills
    enable_commands=False,            # No commands
    auto_pause_on_errors=True,        # Pause on errors
    collaboration_mode="independent", # Independent
    task_decomposition=False          # No decomposition
)

# Autonomous profile (for production use)
AUTONOMOUS_PROFILE = AgentProfile(
    name="autonomous",
    description="Highly autonomous with aggressive error recovery",
    creativity_vs_precision=0.7,      # Creative but not reckless
    speed_vs_accuracy=0.6,            # Speed-leaning
    risk_tolerance=0.7,               # Moderate risk-taking
    prefer_tools_over_model=True,     # Tool-heavy
    max_tools_per_step=4,             # Multiple tools
    tool_retry_limit=3,               # Good retry limit
    aggressive_error_recovery=True,   # Aggressive recovery
    max_retries=4,                    # Persistent retries
    give_up_after_errors=8,           # Very persistent
    enable_skill_system=True,         # Use skills
    prefer_skills_over_tools=True,    # Prefer skills
    enable_commands=True,             # Allow commands
    auto_pause_on_errors=False,       # Don't pause
    collaboration_mode="cooperative", # Cooperative
    task_decomposition=True           # Decompose tasks
)


# Dictionary of built-in profiles
BUILT_IN_PROFILES = {
    "conservative": CONSERVATIVE_PROFILE,
    "creative": CREATIVE_PROFILE,
    "balanced": BALANCED_PROFILE,
    "minimal": MINIMAL_PROFILE,
    "autonomous": AUTONOMOUS_PROFILE
}


def get_profile(name: str) -> AgentProfile:
    """Get a built-in profile by name."""
    if name in BUILT_IN_PROFILES:
        return BUILT_IN_PROFILES[name].__class__(
            **BUILT_IN_PROFILES[name].to_dict()
        )
    else:
        # Return balanced profile as default
        return get_profile("balanced")


def list_profiles() -> list[str]:
    """List available built-in profile names."""
    return list(BUILT_IN_PROFILES.keys())
