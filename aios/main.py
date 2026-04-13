#!/usr/bin/env python3
"""AI-OS Main Entry Point - AIOS-CC2"""
import argparse
import asyncio
import os
import sys
import threading
import time
from datetime import datetime, timezone

# Ensure the project root (parent of the aios/ package) is in the Python path
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)  # one level up from aios/ = repo root
for _p in (_root, _here):
    if _p not in sys.path:
        sys.path.insert(0, _p)

ASCII_LOGO = r"""
  ╔══════════════════════════════════════════════════════╗
  ║   ██████╗ ██╗      ██████╗  ███████╗                 ║
  ║  ██╔══██╗██║     ██╔═══██╗ ██╔════╝                 ║
  ║  ███████║██║     ██║   ██║ ███████╗                 ║
  ║  ██╔══██║██║     ██║   ██║ ╚════██║                 ║
  ║  ██║  ██║███████╗╚██████╔╝ ███████║                 ║
  ║  ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚══════╝  CC2           ║
  ╠══════════════════════════════════════════════════════╣
  ║  AI-OS v2.0.0-CC2  |  Operator: Chris               ║
  ║  Internal Network: 10.0.0.0/8 (VIRTUAL)             ║
  ║  Status: INITIALIZING...                            ║
  ╚══════════════════════════════════════════════════════╝
"""


def parse_args():
    parser = argparse.ArgumentParser(description="AI-OS v2.0.0-CC2")
    parser.add_argument("--ui", choices=["terminal", "web", "none"], default="terminal",
                        help="UI mode: terminal (curses), web (browser), none (background)")
    parser.add_argument("--operator-token", default=None,
                        help="Operator authentication token")
    parser.add_argument("--port", type=int, default=1313,
                        help="Web server port (default: 1313)")
    return parser.parse_args()


def boot_subsystems():
    """Initialize all subsystems in order."""
    import os
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

    # Base persistence directory
    _persist_base = os.path.join(os.path.expanduser("~"), ".aios")

    print("  [1/14] StateRegistry ...")
    state = StateRegistry()
    state.set_persist_path(os.path.join(_persist_base, "state.json"))

    print("  [2/14] PolicyEngine ...")
    policy = PolicyEngine()

    print("  [3/14] SecurityKernel ...")
    security = SecurityKernel()

    print("  [4/14] IdentityLock ...")
    identity = IdentityLock()
    identity.load()
    print(f"         Operator: {identity.get_operator()} | Level: {identity.get_level()}")

    # Authenticate the security kernel using the identity lock file
    _identity_lock_path = str(
        __import__("pathlib").Path(__file__).parent / "identity" / "identity.lock"
    )
    try:
        _auth_token = security.authenticate(_identity_lock_path)
        print(f"         SecurityKernel authenticated (token: {_auth_token[:12]}...)")
    except Exception as _auth_exc:
        print(f"         WARNING: SecurityKernel auth failed: {_auth_exc}")

    print("  [5/14] MemoryMapController ...")
    memory = MemoryMapController()
    memory.allocate("kernel", 4096)
    memory.allocate("heap", 16384)
    memory.allocate("stack", 2048)
    memory.allocate("shared", 8192)

    print("  [6/14] Virtual Hardware ...")
    vcpu = VirtualCPU()
    vmem = VirtualMemory()
    vstorage = VirtualStorage(persist_dir=os.path.join(_persist_base, "vstorage"))
    vnet = VirtualNetwork()
    vnet.create_interface("lo0")
    vnet.create_interface("eth0")
    vnet.create_interface("mesh0")
    vsensors = VirtualSensors()
    vsensors.tick()

    print("  [7/14] HostBridge ...")
    bridge = HostBridge()
    bridge_info = bridge.boot()
    print(f"         Host OS: {bridge_info.get('host_os','?')} | CPUs: {bridge_info.get('cpu_count','?')}")

    print("  [8/14] NodeMesh ...")
    mesh = NodeMesh()
    for node in ["core", "engine", "bridge", "command", "web", "heartbeat", "procwriter"]:
        mesh.add_node(node)

    print("  [9/14] HeartbeatSystem ...")
    heartbeat = HeartbeatSystem(node_mesh=mesh)

    print("  [10/14] AuraEngine ...")
    aura = AuraEngine(state_registry=state)
    aura_boot = aura.boot()
    print(f"          Sub-engines: {len(aura_boot.get('sub_engines', []))}")

    print("  [11/14] ProcessSupervisor ...")
    supervisor = ProcessSupervisor()

    # Register a coroutine factory that properly activates and runs the heartbeat
    async def _heartbeat_runner():
        heartbeat._running = True
        await heartbeat._run()

    supervisor.register("heartbeat", _heartbeat_runner)

    print("  [12/14] ProcWriters ...")
    proc_writers = ProcWriters(vstorage=vstorage)

    print("  [13/14] Sandbox ...")
    sandbox = Sandbox()

    print("  [14/15] CommandCenter ...")
    cc = CommandCenter()

    print("  [15/15] CloudController ...")
    from aios.cloud.cloud_controller import CloudController
    from aios.cloud.cloud_loop import CloudLoop
    cloud = CloudController(state_registry=state, mesh=mesh, vcpu=vcpu)
    cloud.boot()
    # Auto-spawn one worker node so the cloud is immediately operational
    _spawn = cloud.spawn_node()
    if "error" not in _spawn:
        print(f"         Auto-spawned cloud node: {_spawn.get('node_id')} on port {_spawn.get('port')}")
    else:
        print(f"         WARNING: Could not auto-spawn cloud node: {_spawn.get('error')}")
    cloud_loop = CloudLoop(cloud_controller=cloud, mesh=mesh)

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

    return {
        "state": state,
        "policy": policy,
        "security": security,
        "identity": identity,
        "memory": memory,
        "vcpu": vcpu,
        "vmem": vmem,
        "vstorage": vstorage,
        "vnet": vnet,
        "vsensors": vsensors,
        "bridge": bridge,
        "mesh": mesh,
        "heartbeat": heartbeat,
        "aura": aura,
        "supervisor": supervisor,
        "proc_writers": proc_writers,
        "sandbox": sandbox,
        "cloud": cloud,
        "cloud_loop": cloud_loop,
        "cc": cc,
    }


