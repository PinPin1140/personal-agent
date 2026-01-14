"""Command system for system-level instructions during execution."""
from .base import Command, CommandResult
from .registry import CommandRegistry

__all__ = [
        "Command",
        "CommandResult",
        "CommandRegistry"
]