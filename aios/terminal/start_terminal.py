#!/usr/bin/env python3
"""AI-OS Terminal Entry Point — full boot sequence matching main.py.

This is a convenience launcher for the curses terminal UI.
For all options (web mode, background mode, --debug) use main.py directly.
"""
import os
import sys
import threading
import time
import asyncio

# Ensure aios package is importable
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_here))  # repo root
for _p in (_root, os.path.dirname(_here)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

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
from aios.command.command_center import CommandCenter
from aios.procwriters.proc_writers import ProcWriters
from aios.sandbox.sandbox import Sandbox
from aios.cloud.cloud_controller import CloudController
from aios.cloud.cloud_loop import CloudLoop
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
    memory.allocate("shared", 8192)

    vcpu = VirtualCPU()
    vmem = VirtualMemory()
    vstorage = VirtualStorage()
    vnet = VirtualNetwork()
    vnet.create_interface("lo0")
    vnet.create_interface("eth0")
    vnet.create_interface("mesh0")
    vsensors = VirtualSensors()
    vsensors.tick()

    bridge = HostBridge()
    bridge.boot()

    mesh = NodeMesh()
    for node in ["core", "engine", "bridge", "command", "web", "heartbeat", "procwriter"]:
        mesh.add_node(node)

    heartbeat = HeartbeatSystem(node_mesh=mesh)

    aura = AuraEngine(state_registry=state)
    aura.boot()

    supervisor = ProcessSupervisor()
    proc_writers = ProcWriters(vstorage=vstorage)
    sandbox = Sandbox()

    cloud = CloudController(state_registry=state, mesh=mesh, vcpu=vcpu)
    cloud.boot()
    cloud_loop = CloudLoop(cloud_controller=cloud, mesh=mesh)

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
        supervisor=supervisor,
        proc_writers=proc_writers,
        sandbox=sandbox,
        cloud=cloud,
    )
    cc.boot()
    print("  [BOOT] All subsystems ONLINE.")
    return cc, heartbeat, cloud_loop


def _run_async_mesh(cc, heartbeat):
    async def _run():
        heartbeat.start()
        while cc._running:
            await asyncio.sleep(1)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()


def main():
    cc, heartbeat, cloud_loop = boot_system()

    # Start async mesh heartbeat
    mesh_thread = threading.Thread(
        target=_run_async_mesh, args=(cc, heartbeat), daemon=True
    )
    mesh_thread.start()

    cloud_loop.start()

    print("  [BOOT] Launching Terminal UI...")
    ui = TerminalUI(command_center=cc)
    try:
        ui.start()
    except Exception as e:
        print(f"\n  [UI] Terminal UI failed: {e}")
        print("  [UI] Press Ctrl+C to stop.")
        try:
            while cc._running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    cloud_loop.stop()
    print("  AI-OS shutdown complete.")


if __name__ == "__main__":
    main()
