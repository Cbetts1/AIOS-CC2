#!/usr/bin/env python3
"""AI-OS Terminal Entry Point - Boots AI-OS and launches terminal UI.

.. deprecated::
    This module is superseded by ``aios/main.py``.  Use::

        python aios/main.py --ui terminal

    ``start_terminal.py`` boots a reduced subset of subsystems (no cloud,
    no ProcessSupervisor, no VirtualStorage persistence) and is kept only
    for backward compatibility.  It may be removed in a future release.
"""
import os
import sys

# Ensure aios package is importable
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
if _root not in sys.path:
    sys.path.insert(0, _root)

from aios.core.state_registry import StateRegistry
from aios.core.policy_engine import PolicyEngine
from aios.core.security_kernel import SecurityKernel
from aios.core.identity_lock import IdentityLock
from aios.core.memory_map import MemoryMapController
from aios.virtual.vcpu import VirtualCPU
from aios.virtual.vmemory import VirtualMemory
from aios.virtual.vstorage import VirtualStorage
from aios.virtual.vnetwork import VirtualNetwork
from aios.virtual.vsensors import VirtualSensors
from aios.bridge.host_bridge import HostBridge
from aios.mesh.node_mesh import NodeMesh
from aios.mesh.heartbeat import HeartbeatSystem
from aios.engine.aura import AuraEngine
from aios.command.command_center import CommandCenter
from aios.sandbox.sandbox import Sandbox
from aios.terminal.ui_main import TerminalUI


def boot_system():
    print("  [BOOT] Initializing AI-OS subsystems...")

    state = StateRegistry()
    policy = PolicyEngine()
    security = SecurityKernel()
    identity = IdentityLock()
    identity.load()

    memory = MemoryMapController()
    memory.allocate("kernel", 4096)
    memory.allocate("heap", 16384)
    memory.allocate("stack", 2048)

    vcpu = VirtualCPU()
    vmem = VirtualMemory()
    vstorage = VirtualStorage()
    vnet = VirtualNetwork()
    vnet.create_interface("lo0")
    vnet.create_interface("eth0")
    vsensors = VirtualSensors()
    vsensors.tick()

    bridge = HostBridge()
    bridge.boot()

    mesh = NodeMesh()
    for node in ["core", "engine", "bridge", "command", "web"]:
        mesh.add_node(node)

    heartbeat = HeartbeatSystem(node_mesh=mesh)

    aura = AuraEngine(state_registry=state)
    aura.boot()

    sandbox = Sandbox()

    cc = CommandCenter()
    cc.attach(
        state=state,
        policy=policy,
        security=security,
        identity=identity,
        memory=memory,
        vcpu=vcpu,
        vmem=vmem,
        vstorage=vstorage,
        vnet=vnet,
        vsensors=vsensors,
        bridge=bridge,
        mesh=mesh,
        heartbeat=heartbeat,
        aura=aura,
        sandbox=sandbox,
    )
    cc.boot()
    print("  [BOOT] All subsystems ONLINE.")
    return cc, heartbeat


def main():
    cc, heartbeat = boot_system()
    ui = TerminalUI(command_center=cc)
    print("  [BOOT] Launching Terminal UI...")
    ui.start()


if __name__ == "__main__":
    main()
