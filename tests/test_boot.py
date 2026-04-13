"""Tests that boot every subsystem and verify healthy status."""
import pytest


def _assert_healthy(component_name, obj):
    st = obj.status()
    assert isinstance(st, dict), f"{component_name}.status() must return a dict"
    assert st.get("healthy") is True, (
        f"{component_name}.status()['healthy'] is not True: {st}"
    )


# ── Individual subsystem boot tests ─────────────────────────────────────────

def test_state_registry():
    from aios.core.state_registry import StateRegistry
    sr = StateRegistry()
    _assert_healthy("StateRegistry", sr)


def test_policy_engine():
    from aios.core.policy_engine import PolicyEngine
    _assert_healthy("PolicyEngine", PolicyEngine())


def test_security_kernel():
    from aios.core.security_kernel import SecurityKernel
    _assert_healthy("SecurityKernel", SecurityKernel())


def test_identity_lock():
    from aios.core.identity_lock import IdentityLock
    il = IdentityLock()
    il.load()
    _assert_healthy("IdentityLock", il)


def test_memory_map():
    from aios.core.memory_map import MemoryMapController
    mm = MemoryMapController()
    mm.allocate("test", 1024)
    _assert_healthy("MemoryMapController", mm)


def test_process_supervisor():
    from aios.core.process_supervisor import ProcessSupervisor
    _assert_healthy("ProcessSupervisor", ProcessSupervisor())


def test_virtual_cpu():
    from aios.virtual.vcpu import VirtualCPU
    cpu = VirtualCPU()
    cpu.tick()
    _assert_healthy("VirtualCPU", cpu)


def test_virtual_memory():
    from aios.virtual.vmemory import VirtualMemory
    _assert_healthy("VirtualMemory", VirtualMemory())


def test_virtual_storage():
    from aios.virtual.vstorage import VirtualStorage
    _assert_healthy("VirtualStorage", VirtualStorage())


def test_virtual_network():
    from aios.virtual.vnetwork import VirtualNetwork
    vn = VirtualNetwork()
    vn.create_interface("eth0")
    _assert_healthy("VirtualNetwork", vn)


def test_virtual_sensors():
    from aios.virtual.vsensors import VirtualSensors
    vs = VirtualSensors()
    vs.tick()
    _assert_healthy("VirtualSensors", vs)


def test_host_bridge():
    from aios.bridge.host_bridge import HostBridge
    hb = HostBridge()
    hb.boot()
    _assert_healthy("HostBridge", hb)


def test_node_mesh():
    from aios.mesh.node_mesh import NodeMesh
    nm = NodeMesh()
    nm.add_node("test")
    _assert_healthy("NodeMesh", nm)


def test_heartbeat():
    from aios.mesh.heartbeat import HeartbeatSystem
    hb = HeartbeatSystem()
    hb.beat_sync()
    st = hb.status()
    assert isinstance(st, dict)
    assert st.get("beat_count", 0) >= 1


def test_aura_engine():
    from aios.engine.aura import AuraEngine
    from aios.core.state_registry import StateRegistry
    ae = AuraEngine(state_registry=StateRegistry())
    ae.boot()
    ae.tick()
    _assert_healthy("AuraEngine", ae)


def test_sandbox():
    from aios.sandbox.sandbox import Sandbox
    _assert_healthy("Sandbox", Sandbox())


def test_proc_writers():
    from aios.procwriters.proc_writers import ProcWriters
    from aios.virtual.vstorage import VirtualStorage
    pw = ProcWriters(vstorage=VirtualStorage())
    pw.tick()
    _assert_healthy("ProcWriters", pw)


def test_log_writer(tmp_path):
    from aios.core.log_writer import LogWriter
    lw = LogWriter("test", log_dir=tmp_path)
    lw.write({"msg": "hello"})
    lw.close()
    log_file = tmp_path / "test.log"
    assert log_file.exists()
    content = log_file.read_text()
    assert "hello" in content
