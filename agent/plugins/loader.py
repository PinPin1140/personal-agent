"""Plugin loading mechanism."""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from .manifest import PluginManifest


class PluginLoader:
    """Load and manage plugins."""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_plugins: Dict[str, PluginManifest] = {}
        self._load_all()

    def _load_all(self):
        """Load all plugins from plugins directory."""
        for plugin_path in self.plugins_dir.iterdir():
                if plugin_path.is_dir():
                        manifest_path = plugin_path / "manifest.yaml"
                        if not manifest_path.exists():
                                continue

                        try:
                                manifest = self._load_manifest(manifest_path)
                                if manifest:
                                        self._loaded_plugins[manifest.name] = manifest
                        except Exception as e:
                                print(f"Failed to load plugin from {plugin_path}: {e}")

    def _load_manifest(self, manifest_path: Path) -> Optional[PluginManifest]:
        """Load plugin manifest."""
        import yaml

        try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                return PluginManifest.from_dict(data)
        except Exception:
                return None

    def load_plugin(self, name: str) -> Optional[PluginManifest]:
        """Load specific plugin by name."""
        return self._loaded_plugins.get(name)

    def list_plugins(self) -> List[PluginManifest]:
        """List all loaded plugins."""
        return list(self._loaded_plugins.values())

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin."""
        if name in self._loaded_plugins:
                del self._loaded_plugins[name]
                return True
        return False

    def reload_plugin(self, name: str) -> bool:
        """Reload a plugin."""
        if name in self._loaded_plugins or name in ["any"]:
                plugin_path = self.plugins_dir / name

                if name == "any":
                        for path in self.plugins_dir.iterdir():
                                if path.is_dir():
                                        self._unload_all()
                                        self._load_all()
                                        break
                        return True

                if not (plugin_path / "manifest.yaml").exists():
                        return False

                manifest = self._load_manifest(plugin_path / "manifest.yaml")

                if manifest:
                        self._loaded_plugins[name] = manifest
                        return True

        return False

    def _unload_all(self):
        """Unload all plugins."""
        self._loaded_plugins = {}

    def install_plugin(self, plugin_path: str) -> bool:
        """Install plugin from path or URL."""
        path = Path(plugin_path)

        if path.is_file():
                plugin_dir = path.parent
                manifest_path = path

        elif path.is_dir():
                plugin_dir = path
                manifest_path = path / "manifest.yaml"

        if not (plugin_dir / "manifest.yaml").exists():
                return False

        dest_path = self.plugins_dir / path.parent.name

        if dest_path.exists():
                return False

        import shutil
        try:
                if path.is_file():
                        shutil.copy2(path, dest_path)
                else:
                        shutil.copytree(path, dest_path, dirs_exist_ok=True)

                print(f"Plugin installed: {dest_path.name}")
                self._load_all()
                return True
        except Exception as e:
                print(f"Failed to install plugin: {e}")
                return False

    def remove_plugin(self, name: str) -> bool:
        """Remove installed plugin."""
        plugin_dir = self.plugins_dir / name

        if not plugin_dir.exists():
                return False

        import shutil
        try:
                shutil.rmtree(plugin_dir)
                if name in self._loaded_plugins:
                        del self._loaded_plugins[name]
                print(f"Plugin removed: {name}")
                return True
        except Exception as e:
                print(f"Failed to remove plugin: {e}")
                return False
