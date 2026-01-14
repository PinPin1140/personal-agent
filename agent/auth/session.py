"""Persistent authentication session storage."""
import json
from pathlib import Path
from typing import Dict, Any, Optional


class AuthSessionStore:
    """Persistent storage for auth sessions."""

    def __init__(self, filepath: str = "data/auth_sessions.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        """Load sessions from disk."""
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self._sessions = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._sessions = {}

    def _save(self):
        """Atomically save sessions to disk."""
        temp_path = self.filepath.with_suffix(".tmp")
        try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(self._sessions, f, indent=2)
                temp_path.replace(self.filepath)
        except (IOError, OSError):
                if temp_path.exists():
                        temp_path.unlink()
                raise

    def save_session(self, provider_name: str, auth_data: Dict[str, Any]):
        """Store auth data for a provider."""
        self._sessions[provider_name] = auth_data
        self._save()

    def get_session(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve auth data for a provider."""
        return self._sessions.get(provider_name)

    def delete_session(self, provider_name: str) -> bool:
        """Remove auth data for a provider."""
        if provider_name in self._sessions:
                del self._sessions[provider_name]
                self._save()
                return True
        return False

    def has_session(self, provider_name: str) -> bool:
        """Check if provider has stored session."""
        return provider_name in self._sessions

    def clear_all(self):
        """Clear all stored sessions."""
        self._sessions = {}
        self._save()
