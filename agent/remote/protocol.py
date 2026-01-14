"""Simple communication protocol for remote agent nodes."""
from typing import Dict, Any, Optional, List
from enum import Enum


class MessageType(str, Enum):
    """Message types for node communication."""
    HEARTBEAT = "heartbeat"
    TASK_ASSIGN = "task_assign"
    TASK_UPDATE = "task_update"
    TASK_COMPLETE = "task_complete"
    TASK_ERROR = "task_error"
    NODE_STATUS = "node_status"
    SHUTDOWN = "shutdown"


class Message:
    """Base message class for protocol."""

    def __init__(
                self,
                msg_type: str,
                payload: Optional[Dict[str, Any]] = None,
                node_id: Optional[str] = None
                task_id: Optional[int] = None,
                error: Optional[str] = None
    ):
        self.msg_type = msg_type
        self.payload = payload or {}
        self.node_id = node_id
        self.task_id = task_id
        self.error = error
        self.timestamp = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
                "msg_type": self.msg_type,
                "payload": self.payload,
                "node_id": self.node_id,
                "task_id": self.task_id,
                "error": self.error,
                "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        msg = cls(
                msg_type=data["msg_type"],
                payload=data.get("payload", {}),
                node_id=data.get("node_id"),
                task_id=data.get("task_id"),
                error=data.get("error")
        )
        return msg


class ProtocolHandler:
    """Handle encoding and decoding of protocol messages."""

    @staticmethod
    def encode(message: Message) -> str:
        """Encode message to JSON string."""
        import json
        return json.dumps(message.to_dict())

    @staticmethod
    def decode(data: str) -> Message:
        """Decode JSON string to message."""
        import json
        try:
                msg_data = json.loads(data)
                return Message.from_dict(msg_data)
        except (json.JSONDecodeError, KeyError):
                error_msg = Message(msg_type="error", error="Failed to decode message")
                return error_msg

    @staticmethod
    def create_heartbeat(node_id: str) -> Message:
        """Create heartbeat message."""
        return Message(
                msg_type=MessageType.HEARTBEAT,
                node_id=node_id,
                payload={"status": "alive"}
        )

    @staticmethod
    def create_task_assign(
                node_id: str,
                task_id: int,
                task_goal: str,
                priority: str = "normal"
    ) -> Message:
        """Create task assignment message."""
        return Message(
                msg_type=MessageType.TASK_ASSIGN,
                node_id=node_id,
                task_id=task_id,
                payload={
                        "goal": task_goal,
                        "priority": priority
                }
        )

    @staticmethod
    def create_task_update(
                node_id: str,
                task_id: int,
                step: str,
                output: str
    ) -> Message:
        """Create task update message."""
        return Message(
                msg_type=MessageType.TASK_UPDATE,
                node_id=node_id,
                task_id=task_id,
                payload={
                        "step": step,
                        "output": output
                }
        )

    @staticmethod
    def create_task_complete(
                node_id: str,
                task_id: int,
                result: str = "success"
    ) -> Message:
        """Create task completion message."""
        return Message(
                msg_type=MessageType.TASK_COMPLETE,
                node_id=node_id,
                task_id=task_id,
                payload={
                        "result": result
                }
        )

    @staticmethod
    def create_task_error(
                node_id: str,
                task_id: int,
                error_msg: str
    ) -> Message:
        """Create task error message."""
        return Message(
                msg_type=MessageType.TASK_ERROR,
                node_id=node_id,
                task_id=task_id,
                error=error_msg
        )

    @staticmethod
    def create_shutdown(node_id: str) -> Message:
        """Create shutdown message."""
        return Message(
                msg_type=MessageType.SHUTDOWN,
                node_id=node_id
        )
