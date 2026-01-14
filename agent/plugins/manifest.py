"""Plugin manifest representation."""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class PluginManifest:
    """Plugin manifest definition."""
    name: str
    version: str
    description: str
    author: str
    tools: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    models: List[Dict[str, Any]]
    hooks: List[str]
    permissions: List[str]
    min_core_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        return {
                "name": self.name,
                "version": self.version,
                "description": self.description,
                "author": self.author,
                "tools": self.tools,
                "skills": self.skills,
                "models": self.models,
                "hooks": self.hooks,
                "permissions": self.permissions,
                "min_core_version": self.min_core_version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        """Create manifest from dictionary."""
        return cls(
                name=data.get("name", ""),
                version=data.get("version", "1.0.0"),
                description=data.get("description", ""),
                author=data.get("author", ""),
                tools=data.get("tools", []),
                skills=data.get("skills", []),
                models=data.get("models", []),
                hooks=data.get("hooks", []),
                permissions=data.get("permissions", []),
                min_core_version=data.get("min_core_version", "1.0.0")
        )
