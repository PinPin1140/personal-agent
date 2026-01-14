"""Plugin registry and interface."""
from typing import Dict, Any, List, Optional, Callable
from .loader import PluginLoader
from .manifest import PluginManifest
from ..tools.registry import ToolRegistry


class PluginRegistry:
    """Central registry for all plugins."""

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.loader = PluginLoader()
        self._hooks: Dict[str, List[Callable]] = {}
        self._initialize()

    def _initialize(self):
        """Initialize hooks system."""
        self._hooks = {
                "before_task": [],
                "after_task": [],
                "before_tool": [],
                "after_tool": [],
                "before_model": [],
                "after_model": []
        }

    def register_hook(self, event: str, callback: Callable):
        """Register a callback for specific event."""
        if event not in self._hooks:
                self._hooks[event] = []

        self._hooks[event].append(callback)

    def trigger_hooks(self, event: str, context: Dict[str, Any]):
        """Trigger all hooks for an event."""
        if event in self._hooks:
                for callback in self._hooks[event]:
                        try:
                                callback(context)
                        except Exception as e:
                                print(f"Hook error in {event}: {e}")

    def get_plugin_tools(self, plugin_name: str) -> List[Dict[str, Any]]:
        """Get all tools from a plugin."""
        plugin = self.loader.load_plugin(plugin_name)

        if not plugin:
                return []

        return plugin.tools if plugin.tools else []

    def get_plugin_skills(self, plugin_name: str) -> List[Dict[str, Any]]:
        """Get all skills from a plugin."""
        plugin = self.loader.load_plugin(plugin_name)

        if not plugin:
                return []

        return plugin.skills if plugin.skills else []

    def get_plugin_models(self, plugin_name: str) -> List[Dict[str, Any]]:
        """Get all models from a plugin."""
        plugin = self.loader.load_plugin(plugin_name)

        if not plugin:
                return []

        return plugin.models if plugin.models else []

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools from all loaded plugins."""
        all_tools = []

        for manifest in self.loader.list_plugins():
                all_tools.extend(self.get_plugin_tools(manifest.name))

        return all_tools

    def get_all_skills(self) -> List[Dict[str, Any]]:
        """Get all skills from all loaded plugins."""
        all_skills = []

        for manifest in self.loader.list_plugins():
                all_skills.extend(self.get_plugin_skills(manifest.name))

        return all_skills

    def get_all_models(self) -> List[Dict[str, Any]]:
        """Get all models from all loaded plugins."""
        all_models = []

        for manifest in self.loader.list_plugins():
                all_models.extend(self.get_plugin_models(manifest.name))

        return all_models

    def verify_permissions(self, plugin_name: str, required_permissions: List[str]) -> bool:
        """Verify plugin has required permissions."""
        plugin = self.loader.load_plugin(plugin_name)

        if not plugin:
                return False

        return all(perm in plugin.permissions for perm in required_permissions)

    def check_compatibility(self, plugin_name: str, min_version: str) -> bool:
        """Check if plugin is compatible with core version."""
        plugin = self.loader.load_plugin(plugin_name)

        if not plugin:
                return False

        from packaging import version
        plugin_version = version.parse(plugin.version)
        min_version_req = version.parse(min_version)

        return plugin_version >= min_version_req
