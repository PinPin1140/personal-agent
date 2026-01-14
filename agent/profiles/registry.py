"""Profile registry for managing agent behavior configurations."""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from .base import AgentProfile
from .builtin import BUILT_IN_PROFILES, get_profile


class ProfileRegistry:
    """Registry for managing agent profiles."""

    def __init__(self, profiles_path: str = "data/profiles.json"):
        self.profiles_path = Path(profiles_path)
        self.profiles_path.parent.mkdir(parents=True, exist_ok=True)
        self._custom_profiles: Dict[str, AgentProfile] = {}
        self._active_profile: Optional[str] = None
        self._load_custom_profiles()
        self._set_default_profile()

    def _load_custom_profiles(self):
        """Load custom profiles from disk."""
        if self.profiles_path.exists():
                try:
                        with open(self.profiles_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                for name, profile_data in data.get("custom_profiles", {}).items():
                                        profile = AgentProfile.from_dict(profile_data)
                                        self._custom_profiles[name] = profile
                except (json.JSONDecodeError, IOError):
                        self._custom_profiles = {}

    def _save_custom_profiles(self):
        """Save custom profiles to disk."""
        data = {
                "custom_profiles": {
                        name: profile.to_dict()
                        for name, profile in self._custom_profiles.items()
                }
        }

        with open(self.profiles_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def _set_default_profile(self):
        """Set default active profile."""
        if not self._active_profile:
                self._active_profile = "balanced"

    def add_custom_profile(self, profile: AgentProfile) -> bool:
        """Add a custom profile."""
        if profile.name in BUILT_IN_PROFILES:
                return False  # Cannot override built-in profiles

        self._custom_profiles[profile.name] = profile
        self._save_custom_profiles()
        return True

    def remove_custom_profile(self, name: str) -> bool:
        """Remove a custom profile."""
        if name in self._custom_profiles:
                del self._custom_profiles[name]
                self._save_custom_profiles()
                return True
        return False

    def get_profile(self, name: str) -> Optional[AgentProfile]:
        """Get a profile by name."""
        # Check custom profiles first
        if name in self._custom_profiles:
                return self._custom_profiles[name]

        # Check built-in profiles
        if name in BUILT_IN_PROFILES:
                return get_profile(name)

        return None

    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        builtin_names = list(BUILT_IN_PROFILES.keys())
        custom_names = list(self._custom_profiles.keys())
        return builtin_names + custom_names

    def list_builtin_profiles(self) -> List[str]:
        """List built-in profile names."""
        return list(BUILT_IN_PROFILES.keys())

    def list_custom_profiles(self) -> List[str]:
        """List custom profile names."""
        return list(self._custom_profiles.keys())

    def set_active_profile(self, name: str) -> bool:
        """Set the active profile."""
        if self.get_profile(name):
                self._active_profile = name
                return True
        return False

    def get_active_profile(self) -> Optional[AgentProfile]:
        """Get the currently active profile."""
        if self._active_profile:
                return self.get_profile(self._active_profile)
        return None

    def get_active_profile_name(self) -> Optional[str]:
        """Get the name of the active profile."""
        return self._active_profile

    def create_profile_from_template(
                self,
                name: str,
                template_name: str,
                modifications: Dict[str, Any]
    ) -> Optional[AgentProfile]:
        """Create a new profile based on a template with modifications."""
        template = self.get_profile(template_name)
        if not template:
                return None

        # Create modified profile
        profile_data = template.to_dict()
        profile_data.update(modifications)
        profile_data["name"] = name
        profile_data["description"] = f"Modified {template_name}: {modifications}"

        try:
                new_profile = AgentProfile(**profile_data)
                self.add_custom_profile(new_profile)
                return new_profile
        except ValueError:
                return None

    def get_profile_stats(self) -> Dict[str, Any]:
        """Get statistics about available profiles."""
        return {
                "total_profiles": len(self.list_profiles()),
                "builtin_profiles": len(self.list_builtin_profiles()),
                "custom_profiles": len(self.list_custom_profiles()),
                "active_profile": self._active_profile
        }
