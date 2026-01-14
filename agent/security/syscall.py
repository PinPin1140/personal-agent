"""Syscall monitoring and filtering (best-effort, portable)."""
import os
import subprocess
import time
from typing import List, Set, Dict, Any, Optional
import json
from pathlib import Path


class SyscallFilter:
    """Syscall filtering and monitoring system."""

    # Dangerous syscalls to monitor (best-effort list)
    DANGEROUS_SYSCALLS = {
                # Process control
                "fork", "vfork", "clone", "execve", "execve",

                # Network
                "socket", "connect", "bind", "accept", "listen",

                # File system
                "unlink", "rmdir", "rename", "link", "symlink",

                # Privilege escalation
                "setuid", "setgid", "setreuid", "setregid",

                # System
                "mount", "umount2", "pivot_root", "chroot",

                # Process manipulation
                "kill", "ptrace", "killpg"
        }

    def __init__(
                self,
                allowlist: Optional[Set[str]] = None,
                denylist: Optional[Set[str]] = None,
                log_path: str = "data/syscall_log.json"
    ):
        self.allowlist = set(allowlist) if allowlist else set()
        self.denylist = set(denylist) if denylist else set()
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._blocked_count = 0
        self._load_blocked_count()

    def _load_blocked_count(self):
        """Load blocked syscall count from previous runs."""
        if self.log_path.exists():
                try:
                        with open(self.log_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                self._blocked_count = data.get("total_blocked", 0)
                except (json.JSONDecodeError, IOError):
                        self._blocked_count = 0

    def _save_blocked_count(self):
        """Save blocked syscall count."""
        data = {
                "total_blocked": self._blocked_count,
                "last_updated": time.time()
        }

        with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def check_command(self, command: str) -> Dict[str, Any]:
        """Check if command should be allowed based on syscall patterns."""

        # Parse command to detect dangerous operations
        dangerous_patterns = [
                # sudo, doas, pkexec
                ("sudo", "doas", "pkexec"),

                # Package managers auto-installing
                ("apt install", "apt-get install", "pip install", "npm install"),

                # Network operations
                ("wget", "curl", "nc", "ncat", "telnet"),

                # System modifications
                ("iptables", "ufw", "mount", "umount"),

                # Process manipulation
                ("killall", "pkill", "kill -9", "kill -SIGKILL")
        ]

        warnings = []
        blocked_reasons = []

        for pattern in dangerous_patterns:
                if pattern in command.lower():
                        # Check if in denylist
                        if self.denylist and pattern in self.denylist:
                                blocked_reasons.append(f"Explicitly denied: {pattern}")
                                self._blocked_count += 1
                        elif self.allowlist:
                                # Check if allowed
                                allowed = any(a in command.lower() for a in self.allowlist)
                                if not allowed:
                                        blocked_reasons.append(f"Not in allowlist: {pattern}")
                                        self._blocked_count += 1
                        else:
                                blocked_reasons.append(f"Suspicious pattern: {pattern}")
                                self._blocked_count += 1

        if blocked_reasons:
                self._save_blocked_count()
                return {
                        "allowed": False,
                        "blocked": True,
                        "reasons": blocked_reasons
                }

        return {
                "allowed": True,
                "blocked": False,
                "reasons": warnings
        }

    def log_syscall_attempt(self, syscall_name: str, pid: int, allowed: bool):
        """Log syscall attempt."""

        log_entry = {
                "syscall": syscall_name,
                "pid": pid,
                "allowed": allowed,
                "timestamp": time.time()
        }

        with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

    def get_blocked_count(self) -> int:
        """Get total number of blocked syscalls."""
        return self._blocked_count

    def reset_blocked_count(self):
        """Reset blocked syscall counter."""
        self._blocked_count = 0
        self._save_blocked_count()