def start_web_server(cc, port):
    """Start web server in background thread."""
    from aios.web.server import AIWebServer
    srv = AIWebServer(command_center=cc)
    srv.PORT = port
    try:
        srv.start()
        print(f"  [WEB] Server started: http://localhost:{port}")
    except OSError as e:
        print(f"  [WEB] WARNING: Could not bind to port {port}: {e}")
        print(f"  [WEB] Web UI unavailable. Use --port to choose a different port.")
    return srv


def endless_loop(subsystems, stop_event):
    """The main endless loop: tick all engines, heartbeat, update state."""
    cc = subsystems["cc"]
    aura = subsystems["aura"]
    vsensors = subsystems["vsensors"]
    vcpu = subsystems["vcpu"]
    bridge = subsystems["bridge"]
    proc_writers = subsystems["proc_writers"]
    state = subsystems["state"]
    heartbeat = subsystems["heartbeat"]
    cloud = subsystems.get("cloud")

    tick = 0
    last_heartbeat = 0

    while not stop_event.is_set():
        tick += 1
        now = time.time()

        try:
            aura.tick()
        except Exception:
            pass

        try:
            vsensors.tick()
        except Exception:
            pass

        try:
            vcpu.tick()
        except Exception:
            pass

        try:
            bridge.tick()
        except Exception:
            pass

        try:
            proc_writers.tick()
        except Exception:
            pass

        try:
            if cloud and cloud._running:
                cloud.tick()
        except Exception:
            pass

        try:
            state.set("tick", tick, namespace="system")
            state.set("timestamp", datetime.now(timezone.utc).isoformat(), namespace="system")
        except Exception:
            pass

        if now - last_heartbeat >= 5.0:
            last_heartbeat = now
            try:
                heartbeat.beat_sync()
            except Exception:
                pass

        if not cc._running:
            stop_event.set()
            break

        time.sleep(1.0)


def run_async_mesh(subsystems):
    """Start mesh and heartbeat in an asyncio loop, with ProcessSupervisor tracking."""
    async def _run():
        supervisor = subsystems.get("supervisor")
        if supervisor:
            # supervisor.start_all() includes the heartbeat_runner which sets _running=True
            await supervisor.start_all()
        else:
            subsystems["heartbeat"].start()
        while subsystems["cc"]._running:
            await asyncio.sleep(1)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run())
    finally:
        loop.close()


def main():
    print(ASCII_LOGO)
    print(f"  Boot time: {datetime.now(timezone.utc).isoformat()}")
    print()

    args = parse_args()
    subsystems = boot_subsystems()
    cc = subsystems["cc"]

    # Validate operator token if provided on command line
    if args.operator_token:
        identity = subsystems["identity"]
        if identity.is_operator(args.operator_token):
            print("  [AUTH] Operator token accepted.")
        else:
            print("  [AUTH] WARNING: Provided operator token is invalid. Continuing as unauthenticated.")

    print()
    print("  ═══════════════════════════════════════")
    print("  All subsystems ONLINE. AI-OS is ready.")
    print("  ═══════════════════════════════════════")
    print()

    web_server = start_web_server(cc, args.port)

    stop_event = threading.Event()

    # Start the async mesh/heartbeat thread
    mesh_thread = threading.Thread(target=run_async_mesh, args=(subsystems,), daemon=True)
    mesh_thread.start()

    # Start the cloud loop (never-exit)
    cloud_loop = subsystems.get("cloud_loop")
    if cloud_loop:
        cloud_loop.start()
        print("  [CLOUD] Cloud loop started.")

    # Start the endless loop thread
    loop_thread = threading.Thread(target=endless_loop, args=(subsystems, stop_event), daemon=True)
    loop_thread.start()

    if args.ui == "terminal":
        from aios.terminal.ui_main import TerminalUI
        ui = TerminalUI(command_center=cc)
        try:
            ui.start()
        except Exception as e:
            print(f"\n  [UI] Terminal UI failed: {e}")
            print("  [UI] Falling back to background mode. Press Ctrl+C to stop.")
            try:
                while cc._running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n  Interrupted by operator.")
        stop_event.set()

    elif args.ui == "web":
        print(f"  Web UI running at: http://localhost:{args.port}")
        print("  Press Ctrl+C to stop.")
        try:
            while cc._running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n  Interrupted by operator.")
        stop_event.set()

    elif args.ui == "none":
        print("  Running in background mode. Press Ctrl+C to stop.")
        try:
            while cc._running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n  Interrupted by operator.")
        stop_event.set()

    web_server.stop()
    if cloud_loop:
        cloud_loop.stop()
    print("  AI-OS shutdown complete.")


if __name__ == "__main__":
    main()
