"""AI-OS Identity Lock - Operator identity enforcement."""
import hashlib
import json
import os
from pathlib import Path


class IdentityLockError(Exception):
    """Raised when identity lock operations fail."""


class IdentityLock:
    REQUIRED_OPERATOR = "Chris"

    def __init__(self):
        self._data = {}
        self._loaded = False
        self._override_token = None

    def _find_identity_file(self) -> Path:
        candidates = [
            Path(__file__).parent.parent / "identity" / "identity.lock",
            Path("aios/identity/identity.lock"),
            Path("identity/identity.lock"),
        ]
        for c in candidates:
            if c.exists():
                return c
        raise FileNotFoundError("identity.lock not found in expected locations.")

    def load(self, path: str = None) -> None:
        if path:
            p = Path(path)
        else:
            p = self._find_identity_file()
        with open(p, "r") as fh:
            self._data = json.load(fh)
        self._loaded = True
        operator = self._data.get("operator", "")
        if operator != self.REQUIRED_OPERATOR:
            raise IdentityLockError(
                f"Identity mismatch: expected operator '{self.REQUIRED_OPERATOR}', "
                f"found '{operator}'. System halted."
            )

    def get_operator(self) -> str:
        if not self._loaded:
            self.load()
        return self._data.get("operator", "UNKNOWN")

    def is_operator(self, token: str) -> bool:
        if not self._loaded:
            self.load()
        if not self._data.get("locked", True):
            return False
        expected = self._make_operator_token()
        return token == expected

    def _make_operator_token(self) -> str:
        """Return the operator token.

        The value is taken from the ``AIOS_OPERATOR_TOKEN`` environment
        variable when set, which lets operators change it without editing
        source code.  The built-in default (``"7212"``) is kept for
        backward compatibility but should be overridden in production via
        the environment variable.
        """
        return os.environ.get("AIOS_OPERATOR_TOKEN", "7212")

    def get_operator_token(self) -> str:
        if not self._loaded:
            self.load()
        return self._make_operator_token()

    def lock(self) -> None:
        if not self._loaded:
            self.load()
        self._data["locked"] = True

    def unlock(self, token: str) -> bool:
        if not self._loaded:
            self.load()
        if self.is_operator(token):
            self._data["locked"] = False
            return True
        return False

    def is_locked(self) -> bool:
        if not self._loaded:
            self.load()
        return self._data.get("locked", True)

    def get_level(self) -> str:
        if not self._loaded:
            self.load()
        return self._data.get("level", "operator-only")

    def status(self) -> dict:
        return {
            "component": "IdentityLock",
            "loaded": self._loaded,
            "operator": self._data.get("operator", "UNKNOWN") if self._loaded else "NOT_LOADED",
            "locked": self._data.get("locked", True) if self._loaded else True,
            "level": self._data.get("level", "operator-only") if self._loaded else "unknown",
            "healthy": self._loaded,
        }
