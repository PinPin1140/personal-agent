"""Multi-account management for providers."""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class AccountManager:
    """Manage multiple accounts per provider."""

    def __init__(self, accounts_path: str = "data/accounts.json"):
        self.accounts_path = Path(accounts_path)
        self.accounts_path.parent.mkdir(parents=True, exist_ok=True)
        self._accounts: Dict[str, List[Dict[str, Any]]] = {}
        self._load()

    def _load(self):
        """Load accounts from disk."""
        if self.accounts_path.exists():
                try:
                        with open(self.accounts_path, "r", encoding="utf-8") as f:
                                self._accounts = json.load(f)
                except (json.JSONDecodeError, IOError):
                        self._accounts = {}

    def _save(self):
        """Atomically save accounts to disk."""
        temp_path = self.accounts_path.with_suffix(".tmp")
        try:
                with open(temp_path, "w", encoding="utf-8") as f:
                        json.dump(self._accounts, f, indent=2)
                temp_path.replace(self.accounts_path)
        except (IOError, OSError):
                if temp_path.exists():
                        temp_path.unlink()
                raise

    def add_account(
                self,
                provider: str,
                account_id: str,
                credentials: Dict[str, Any],
                priority: int = 1,
                cooldown_until: Optional[float] = None
    ) -> bool:
        """Add a new account."""
        if provider not in self._accounts:
                self._accounts[provider] = []

        account = {
                "account_id": account_id,
                "credentials": credentials,
                "priority": priority,
                "cooldown_until": cooldown_until,
                "created_at": time.time(),
                "last_used": None,
                "use_count": 0
        }

        self._accounts[provider].append(account)
        self._save()
        return True

    def list_accounts(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all accounts or accounts for specific provider."""
        if provider and provider in self._accounts:
                return self._accounts[provider]

        all_accounts = []
        for provider_accounts in self._accounts.values():
                all_accounts.extend(provider_accounts)

        return all_accounts

    def get_next_available(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get next available account for provider."""
        if provider not in self._accounts:
                return None

        current_time = time.time()

        for account in sorted(
                self._accounts[provider],
                key=lambda a: (
                        -a["priority"],
                        a.get("cooldown_until", 0)
                )
        ):
                if account.get("cooldown_until", 0) == 0 or account["cooldown_until"] < current_time:
                        return account

        return None

    def mark_used(self, provider: str, account_id: str):
        """Mark account as used and update cooldown."""
        if provider not in self._accounts:
                return False

        for account in self._accounts[provider]:
                if account["account_id"] == account_id:
                        account["last_used"] = time.time()
                        account["use_count"] += 1

                        account["cooldown_until"] = time.time() + 7200

                        self._save()
                        return True

        return False

    def set_cooldown(self, provider: str, account_id: str, cooldown_seconds: int):
        """Set custom cooldown for account."""
        if provider not in self._accounts:
                return False

        for account in self._accounts[provider]:
                if account["account_id"] == account_id:
                        account["cooldown_until"] = time.time() + cooldown_seconds
                        self._save()
                        return True

        return False

    def remove_account(self, provider: str, account_id: str) -> bool:
        """Remove an account."""
        if provider not in self._accounts:
                return False

        for i, account in enumerate(self._accounts[provider]):
                if account["account_id"] == account_id:
                        self._accounts[provider].pop(i)
                        self._save()
                        return True

        return False

    def get_account_stats(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for accounts."""
        total_accounts = 0
        available_accounts = 0
        in_cooldown_accounts = 0

        providers_to_check = [provider] if provider else list(self._accounts.keys())

        for prov in providers_to_check:
                if prov in self._accounts:
                        for account in self._accounts[prov]:
                                total_accounts += 1

                                current_time = time.time()
                                cooldown = account.get("cooldown_until", 0)

                                if cooldown == 0 or cooldown < current_time:
                                        available_accounts += 1
                                else:
                                        in_cooldown_accounts += 1

        return {
                "total_accounts": total_accounts,
                "available_accounts": available_accounts,
                "in_cooldown": in_cooldown_accounts
        }
