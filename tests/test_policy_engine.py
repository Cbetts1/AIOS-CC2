"""Tests for PolicyEngine — permission levels, enforcement, audit log, file logging."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aios.core.policy_engine import PolicyEngine, PolicyViolation


class TestPolicyEngine(unittest.TestCase):

    def setUp(self):
        self.policy = PolicyEngine()

    def _make_identity(self, role):
        return {"name": f"test_{role}", "role": role}

    def test_public_action_allowed_for_everyone(self):
        for role in ("public", "internal", "restricted", "operator"):
            ident = self._make_identity(role)
            self.assertTrue(self.policy.check_permission("read_status", 0, ident))

    def test_operator_only_blocked_for_lower_roles(self):
        for role in ("public", "internal", "restricted"):
            ident = self._make_identity(role)
            self.assertFalse(self.policy.check_permission("shutdown", 0, ident))

    def test_operator_only_allowed_for_operator(self):
        ident = self._make_identity("operator")
        self.assertTrue(self.policy.check_permission("shutdown", 3, ident))

    def test_enforce_raises_for_blocked_action(self):
        ident = self._make_identity("public")
        with self.assertRaises(PolicyViolation):
            self.policy.enforce("shutdown", ident)

    def test_enforce_succeeds_for_operator(self):
        ident = self._make_identity("operator")
        # Should not raise
        self.policy.enforce("shutdown", ident)

    def test_audit_log_grows(self):
        ident = self._make_identity("operator")
        self.policy.enforce("read_status", ident)
        log = self.policy.get_audit_log()
        self.assertGreater(len(log), 0)

    def test_audit_log_records_action(self):
        ident = self._make_identity("internal")
        self.policy.enforce("write_state", ident)
        log = self.policy.get_audit_log(1)
        self.assertEqual(log[-1]["action"], "write_state")

    def test_custom_policy_override(self):
        self.policy.set_policy("custom_action", PolicyEngine.PUBLIC)
        ident = self._make_identity("public")
        # Should not raise
        self.policy.enforce("custom_action", ident)

    def test_file_logging(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
            path = f.name
        try:
            self.policy.set_log_file(path)
            ident = self._make_identity("operator")
            self.policy.enforce("read_status", ident)
            with open(path) as fh:
                lines = [l for l in fh.readlines() if l.strip()]
            self.assertGreater(len(lines), 0)
            record = json.loads(lines[-1])
            self.assertIn("action", record)
        finally:
            os.unlink(path)

    def test_status(self):
        st = self.policy.status()
        self.assertTrue(st["healthy"])
        self.assertIn("defined_actions", st)


if __name__ == "__main__":
    unittest.main()
