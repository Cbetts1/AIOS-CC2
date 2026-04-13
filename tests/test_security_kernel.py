"""Tests for SecurityKernel — authenticate, token verify, log, file logging."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aios.core.security_kernel import SecurityKernel


# Path to the actual identity.lock used in this repo
IDENTITY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "aios", "identity", "identity.lock"
)


class TestSecurityKernel(unittest.TestCase):

    def setUp(self):
        self.sk = SecurityKernel()

    def test_authenticate_with_real_identity(self):
        if not os.path.exists(IDENTITY_PATH):
            self.skipTest("identity.lock not found")
        token = self.sk.authenticate(IDENTITY_PATH)
        self.assertIsInstance(token, str)
        self.assertEqual(len(token), 64)  # SHA-256 hex digest

    def test_is_authenticated_after_authenticate(self):
        if not os.path.exists(IDENTITY_PATH):
            self.skipTest("identity.lock not found")
        self.assertFalse(self.sk.is_authenticated())
        self.sk.authenticate(IDENTITY_PATH)
        self.assertTrue(self.sk.is_authenticated())

    def test_verify_valid_token(self):
        if not os.path.exists(IDENTITY_PATH):
            self.skipTest("identity.lock not found")
        token = self.sk.authenticate(IDENTITY_PATH)
        self.assertTrue(self.sk.verify_identity(token))

    def test_verify_invalid_token_returns_false(self):
        self.assertFalse(self.sk.verify_identity("deadbeef" * 8))

    def test_revoke_token(self):
        if not os.path.exists(IDENTITY_PATH):
            self.skipTest("identity.lock not found")
        token = self.sk.authenticate(IDENTITY_PATH)
        self.sk.revoke_token(token)
        self.assertFalse(self.sk.verify_identity(token))

    def test_log_security_event_appends(self):
        self.sk.log_security_event({"type": "TEST_EVENT"})
        log = self.sk.get_security_log(limit=5)
        types = [e.get("type") for e in log]
        self.assertIn("TEST_EVENT", types)

    def test_file_logging(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
            path = f.name
        try:
            self.sk.set_log_file(path)
            self.sk.log_security_event({"type": "FILE_LOG_TEST"})
            with open(path) as fh:
                lines = [l.strip() for l in fh if l.strip()]
            self.assertGreater(len(lines), 0)
            record = json.loads(lines[-1])
            self.assertEqual(record["type"], "FILE_LOG_TEST")
        finally:
            os.unlink(path)

    def test_authenticate_fallback_resolves_real_identity(self):
        """SecurityKernel auto-resolves to identity.lock when the path is absent."""
        # The resolver falls back to the repo's identity.lock, so authenticate
        # with any nonexistent path should still succeed (not raise) when the
        # identity.lock exists at its standard location.
        if not os.path.exists(IDENTITY_PATH):
            self.skipTest("identity.lock not found")
        # Should succeed via fallback resolution (no exception)
        token = self.sk.authenticate("/tmp/no_such_aios_identity_file.lock")
        self.assertIsInstance(token, str)

    def test_status(self):
        st = self.sk.status()
        self.assertTrue(st["healthy"])
        self.assertIn("authenticated", st)


if __name__ == "__main__":
    unittest.main()
