"""Executor for running tools and actions."""
import subprocess
import shlex
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class ToolExecutor:
    """Execute tools and shell commands safely."""

    def __init__(self, working_dir: Optional[str] = None, timeout: int = 30):
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.timeout = timeout

    def execute_shell(
        self,
        command: str,
        capture_output: bool = True
    ) -> Tuple[int, str, Optional[str]]:
        """
        Execute shell command safely.

        Returns:
            (exit_code, stdout, stderr)
        """
        parts = None
        try:
            parts = shlex.split(command)
            if not parts:
                return 1, "", "Empty command"

            result = subprocess.run(
                parts,
                cwd=str(self.working_dir),
                capture_output=capture_output,
                timeout=self.timeout,
                text=True
            )

            stdout = result.stdout or ""
            stderr = result.stderr or ""
            return result.returncode, stdout, stderr

        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {self.timeout}s"
        except FileNotFoundError:
            return 127, "", f"Command not found: {parts[0] if parts else 'unknown'}"
        except PermissionError:
            return 126, "", f"Permission denied: {parts[0] if parts else 'unknown'}"
        except Exception as e:
            return -1, "", str(e)

    def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Tuple[int, str, Optional[str]]:
        """
        Execute a tool by name.

        Currently supported: shell (via execute_shell)
        """
        if tool_name == "shell":
            command = args.get("command", "")
            if not command:
                return 1, "", "shell tool requires 'command' argument"

            if args.get("sudo", False):
                return 1, "", "sudo execution not allowed by default"

            return self.execute_shell(command)

        return 1, "", f"Unknown tool: {tool_name}"
