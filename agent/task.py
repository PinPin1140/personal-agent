"""Task model and state machine for persistent task management."""
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class TaskStatus(str, Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    DONE = "done"
    ERROR = "error"


@dataclass
class Step:
    """Single step in task execution history."""
    step_id: int
    timestamp: str
    action: str
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Task:
    """First-class task entity with persistence support."""
    id: int
    goal: str
    status: TaskStatus
    created_at: str
    updated_at: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Deserialize from dictionary."""
        if isinstance(data.get("status"), str):
            data["status"] = TaskStatus(data["status"])
        return cls(**data)

    def add_step(self, action: str, result: Optional[str] = None, error: Optional[str] = None):
        """Add a step to the task history."""
        step_id = len(self.steps) + 1
        step = Step(
            step_id=step_id,
            timestamp=datetime.utcnow().isoformat(),
            action=action,
            result=result,
            error=error
        )
        self.steps.append(asdict(step))
        self.updated_at = datetime.utcnow().isoformat()

    def update_status(self, new_status: TaskStatus):
        """Transition task to new status."""
        self.status = new_status
        self.updated_at = datetime.utcnow().isoformat()
