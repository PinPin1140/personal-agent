"""Generic OAuth-like authentication stub for CLI-based providers."""
from typing import Dict, Any
from .base import AuthProvider
from .session import AuthSessionStore


class OAuthStubProvider(AuthProvider):
    """Generic OAuth stub provider for CLI-based authentication."""

    def __init__(self, provider_name: str, session_store: AuthSessionStore):
        self.provider_name = provider_name
        self.session_store = session_store
        self._auth_data: Dict[str, Any] = {}
        self._load_session()

    def _load_session(self):
        """Load existing session from storage."""
        if self.session_store.has_session(self.provider_name):
                session_data = self.session_store.get_session(self.provider_name)
                if session_data:
                        self._auth_data = session_data
                else:
                        self._auth_data = {}

    def login(self) -> bool:
        """Stub login flow. Real providers override this."""
        # Real OAuth implementation would:
        # 1. Show auth URL
        # 2. Wait for callback
        # 3. Exchange code for tokens
        # 4. Store tokens securely
        print(f"[OAUTH] Login flow for {self.provider_name}")
        print("This is a stub. Real provider would redirect to OAuth flow.")

        # Store mock credentials
        self._auth_data = {
                "access_token": "stub_token",
                "refresh_token": "stub_refresh",
                "expires_at": "never"
        }
        self.session_store.save_session(self.provider_name, self._auth_data)
        return True

    def logout(self) -> bool:
        """Clear stored authentication."""
        self._auth_data = {}
        self.session_store.delete_session(self.provider_name)
        print(f"[OAUTH] Logged out from {self.provider_name}")
        return True

    def is_authenticated(self) -> bool:
        """Check if valid session exists."""
        return bool(self._auth_data.get("access_token"))

    def get_auth_context(self) -> Dict[str, Any]:
        """Return auth data for provider use."""
        return self._auth_data

    def refresh_if_needed(self) -> bool:
        """Refresh tokens if expired."""
        # Stub: always valid
        return True
