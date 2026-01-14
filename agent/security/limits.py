"""Resource limits configuration."""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ResourceLimits:
    """Resource limit configuration."""

    max_cpu_time: float = 30.0
    max_memory_mb: int = 1024
    max_processes: int = 100
    max_open_files: int = 1024
    timeout_kill_signal: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
                "max_cpu_time": self.max_cpu_time,
                "max_memory_mb": self.max_memory_mb,
                "max_processes": self.max_processes,
                "max_open_files": self.max_open_files,
                "timeout_kill_signal": self.timeout_kill_signal
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceLimits":
        """Create from dictionary."""
        return cls(
                max_cpu_time=data.get("max_cpu_time", 30.0),
                max_memory_mb=data.get("max_memory_mb", 1024),
                max_processes=data.get("max_processes", 100),
                max_open_files=data.get("max_open_files", 1024),
                timeout_kill_signal=data.get("timeout_kill_signal", True)
        )
