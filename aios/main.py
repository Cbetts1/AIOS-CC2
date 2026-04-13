#!/usr/bin/env python3
"""AI-OS Main Entry Point - AIOS-CC2"""
import argparse
import asyncio
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure the project root (parent of the aios/ package) is in the Python path
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)  # one level up from aios/ = repo root
for _p in (_root, _here):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Data directory: honours AIOS_DATA_DIR env var, defaults to ~/.aios
AIOS_DATA_DIR = os.environ.get(
    "AIOS_DATA_DIR",
    os.path.join(os.path.expanduser("~"), ".aios"),
)

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
    policy.set_log_file(os.path.join(AIOS_DATA_DIR, "logs", "policy.jsonl"))

    print("  [3/14] SecurityKernel ...")
    security = SecurityKernel()
    security.set_log_file(os.path.join(AIOS_DATA_DIR, "logs", "security.jsonl"))

    print("  [4/14] IdentityLock ...")
    identity = IdentityLock()
    identity.load()
    print(f"         Operator: {identity.get_operator()} | Level: {identity.get_level()}")

    # Wire SecurityKernel — authenticate using the identity.lock file
    try:
        security.authenticate(str(identity._find_identity_file()))
        print("         SecurityKernel authenticated.")
    except Exception as _sec_exc:
        print(f"         SecurityKernel WARNING: {_sec_exc}")

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

    # Restore VirtualStorage from disk (no-op on first boot)
    _vstorage_path = os.path.join(AIOS_DATA_DIR, "vstorage.json")
    if vstorage.load_from_file(_vstorage_path):
        print(f"         VirtualStorage restored from {_vstorage_path}")

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
        heartbeat.activate()
        await heartbeat._run()

    supervisor.register("heartbeat", _heartbeat_runner)

    print("  [12/14] ProcWriters ...")
    proc_writers = ProcWriters(vstorage=vstorage)

    print("  [13/14] Sandbox ...")
    sandbox = Sandbox()

    print("  [14/14] CommandCenter ...")
    cc = CommandCenter()
    cc.set_log_file(os.path.join(AIOS_DATA_DIR, "logs", "console.jsonl"))

    print("  [15/15] CloudController ...")
    from aios.cloud.cloud_controller import CloudController
    from aios.cloud.cloud_loop import CloudLoop
    from aios.cloud.cloud_api import CloudAPI
    cloud = CloudController(state_registry=state, mesh=mesh, vcpu=vcpu)
    cloud.boot()
    # Auto-spawn one worker node so the cloud is immediately operational
    _spawn = cloud.spawn_node()
    if "error" not in _spawn:
        print(f"         Auto-spawned cloud node: {_spawn.get('node_id')} on port {_spawn.get('port')}")
    else:
        print(f"         WARNING: Could not auto-spawn cloud node: {_spawn.get('error')}")
    cloud_loop = CloudLoop(cloud_controller=cloud, mesh=mesh)
    cloud_api = CloudAPI(cloud_controller=cloud)

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
    # Attach CloudAPI separately (not in MENU-driven attach loop)
    cc._cloud_api = cloud_api
    cc.boot()

    # Restore StateRegistry from disk (no-op on first boot)
    _state_path = os.path.join(AIOS_DATA_DIR, "state_registry.json")
    if state.load_from_file(_state_path):
        print(f"         StateRegistry restored from {_state_path}")

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
        "_vstorage_path": _vstorage_path,
        "_state_path": _state_path,
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


def _watchdog_restart(name: str, subsystems: dict) -> None:
    """Attempt to restart a subsystem that has been unhealthy too long."""
    try:
        comp = subsystems.get(name)
        if comp is None:
            return
        if hasattr(comp, "boot"):
            comp.boot()
        elif hasattr(comp, "start"):
            comp.start()
        # Log the watchdog action through SecurityKernel if available
        cc = subsystems.get("cc")
        if cc and getattr(cc, "_security", None):
            cc._security.log_security_event({
                "type": "WATCHDOG_RESTART",
                "component": name,
            })
    except Exception:
        pass


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
    state_path = subsystems.get("_state_path", "")
    vstorage_path = subsystems.get("_vstorage_path", "")
    vstorage = subsystems["vstorage"]

    tick = 0
    last_heartbeat = 0
    _unhealthy_counts: dict = {}
    WATCHDOG_THRESHOLD = 3

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

        # Flush StateRegistry to disk every 60 ticks (≈ 60 s)
        if tick % 60 == 0 and state_path:
            try:
                state.flush_to_file(state_path)
            except Exception:
                pass

        # Watchdog: inspect subsystem health every 30 ticks (≈ 30 s)
        if tick % 30 == 0:
            try:
                full_status = cc.get_status_dict()
                for comp_name, comp_status in full_status.items():
                    if not isinstance(comp_status, dict):
                        continue
                    if "healthy" not in comp_status:
                        continue
                    if not comp_status.get("healthy", True):
                        _unhealthy_counts[comp_name] = _unhealthy_counts.get(comp_name, 0) + 1
                        if _unhealthy_counts[comp_name] >= WATCHDOG_THRESHOLD:
                            _watchdog_restart(comp_name, subsystems)
                            _unhealthy_counts[comp_name] = 0
                    else:
                        _unhealthy_counts[comp_name] = 0
            except Exception:
                pass

        if not cc._running:
            stop_event.set()
            break

        time.sleep(1.0)

    # Persist state on clean exit
    if state_path:
        try:
            state.flush_to_file(state_path)
        except Exception:
            pass
    if vstorage_path:
        try:
            vstorage.save_to_file(vstorage_path)
        except Exception:
            pass


def run_async_mesh(subsystems):
    """Start mesh and heartbeat in an asyncio loop.

    Also registers the heartbeat coroutine with ProcessSupervisor so the
    supervisor tracks and can restart it on failure.
    """
    async def _run():
        heartbeat = subsystems["heartbeat"]
        supervisor = subsystems["supervisor"]
        # Register the heartbeat with ProcessSupervisor for tracking
        try:
            supervisor.register("heartbeat", heartbeat._run)
            await supervisor.start_all()
        except Exception:
            pass
        # Also start via the HeartbeatSystem's own method (both paths work)
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
    subsystems = boot_subsystems()
    cc = subsystems["cc"]

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
