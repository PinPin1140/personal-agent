"""Controlled shell execution tool."""
from typing import Tuple, Optional
from pathlib import Path


def execute_command(
    command: str,
    working_dir: Optional[str] = None,
    timeout: int = 30,
    allow_sudo: bool = False
) -> Tuple[int, str, Optional[str]]:
    """
    Execute shell command with safety controls.

    Args:
        command: Shell command to execute
        working_dir: Directory to execute in (default: current)
        timeout: Maximum execution time in seconds
        allow_sudo: Whether sudo commands are allowed

    Returns:
        (exit_code, stdout, stderr)
    """
    import subprocess
    import shlex

    if command.lower().startswith("sudo") and not allow_sudo:
        return 1, "", "sudo execution not allowed"

    workdir = Path(working_dir) if working_dir else Path.cwd()

    try:
        parts = shlex.split(command)
        result = subprocess.run(
            parts,
            cwd=str(workdir),
            capture_output=True,
            timeout=timeout,
            text=True
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""
        return result.returncode, stdout, stderr

    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return 127, "", "Command not found"
    except PermissionError:
        return 126, "", "Permission denied"
    except Exception as e:
        return -1, "", str(e)
