#!/usr/bin/env python3
"""AI-OS Main Entry Point - AIOS-CC2"""
import argparse
import asyncio
import os
import signal
import sys
import threading
import time
import traceback
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
    default_port = int(os.environ.get("AIOS_PORT", 1313))
    parser.add_argument("--port", type=int, default=default_port,
                        help="Web server port (default: 1313, or $AIOS_PORT env var)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable verbose debug output and write logs/debug.log")
    return parser.parse_args()


def boot_subsystems():
    """Initialize all subsystems in order."""
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

    print("  [1/14] StateRegistry ...")
    state = StateRegistry()

    print("  [2/14] PolicyEngine ...")
    policy = PolicyEngine()

    print("  [3/14] SecurityKernel ...")
    security = SecurityKernel()

    print("  [4/14] IdentityLock ...")
    identity = IdentityLock()
    identity.load()
    print(f"         Operator: {identity.get_operator()} | Level: {identity.get_level()}")

    print("  [5/14] MemoryMapController ...")
    memory = MemoryMapController()
    memory.allocate("kernel", 4096)
    memory.allocate("heap", 16384)
    memory.allocate("stack", 2048)
    memory.allocate("shared", 8192)

    print("  [6/14] Virtual Hardware ...")
    vcpu = VirtualCPU()
    vmem = VirtualMemory()
    vstorage = VirtualStorage()
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

    # Attach persistent log writer
    from aios.core.log_writer import LogWriter
    log_writer = LogWriter("aios")
    cc.attach_log_writer(log_writer)

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
    """Start web server in background thread.

    Returns the ``AIWebServer`` instance.  If the port is unavailable the
    server is returned in an unbound state so the rest of the system can
    continue running — only the web UI will be absent.
    """
    from aios.web.server import AIWebServer
    srv = AIWebServer(command_center=cc)
    srv.PORT = port
    try:
        srv.start()
        print(f"  [WEB] Server started:  http://localhost:{port}")
    except OSError as e:
        print()
        print(f"  [WEB] ERROR: Could not bind to port {port}.")
        print(f"  [WEB]   {e}")
        print(f"  [WEB] To use a different port, run:")
        print(f"  [WEB]     python aios/main.py --port <PORT>")
        print(f"  [WEB]   or set:  export AIOS_PORT=<PORT>")
        print(f"  [WEB] To find what is using port {port}, run:")
        print(f"  [WEB]     lsof -i :{port}   (Linux/Mac/Termux)")
        print(f"  [WEB]     netstat -ano | findstr :{port}   (Windows)")
        print(f"  [WEB] Web UI unavailable — all other subsystems remain ONLINE.")
        print()
    return srv


def endless_loop(subsystems, stop_event, debug=False):
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
            if debug:
                traceback.print_exc()

        try:
            vsensors.tick()
        except Exception:
            if debug:
                traceback.print_exc()

        try:
            vcpu.tick()
        except Exception:
            if debug:
                traceback.print_exc()

        try:
            bridge.tick()
        except Exception:
            if debug:
                traceback.print_exc()

        try:
            proc_writers.tick()
        except Exception:
            if debug:
                traceback.print_exc()

        try:
            if cloud and cloud._running:
                cloud.tick()
        except Exception:
            if debug:
                traceback.print_exc()

        try:
            state.set("tick", tick, namespace="system")
            state.set("timestamp", datetime.now(timezone.utc).isoformat(), namespace="system")
        except Exception:
            if debug:
                traceback.print_exc()

        hb_interval = 1.0 if debug else 5.0
        if now - last_heartbeat >= hb_interval:
            last_heartbeat = now
            try:
                heartbeat.beat_sync()
            except Exception:
                if debug:
                    traceback.print_exc()

        if not cc._running:
            stop_event.set()
            break

        time.sleep(1.0)


def run_async_mesh(subsystems):
    """Start mesh and heartbeat in an asyncio loop."""
    async def _run():
        heartbeat = subsystems["heartbeat"]
        heartbeat.start()
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

    # ── Debug log file ───────────────────────────────────────────────────────
    if args.debug:
        logs_dir = os.path.join(os.path.dirname(_here), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        debug_log_path = os.path.join(logs_dir, "debug.log")
        print(f"  [DEBUG] Verbose mode ON. Log: {debug_log_path}")

    subsystems = boot_subsystems()
    cc = subsystems["cc"]

    # ── SIGTERM handler (Docker stop / systemd stop) ─────────────────────────
    def _handle_sigterm(signum, frame):
        print("\n  [SIGNAL] SIGTERM received. Shutting down gracefully...")
        cc._running = False

    signal.signal(signal.SIGTERM, _handle_sigterm)

    # Validate operator token if provided on command line
    if args.operator_token:
        identity = subsystems["identity"]
        if identity.is_operator(args.operator_token):
            print("  [AUTH] Operator token accepted.")
        else:
            print("  [AUTH] WARNING: Provided operator token is invalid. Continuing as unauthenticated.")

    web_server = start_web_server(cc, args.port)

    print()
    print("  ═══════════════════════════════════════")
    print("  All subsystems ONLINE. AI-OS is ready.")
    if web_server.is_bound():
        print(f"  Web UI: http://localhost:{args.port}")
    print("  ═══════════════════════════════════════")
    print()

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
    loop_thread = threading.Thread(
        target=endless_loop, args=(subsystems, stop_event, args.debug), daemon=True
    )
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
