"""Plugin system for extensibility."""
from .loader import PluginLoader
from .registry import PluginRegistry
from .manifest import PluginManifest

__all__ = [
        "PluginLoader",
        "PluginRegistry",
        "PluginManifest"
]