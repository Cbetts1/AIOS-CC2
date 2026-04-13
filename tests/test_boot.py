"""AI-OS CC2 — Boot and command smoke tests."""
import os
import sys

import pytest

# Make sure the repo root is on the path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_root, os.path.join(_root, "aios")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def subsystems():
    from aios.main import boot_subsystems
    subs = boot_subsystems()
    # Force one heartbeat so it registers as healthy
    hb = subs.get("heartbeat")
    if hb:
        hb.beat_sync()
    return subs


@pytest.fixture(scope="module")
def cc(subsystems):
    return subsystems["cc"]


# ── Boot tests ─────────────────────────────────────────────────────────────

class TestBoot:
    def test_boot_returns_all_subsystems(self, subsystems):
        expected = [
            "state", "policy", "security", "identity", "memory",
            "vcpu", "vmem", "vstorage", "vnet", "vsensors",
            "bridge", "mesh", "heartbeat", "aura", "supervisor",
            "proc_writers", "sandbox", "cloud", "cloud_loop", "cc",
        ]
        for key in expected:
            assert key in subsystems, f"Missing subsystem: {key}"

    def test_command_center_running(self, cc):
        assert cc._running is True

    def test_identity_operator(self, subsystems):
        identity = subsystems["identity"]
        assert identity.get_operator() == "Chris"
        assert identity.is_locked() is True

    def test_state_registry_usable(self, subsystems):
        state = subsystems["state"]
        state.set("test_key", "test_value", namespace="test")
        assert state.get("test_key", namespace="test") == "test_value"

    def test_memory_regions_allocated(self, subsystems):
        memory = subsystems["memory"]
        st = memory.status()
        assert st["regions"] >= 4
        assert "kernel" in st["region_names"]
        assert "heap" in st["region_names"]


# ── Health checks ──────────────────────────────────────────────────────────

class TestHealth:
    COMPONENTS = [
        "state", "policy", "security", "identity", "memory",
        "vcpu", "vmem", "vstorage", "vnet", "vsensors",
        "bridge", "mesh", "aura", "cloud",
    ]

    def test_all_components_healthy(self, cc):
        status = cc.get_status_dict()
        for name in self.COMPONENTS:
            comp = status.get(name, {})
            assert isinstance(comp, dict), f"{name}: expected dict status"
            assert comp.get("healthy") is True, \
                f"{name}: healthy=False — {comp}"

    def test_heartbeat_healthy(self, subsystems):
        hb = subsystems["heartbeat"]
        st = hb.status()
        assert st["beat_count"] > 0, "Heartbeat has not beaten"
        assert st["healthy"] is True

    def test_status_dict_has_required_keys(self, cc):
        status = cc.get_status_dict()
        for key in ("version", "operator", "uptime_seconds", "running", "timestamp"):
            assert key in status, f"Missing key in status_dict: {key}"
        assert status["operator"] == "Chris"
        assert status["running"] is True
        assert status["version"] == "2.0.0-CC2"


# ── Command routing smoke tests ────────────────────────────────────────────

class TestCommands:
    @pytest.mark.parametrize("cmd,expected_substr", [
        ("1.1",   "version"),
        ("1.2",   "Layer"),
        ("1.3",   "Subsystem"),
        ("1.4",   "Resource"),
        ("1.5",   "Event"),
        ("2",     "Layer Control"),
        ("4.1",   "VirtualCPU"),
        ("4.2",   "VirtualMemory"),
        ("4.3",   "VirtualStorage"),
        ("4.4",   "cpu_temp"),
        ("5.1",   "lo0"),
        ("5.2",   "Node Mesh"),
        ("5.3",   "HeartbeatSystem"),
        ("6.1",   "IdentityLock"),
        ("7.1",   "Running"),
        ("10.1",  "AuraEngine"),
        ("11.1",  "Diagnostic"),
        ("11.2",  "✓"),
        ("13.1",  "LegalCortex"),
        ("14.1",  "system_overview"),
        ("15.5",  "entries"),
    ])
    def test_command_output(self, cc, cmd, expected_substr):
        result = cc.handle_command(cmd)
        assert expected_substr.lower() in result.lower(), \
            f"CMD {cmd}: expected {expected_substr!r} in output:\n{result}"

    def test_unknown_command_returns_error(self, cc):
        result = cc.handle_command("99")
        assert "Unknown" in result or "unknown" in result.lower()

    def test_empty_command_returns_error(self, cc):
        result = cc.handle_command("")
        assert "Unknown" in result or "unknown" in result.lower()


