"""Tool execution registry for function calling."""
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod
import shlex
import subprocess
from pathlib import Path


class Tool(ABC):
    """Abstract base class for executable tools."""

    def __init__(self):
        self.name = self.__class__.__name__
        self.description = ""
        self.parameters: Dict[str, Dict[str, Any]] = {}

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool with arguments."""
        pass

    def to_schema(self) -> Dict[str, Any]:
        """Return tool schema for model consumption."""
        return {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
        }


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool instance."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    def to_schemas(self) -> list[Dict[str, Any]]:
        """Export all tool schemas."""
        return [tool.to_schema() for tool in self._tools.values()]


class ShellTool(Tool):
    """Shell command execution tool."""

    def __init__(self, timeout: int = 30, allow_sudo: bool = False):
        super().__init__()
        self.description = "Execute shell command safely"
        self.timeout = timeout
        self.allow_sudo = allow_sudo
        self.parameters = {
                "command": {
                        "type": "string",
                        "description": "Shell command to execute",
                        "required": True
                }
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        command = kwargs.get("command", "")

        if not command:
                return {"error": "No command provided", "output": ""}

        if command.lower().startswith("sudo") and not self.allow_sudo:
                return {"error": "sudo execution not allowed", "output": ""}

        try:
                parts = shlex.split(command)
                result = subprocess.run(
                        parts,
                        capture_output=True,
                        timeout=self.timeout,
                        text=True
                )

                return {
                        "output": result.stdout or "",
                        "error": result.stderr or ""
                }

        except subprocess.TimeoutExpired:
                return {"error": f"Command timed out after {self.timeout}s", "output": ""}
        except FileNotFoundError:
                return {"error": "Command not found", "output": ""}
        except Exception as e:
                return {"error": str(e), "output": ""}


class FileReadTool(Tool):
    """Read file contents tool."""

    def __init__(self):
        super().__init__()
        self.description = "Read file contents"
        self.parameters = {
                "filepath": {
                        "type": "string",
                        "description": "Path to file to read",
                        "required": True
                }
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        filepath = kwargs.get("filepath", "")

        try:
                path = Path(filepath)
                if not path.exists():
                        return {"error": f"File not found: {filepath}", "output": ""}

                with open(path, "r", encoding="utf-8") as f:
                        content = f.read()

                return {"output": content, "error": ""}

        except Exception as e:
                return {"error": str(e), "output": ""}


class FileWriteTool(Tool):
    """Write content to file tool."""

    def __init__(self):
        super().__init__()
        self.description = "Write content to file"
        self.parameters = {
                "filepath": {
                        "type": "string",
                        "description": "Path to file to write",
                        "required": True
                },
                "content": {
                        "type": "string",
                        "description": "Content to write",
                        "required": True
                }
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        filepath = kwargs.get("filepath", "")
        content = kwargs.get("content", "")

        try:
                path = Path(filepath)
                path.parent.mkdir(parents=True, exist_ok=True)

                with open(path, "w", encoding="utf-8") as f:
                        f.write(content)

                return {"output": f"Wrote {len(content)} bytes to {filepath}", "error": ""}

        except Exception as e:
                return {"error": str(e), "output": ""}


class ListDirTool(Tool):
    """List directory contents tool."""

    def __init__(self):
        super().__init__()
        self.description = "List directory contents"
        self.parameters = {
                "path": {
                        "type": "string",
                        "description": "Path to directory (default: current)",
                        "required": False,
                        "default": "."
                }
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        path = kwargs.get("path", ".")

        try:
                dir_path = Path(path)
                if not dir_path.exists():
                        return {"error": f"Directory not found: {path}", "output": ""}

                items = list(dir_path.iterdir())
                names = sorted([item.name for item in items])

                return {
                        "output": "\n".join(names),
                        "error": ""
                }

        except Exception as e:
                return {"error": str(e), "output": ""}