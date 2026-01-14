"""Abstract authentication provider for login-based providers."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class AuthProvider(ABC):
    """Abstract base class for authentication providers."""

    @abstractmethod
    def login(self) -> bool:
        """Perform login flow, return True on success."""
        pass

    @abstractmethod
    def logout(self) -> bool:
        """Clear authentication state, return True on success."""
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        pass

    @abstractmethod
    def get_auth_context(self) -> Dict[str, Any]:
        """Get authentication context for provider usage."""
        pass

    def refresh_if_needed(self) -> bool:
        """Refresh tokens if needed. Default: no-op."""
        return True
