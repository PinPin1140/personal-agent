"""Remote agent node representation."""
from typing import Dict, Any, Optional, List
import json
from pathlib import Path


class RemoteNode:
    """Represents a remote agent running the same core."""

    def __init__(
                self,
                node_id: str,
                host: str,
                port: int,
                capabilities: List[str]
    ):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.capabilities = capabilities
        self._status = "unknown"
        self._last_heartbeat = None
        self._active_tasks: List[int] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization."""
        return {
                "node_id": self.node_id,
                "host": self.host,
                "port": self.port,
                "capabilities": self.capabilities,
                "status": self._status,
                "active_tasks": self._active_tasks,
                "last_heartbeat": self._last_heartbeat
        }

    def update_status(self, status: str):
        """Update node status."""
        self._status = status

    def add_active_task(self, task_id: int):
        """Track active task on this node."""
        if task_id not in self._active_tasks:
                self._active_tasks.append(task_id)

    def remove_active_task(self, task_id: int):
        """Remove task from active tracking."""
        if task_id in self._active_tasks:
                self._active_tasks.remove(task_id)

    def heartbeat(self, timestamp: float):
        """Update heartbeat timestamp."""
        self._last_heartbeat = timestamp

    def is_available(self) -> bool:
        """Check if node is available for new tasks."""
        return self._status == "online" and len(self._active_tasks) < 3

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RemoteNode":
        """Create node from dictionary."""
        return cls(
                node_id=data["node_id"],
                host=data["host"],
                port=data["port"],
                capabilities=data.get("capabilities", []),
                status=data.get("status", "unknown")
        )
