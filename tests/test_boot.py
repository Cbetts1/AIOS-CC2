"""Integration smoke-test: boot_subsystems() completes without exceptions."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Isolate StateRegistry singleton
from aios.core.state_registry import StateRegistry
StateRegistry._instance = None


class TestBoot(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Use a temp dir so the boot test doesn't pollute ~/.aios
        import tempfile
        cls._tmpdir = tempfile.mkdtemp()
        # Override the data dir before importing main
        os.environ["AIOS_DATA_DIR"] = cls._tmpdir

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls._tmpdir, ignore_errors=True)
        os.environ.pop("AIOS_DATA_DIR", None)

    def test_boot_subsystems_returns_all_keys(self):
        StateRegistry._instance = None
        import importlib
        import aios.main as main_mod
        importlib.reload(main_mod)  # picks up the updated AIOS_DATA_DIR

        subs = main_mod.boot_subsystems()

        expected_keys = [
            "state", "policy", "security", "identity", "memory",
            "vcpu", "vmem", "vstorage", "vnet", "vsensors",
            "bridge", "mesh", "heartbeat", "aura", "supervisor",
            "proc_writers", "sandbox", "cloud", "cloud_loop", "cc",
        ]
        for key in expected_keys:
            self.assertIn(key, subs, f"Missing subsystem key: {key}")

    def test_all_subsystems_report_healthy(self):
        StateRegistry._instance = None
        import importlib
        import aios.main as main_mod
        importlib.reload(main_mod)

        subs = main_mod.boot_subsystems()
        cc = subs["cc"]
        status = cc.get_status_dict()

        # HeartbeatSystem starts healthy=False until the async mesh thread runs;
        # exclude it from the static boot check.
        SKIP = {"heartbeat"}
        unhealthy = [
            name for name, val in status.items()
            if isinstance(val, dict)
            and val.get("healthy") is False
            and name not in SKIP
        ]
        self.assertEqual(
            unhealthy, [],
            f"Unhealthy subsystems after boot: {unhealthy}",
        )

    def test_security_kernel_authenticated_after_boot(self):
        StateRegistry._instance = None
        import importlib
        import aios.main as main_mod
        importlib.reload(main_mod)

        subs = main_mod.boot_subsystems()
        security = subs["security"]
        self.assertTrue(
            security.is_authenticated(),
            "SecurityKernel should be authenticated after boot_subsystems()",
        )

    def test_cloud_api_attached_to_command_center(self):
        StateRegistry._instance = None
        import importlib
        import aios.main as main_mod
        importlib.reload(main_mod)

        subs = main_mod.boot_subsystems()
        cc = subs["cc"]
        self.assertTrue(
            hasattr(cc, "_cloud_api") and cc._cloud_api is not None,
            "CommandCenter should have _cloud_api set after boot",
        )


if __name__ == "__main__":
    unittest.main()
