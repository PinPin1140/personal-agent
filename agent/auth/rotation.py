"""Automatic account rotation based on cooldowns."""
from typing import Optional
from .accounts import AccountManager


class AccountRotator:
    """Manage automatic account rotation."""

    def __init__(self, account_manager: AccountManager):
        self.account_manager = account_manager

    def select_account(self, provider: str) -> Optional[str]:
        """Select best available account for provider."""
        account = self.account_manager.get_next_available(provider)

        if not account:
                return None

        account_id = account["account_id"]

        # Mark as used (sets cooldown)
        self.account_manager.mark_used(provider, account_id)

        return account_id

    def rotate_if_needed(self, provider: str, cooldown_threshold: int = 3600) -> Optional[str]:
        """Rotate to next account if current is in cooldown."""

        # Get stats
        stats = self.account_manager.get_account_stats(provider)

        if stats["available_accounts"] == 0:
                return None

        # If too many in cooldown, wait
        if stats["in_cooldown"] >= stats["total_accounts"] - 1:
                return None

        # Find account with lowest cooldown
        best_account = None
        lowest_cooldown = float('inf')

        if provider in self.account_manager._accounts:
                for account in self.account_manager._accounts[provider]:
                        cooldown = account.get("cooldown_until", 0)
                        current_time = account.get("cooldown_until", 0) if account.get("cooldown_until") else float('inf')

                        if current_time <= cooldown:
                                if cooldown < lowest_cooldown:
                                        lowest_cooldown = cooldown
                                        best_account = account

        if best_account:
                account_id = best_account["account_id"]

                # Check if we need to rotate (current account in cooldown)
                # Get current active (most recently used)
                current_active = None
                for account in self.account_manager._accounts.get(provider, []):
                        if account.get("cooldown_until", 0) == 0:
                                if not current_active or account["last_used"] > current_active.get("last_used", 0):
                                        current_active = account
                                        break

                if current_active and current_active["account_id"] != account_id:
                        # Rotation needed
                        self.account_manager.mark_used(provider, account_id)
                        return account_id

        return None

    def get_rotation_status(self, provider: str) -> dict:
        """Get rotation status for provider."""
        stats = self.account_manager.get_account_stats(provider)

        return {
                "provider": provider,
                "total_accounts": stats["total_accounts"],
                "available": stats["available_accounts"],
                "in_cooldown": stats["in_cooldown"],
                "needs_rotation": stats["in_cooldown"] > 0 and stats["available_accounts"] > 0
        }
