"""Tests for CommandCenter — handle_command routing, logging, shutdown."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Reset StateRegistry singleton before import
from aios.core.state_registry import StateRegistry
StateRegistry._instance = None

from aios.command.command_center import CommandCenter


class TestCommandCenter(unittest.TestCase):

    def setUp(self):
        StateRegistry._instance = None
        self.cc = CommandCenter()

    def test_handle_empty_command(self):
        result = self.cc.handle_command("")
        self.assertIn("menu", result.lower())

    def test_handle_top_level_menu(self):
        result = self.cc.handle_command("1")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_handle_system_full_report(self):
        result = self.cc.handle_command("1.1")
        # Should contain version info even without all subsystems attached
        self.assertIsInstance(result, str)

    def test_handle_invalid_top(self):
        result = self.cc.handle_command("99")
        self.assertIsInstance(result, str)

    def test_handle_invalid_sub(self):
        result = self.cc.handle_command("1.99")
        self.assertIsInstance(result, str)

    def test_quit_command(self):
        result = self.cc.handle_command("q")
        self.assertIsInstance(result, str)

    def test_get_banner(self):
        banner = self.cc.get_banner()
        self.assertIn("AI-OS", banner)

    def test_console_log(self):
        self.cc.handle_command("1")
        log = self.cc.get_console_log(limit=10)
        self.assertIsInstance(log, list)

    def test_file_logging(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
            path = f.name
        try:
            self.cc.set_log_file(path)
            self.cc.handle_command("1.1")
            with open(path) as fh:
                content = fh.read()
            self.assertGreater(len(content), 0)
        finally:
            os.unlink(path)

    def test_shutdown_requires_valid_token(self):
        # Without identity attached, shutdown always succeeds (no token to check)
        # This test verifies that when identity IS attached, a bad token is rejected
        from aios.core.identity_lock import IdentityLock
        identity = IdentityLock()
        identity.load()
        self.cc._identity = identity
        result = self.cc.shutdown("bad_token_12345")
        self.assertIn("REFUSED", result.upper())

    def test_status_dict(self):
        st = self.cc.get_status_dict()
        self.assertIsInstance(st, dict)
        self.assertIn("version", st)

    def test_duplicate_cloud_block_removed(self):
        """Verify the duplicate elif top=='7' block is gone."""
        src_path = os.path.join(
            os.path.dirname(__file__), "..", "aios", "command", "command_center.py"
        )
        with open(src_path) as fh:
            src = fh.read()
        # Count occurrences of the dead-code marker from the old second block
        self.assertNotIn("SIMULATED — no real cloud connected", src)


if __name__ == "__main__":
    unittest.main()
