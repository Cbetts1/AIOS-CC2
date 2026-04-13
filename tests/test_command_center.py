"""Tests for CommandCenter — every menu key must produce non-empty output."""
import pytest
from aios.command.command_center import CommandCenter
from aios.core.state_registry import StateRegistry
from aios.core.policy_engine import PolicyEngine
from aios.core.security_kernel import SecurityKernel
from aios.core.identity_lock import IdentityLock
from aios.core.memory_map import MemoryMapController
from aios.core.process_supervisor import ProcessSupervisor
from aios.virtual.vcpu import VirtualCPU
from aios.virtual.vmemory import VirtualMemory
from aios.virtual.vstorage import VirtualStorage
from aios.virtual.vnetwork import VirtualNetwork
from aios.virtual.vsensors import VirtualSensors
from aios.bridge.host_bridge import HostBridge
from aios.mesh.node_mesh import NodeMesh
from aios.mesh.heartbeat import HeartbeatSystem
from aios.engine.aura import AuraEngine
from aios.procwriters.proc_writers import ProcWriters
from aios.sandbox.sandbox import Sandbox
from aios.cloud.cloud_controller import CloudController


@pytest.fixture
def cc():
    """A fully wired CommandCenter instance."""
    state = StateRegistry()
    policy = PolicyEngine()
    security = SecurityKernel()
    identity = IdentityLock()
    identity.load()
    memory = MemoryMapController()
    memory.allocate("kernel", 1024)
    vcpu = VirtualCPU()
    vmem = VirtualMemory()
    vstorage = VirtualStorage()
    vnet = VirtualNetwork()
    vnet.create_interface("eth0")
    vsensors = VirtualSensors()
    vsensors.tick()
    bridge = HostBridge()
    bridge.boot()
    mesh = NodeMesh()
    mesh.add_node("core")
    heartbeat = HeartbeatSystem(node_mesh=mesh)
    heartbeat.beat_sync()
    aura = AuraEngine(state_registry=state)
    aura.boot()
    supervisor = ProcessSupervisor()
    proc_writers = ProcWriters(vstorage=vstorage)
    sandbox = Sandbox()
    cloud = CloudController(state_registry=state, mesh=mesh, vcpu=vcpu)
    cloud.boot()

    center = CommandCenter()
    center.attach(
        state=state, policy=policy, security=security, identity=identity,
        memory=memory, vcpu=vcpu, vmem=vmem, vstorage=vstorage, vnet=vnet,
        vsensors=vsensors, bridge=bridge, mesh=mesh, heartbeat=heartbeat,
        aura=aura, supervisor=supervisor, proc_writers=proc_writers,
        sandbox=sandbox, cloud=cloud,
    )
    center.boot()
    return center


def test_top_level_menu_items(cc):
    """Every top-level menu number returns a non-empty string."""
    for key in CommandCenter.MENU:
        result = cc.handle_command(key)
        assert isinstance(result, str), f"Menu {key} returned non-string"
        assert result.strip(), f"Menu {key} returned empty output"


def test_all_sub_commands(cc):
    """Every sub-command returns a non-empty string without raising."""
    for top, (name, sub_menu) in CommandCenter.MENU.items():
        for sub in sub_menu:
            cmd = f"{top}.{sub}"
            try:
                result = cc.handle_command(cmd)
                assert isinstance(result, str), f"{cmd} returned non-string"
                assert result.strip(), f"{cmd} returned empty output"
            except Exception as exc:
                pytest.fail(f"handle_command('{cmd}') raised: {exc}")


def test_unknown_command(cc):
    result = cc.handle_command("99")
    assert "Unknown" in result or "99" in result


def test_cloud_text_commands(cc):
    for cmd in ("cloud status", "cloud start", "cloud stop"):
        result = cc.handle_command(cmd)
        assert isinstance(result, str)
        assert result.strip()


def test_shutdown_requires_token(cc):
    result = cc.shutdown("wrong-token")
    assert "REFUSED" in result or "Invalid" in result