# ── Engine tests ───────────────────────────────────────────────────────────

class TestEngines:
    def test_aura_engine_status(self, subsystems):
        aura = subsystems["aura"]
        st = aura.status()
        assert st["status"] == "ONLINE"
        assert "BuilderEngine" in st["sub_engines"]
        assert "RepairEngine" in st["sub_engines"]
        assert "LegalCortex" in st["sub_engines"]

    def test_aura_tick(self, subsystems):
        aura = subsystems["aura"]
        before = aura._tick_count
        aura.tick()
        assert aura._tick_count == before + 1

    def test_legal_cortex_compliance(self, subsystems):
        aura = subsystems["aura"]
        legal = aura.legal
        st = legal.status()
        assert st["healthy"] is True
        # BLOCKED_ACTIONS is a class-level constant — always populated
        assert "blocked_action_count" in st
        assert len(legal.BLOCKED_ACTIONS) > 0

    def test_policy_engine_allows_read(self, subsystems):
        policy = subsystems["policy"]
        # check_permission requires action, level (int), identity (dict)
        # "read_status" is defined as PUBLIC in ACTION_POLICY
        identity_data = {"operator": "Chris", "locked": True, "level": "public"}
        result = policy.check_permission("read_status", 0, identity_data)
        assert result is True


# ── Trace file tests ───────────────────────────────────────────────────────

class TestTraceFile:
    def test_trace_file_created(self, cc, tmp_path):
        trace_path = str(tmp_path / "test_trace.log")
        cc.set_trace_file(trace_path)
        cc.handle_command("1.1")
        assert os.path.exists(trace_path), "Trace file was not created"
        with open(trace_path) as fh:
            content = fh.read()
        assert "TRACE LOG" in content
        assert "CMD" in content
        # Reset trace file to avoid interfering with other tests
        cc._trace_file = None

    def test_trace_file_appends(self, cc, tmp_path):
        trace_path = str(tmp_path / "append_trace.log")
        cc.set_trace_file(trace_path)
        cc.handle_command("1.1")
        cc.handle_command("5.3")
        with open(trace_path) as fh:
            lines = [ln for ln in fh.readlines() if ln.strip()]
        assert len(lines) >= 3  # header + 2 CMD lines
        cc._trace_file = None


# ── Virtual hardware tests ─────────────────────────────────────────────────

class TestVirtualHardware:
    def test_vcpu_tick(self, subsystems):
        vcpu = subsystems["vcpu"]
        before = vcpu._tick_count
        vcpu.tick()
        assert vcpu._tick_count == before + 1

    def test_vsensors_readings(self, subsystems):
        vsensors = subsystems["vsensors"]
        vsensors.tick()
        readings = vsensors.read_all()
        assert "cpu_temp" in readings
        assert "cpu_load" in readings
        assert isinstance(readings["cpu_temp"], (int, float))

    def test_vmemory_read_write(self, subsystems):
        vmem = subsystems["vmem"]
        vmem.write(0x100, b"\xDE\xAD\xBE\xEF")
        data = vmem.read(0x100, 4)
        assert data == b"\xDE\xAD\xBE\xEF"

    def test_vstorage_write_read(self, subsystems):
        vstorage = subsystems["vstorage"]
        vstorage.write("test_health_file.txt", b"AIOS-CC2-TEST")
        data = vstorage.read("test_health_file.txt")
        assert data == b"AIOS-CC2-TEST"

    def test_vnetwork_interfaces(self, subsystems):
        vnet = subsystems["vnet"]
        ifaces = vnet.list_interfaces()
        names = [i["name"] for i in ifaces]
        assert "lo0" in names
        assert "eth0" in names
