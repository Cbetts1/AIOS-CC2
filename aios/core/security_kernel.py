"""AI-OS Security Kernel - Authentication and security event logging."""
import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from pathlib import Path


class SecurityKernel:
    _SECRET_SALT = b"AIOS-CC2-SECURITY-KERNEL-SALT-2026"

    def __init__(self):
        self._identity_data = {}
        self._active_tokens = {}
        self._security_log = []
        self._authenticated = False
        self._identity_path = None

    def _resolve_identity_path(self, identity_path: str) -> Path:
        p = Path(identity_path)
        if p.exists():
            return p
        # Try relative to this file's parent tree
        base = Path(__file__).parent.parent / "identity" / "identity.lock"
        if base.exists():
            return base
        return p

    def authenticate(self, identity_path: str) -> str:
        resolved = self._resolve_identity_path(identity_path)
        self._identity_path = str(resolved)
        if not resolved.exists():
            self.log_security_event({
                "type": "AUTH_FAILURE",
                "reason": f"identity file not found: {resolved}",
            })
            raise FileNotFoundError(f"Identity file not found: {resolved}")

        with open(resolved, "r") as fh:
            self._identity_data = json.load(fh)

        if not self._identity_data.get("locked", False):
            self.log_security_event({"type": "AUTH_FAILURE", "reason": "identity not locked"})
            raise ValueError("Identity file is not locked - system in unsafe state.")

        token = self._generate_token(self._identity_data)
        self._active_tokens[token] = {
            "created_at": time.time(),
            "operator": self._identity_data.get("operator"),
            "level": self._identity_data.get("level"),
        }
        self._authenticated = True
        self.log_security_event({
            "type": "AUTH_SUCCESS",
            "operator": self._identity_data.get("operator"),
        })
        return token

    def _generate_token(self, identity_data: dict) -> str:
        payload = json.dumps(identity_data, sort_keys=True).encode()
        timestamp = str(int(time.time())).encode()
        raw = payload + b":" + timestamp
        token = hmac.new(self._SECRET_SALT, raw, hashlib.sha256).hexdigest()
        return token

    def verify_identity(self, token: str) -> bool:
        entry = self._active_tokens.get(token)
        if entry is None:
            self.log_security_event({"type": "TOKEN_INVALID", "token_prefix": token[:8]})
            return False
        # Tokens expire after 24 hours
        if time.time() - entry["created_at"] > 86400:
            del self._active_tokens[token]
            self.log_security_event({"type": "TOKEN_EXPIRED", "token_prefix": token[:8]})
            return False
        return True

    def log_security_event(self, event: dict) -> None:
        event["timestamp"] = datetime.utcnow().isoformat() + "Z"
        self._security_log.append(event)
        if len(self._security_log) > 2000:
            self._security_log = self._security_log[-1000:]

    def get_security_log(self, limit: int = 100) -> list:
        return list(self._security_log[-limit:])

    def is_authenticated(self) -> bool:
        return self._authenticated

    def revoke_token(self, token: str) -> None:
        if token in self._active_tokens:
            del self._active_tokens[token]
            self.log_security_event({"type": "TOKEN_REVOKED", "token_prefix": token[:8]})

    def status(self) -> dict:
        return {
            "component": "SecurityKernel",
            "authenticated": self._authenticated,
            "active_tokens": len(self._active_tokens),
            "security_log_entries": len(self._security_log),
            "identity_path": self._identity_path,
            "healthy": True,
        }
