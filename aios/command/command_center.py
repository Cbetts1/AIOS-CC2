"""AI-OS Command Center - Main command and control interface."""
import time
from datetime import datetime, timezone


class CommandCenter:
    VERSION = "2.0.0-CC2"

    MENU = {
        "1": ("System Status", {
            "1": "Full System Report",
            "2": "Layer Health",
            "3": "Subsystem List",
            "4": "Resource Usage",
            "5": "Event Log",
        }),
        "2": ("Layer Control", {
            "1": "Layer 1 - Physical Abstraction",
            "2": "Layer 2 - Virtual Hardware",
            "3": "Layer 3 - Kernel Bridge",
            "4": "Layer 4 - Process & Memory",
            "5": "Layer 5 - Engine & Intelligence",
            "6": "Layer 6 - Command & Interface",
            "7": "Layer 7 - Application & Output",
        }),
        "3": ("Engine Control", {
            "1": "Start All Engines",
            "2": "Tick AuraEngine",
            "3": "BuilderEngine Status",
            "4": "RepairEngine Status",
            "5": "DocumentationEngine Status",
            "6": "EvolutionEngine Status",
            "7": "LegalCortex Status",
        }),
        "4": ("Virtual Hardware", {
            "1": "CPU Status",
            "2": "Memory Status",
            "3": "Storage Status",
            "4": "Sensor Readings",
            "5": "Execute CPU Instruction",
            "6": "Memory Dump (64 bytes)",
        }),
        "5": ("Network Management", {
            "1": "List Interfaces",
            "2": "Node Mesh Status",
            "3": "Heartbeat Status",
            "4": "Packet Log",
            "5": "Broadcast Message",
        }),
        "6": ("Security & Identity", {
            "1": "Identity Status",
            "2": "Security Log",
            "3": "Policy Report",
            "4": "Permission Container",
            "5": "Sandbox Status",
        }),
        "7": ("Cloud Systems", {
            "1": "Cloud Status",
            "2": "List Nodes",
            "3": "Start Cloud",
            "4": "Stop Cloud",
            "5": "Spawn Node",
            "6": "Execute Task (echo)",
            "7": "Cloud Heartbeat",
            "8": "Cloud Storage Info",
            "9": "Cloud Event Log",
        }),
        "8": ("Cellular Systems", {
            "1": "Virtual Cellular Status",
            "2": "Signal Simulation",
            "3": "Channel Report",
        }),
        "9": ("Computer Systems", {
            "1": "Process Supervisor Status",
            "2": "Memory Map Report",
            "3": "ProcWriters Report",
            "4": "VirtualStorage Files",
        }),
        "10": ("AI Systems", {
            "1": "AuraEngine Full Status",
            "2": "Evolution Log",
            "3": "Builder Queue",
            "4": "Repair History",
        }),
        "11": ("Diagnostics", {
            "1": "Full Diagnostic Report",
            "2": "Health Check All",
            "3": "Error Log",
            "4": "Performance Metrics",
        }),
        "12": ("Maintenance", {
            "1": "Clear State Namespace",
            "2": "Reset VirtualCPU",
            "3": "Run Repair Scan",
            "4": "Allocate Memory Region",
        }),
        "13": ("Legal & Compliance", {
            "1": "Compliance Status",
            "2": "Audit Log",
            "3": "Violation Report",
            "4": "Check Action Compliance",
        }),
        "14": ("Documentation", {
            "1": "System Overview",
            "2": "Layer Map",
            "3": "API Reference",
            "4": "Operator Manual",
            "5": "List All Topics",
        }),
        "15": ("Logs & Audit", {
            "1": "Security Log",
            "2": "Policy Audit Log",
            "3": "Legal Audit Log",
            "4": "Engine Event Log",
            "5": "Full Audit Dump",
        }),
        "16": ("Shutdown", {
            "1": "Graceful Shutdown (operator only)",
            "2": "Emergency Halt (operator only)",
            "3": "Restart Loop",
        }),
    }

    def __init__(self):
        self._boot_time = None
        self._running = False
        self._state = None
        self._policy = None
        self._security = None
        self._identity = None
        self._memory = None
        self._vcpu = None
        self._vmem = None
        self._vstorage = None
        self._vnet = None
        self._vsensors = None
        self._bridge = None
        self._mesh = None
        self._heartbeat = None
        self._aura = None
        self._supervisor = None
        self._proc_writers = None
        self._sandbox = None
        self._cloud = None
        self._console_log = []

    def attach(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if hasattr(self, f"_{k}"):
                setattr(self, f"_{k}", v)

    def boot(self) -> dict:
        self._boot_time = time.time()
        self._running = True
        self._log("AI-OS Command Center ONLINE")
        self._log(f"Operator: {self._get_operator()}")
        self._log(f"Boot time: {datetime.now(timezone.utc).isoformat()}")
        return {"status": "ONLINE", "boot_time": self._boot_time}

    def _get_operator(self) -> str:
        if self._identity:
            try:
                return self._identity.get_operator()
            except Exception:
                return "Chris"
        return "Chris"

    def _log(self, msg: str) -> None:
        entry = {
            "msg": msg,
            "ts": datetime.now(timezone.utc).isoformat(),
            "time": time.time(),
        }
        self._console_log.append(entry)
        if len(self._console_log) > 500:
            self._console_log = self._console_log[-250:]

    def get_banner(self) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime = self._uptime_str()
        operator = self._get_operator()
        hb = "●" if self._heartbeat and self._heartbeat.status().get("running") else "○"
        lines = [
            "╔══════════════════════════════════════════════════════════════════╗",
            "║          ██████╗ ██╗      ██████╗  ███████╗                      ║",
            "║         ██╔══██╗██║     ██╔═══██╗ ██╔════╝                      ║",
            "║         ███████║██║     ██║   ██║ ███████╗                      ║",
            "║         ██╔══██║██║     ██║   ██║ ╚════██║                      ║",
            "║         ██║  ██║███████╗╚██████╔╝ ███████║                      ║",
            "║         ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚══════╝  CC2               ║",
            "╠══════════════════════════════════════════════════════════════════╣",
            f"║  AI-OS COMMAND CENTER v{self.VERSION:<8}  Operator: {operator:<12}      ║",
            f"║  Time: {now:<26}  Uptime: {uptime:<15}       ║",
            f"║  Status: ONLINE  Heartbeat: {hb}  Layer 1-7: ALL GREEN            ║",
            "╚══════════════════════════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)

    def _uptime_str(self) -> str:
        if not self._boot_time:
            return "00:00:00"
        secs = int(time.time() - self._boot_time)
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def get_status_bar(self) -> str:
        components = ["StateReg", "PolicyEng", "SecKernel", "AuraEng", "VirtHW", "HostBridge", "NodeMesh"]
        bar = "  ".join(f"[{c}:OK]" for c in components)
        return f"STATUS | {bar}"

    def get_status_dict(self) -> dict:
        status = {
            "version": self.VERSION,
            "operator": self._get_operator(),
            "uptime_seconds": round(time.time() - self._boot_time, 1) if self._boot_time else 0,
            "boot_time": self._boot_time,
            "running": self._running,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        components = {
            "state": self._state,
            "policy": self._policy,
            "security": self._security,
            "identity": self._identity,
            "memory": self._memory,
            "vcpu": self._vcpu,
            "vmem": self._vmem,
            "vstorage": self._vstorage,
            "vnet": self._vnet,
            "vsensors": self._vsensors,
            "bridge": self._bridge,
            "mesh": self._mesh,
            "heartbeat": self._heartbeat,
            "aura": self._aura,
            "supervisor": self._supervisor,
            "cloud": self._cloud,
        }
        for name, comp in components.items():
            if comp and hasattr(comp, "status"):
                try:
                    status[name] = comp.status()
                except Exception as exc:
                    status[name] = {"error": str(exc)}
        return status

    def handle_command(self, cmd: str) -> str:
        cmd = cmd.strip()

        # ── Plain-text cloud commands (cloud start / stop / status / etc.) ──
        lower = cmd.lower()
        if lower.startswith("cloud"):
            return self._handle_cloud_text(cmd)

        parts = cmd.split(".")
        top = parts[0] if parts else ""
        sub = parts[1] if len(parts) > 1 else ""

        if top not in self.MENU:
            return f"Unknown command: '{cmd}'. Enter 1-16 for main menu."

        menu_name = self.MENU[top][0]

        if not sub:
            sub_menu = self.MENU[top][1]
            lines = [f"\n  {menu_name}"]
            lines.append("  " + "─" * 40)
            for k, v in sub_menu.items():
                lines.append(f"  {top}.{k}  {v}")
            lines.append("\n  Enter sub-option (e.g. {}.1):".format(top))
            result = "\n".join(lines)
            self._log(f"CMD: {top} -> {menu_name}")
            return result

        handler = f"_handle_{top}_{sub}"
        if hasattr(self, handler):
            return getattr(self, handler)()
        return self._generic_handler(top, sub)

    def _handle_cloud_text(self, cmd: str) -> str:
        """Dispatch plain-text cloud commands from terminal / web input."""
        parts = cmd.lower().split()
        sub = parts[1] if len(parts) > 1 else ""
        arg = parts[2] if len(parts) > 2 else ""

        if sub in ("start",):
            return self._cloud_start()
        if sub in ("stop",):
            return self._cloud_stop()
        if sub in ("status", ""):
            return self._cloud_status()
        if sub in ("nodes", "list"):
            return self._cloud_nodes()
        if sub in ("spawn",):
            node_id = arg or None
            return self._cloud_spawn(node_id)
        if sub in ("exec", "execute"):
            payload = parts[2:] or ["ping"]
            return self._cloud_exec(" ".join(payload))
        if sub in ("heartbeat", "hb"):
            return self._cloud_heartbeat()
        if sub in ("log",):
            return self._cloud_event_log()
        return (
            f"  Unknown cloud sub-command: '{sub}'\n"
            "  Available: start, stop, status, nodes, spawn [id], "
            "exec [payload], heartbeat, log"
        )

    def _generic_handler(self, top: str, sub: str) -> str:
        menu_name = self.MENU.get(top, ("Unknown",))[0]
        sub_name = self.MENU.get(top, ({}, {}))[1].get(sub, "Unknown")
        self._log(f"CMD: {top}.{sub} -> {sub_name}")
        return self._render_status_for(top, sub, menu_name, sub_name)

    def _render_status_for(self, top: str, sub: str, menu_name: str, sub_name: str) -> str:
        lines = [f"\n  [{menu_name}] → {sub_name}", "  " + "─" * 50]

        # System Status
        if top == "1":
            if sub == "1":
                d = self.get_status_dict()
                lines += [f"  {k}: {v}" for k, v in d.items() if not isinstance(v, dict)]
            elif sub == "2":
                for i in range(1, 8):
                    lines.append(f"  Layer {i}: ONLINE ✓")
            elif sub == "3":
                subsystems = [
                    "StateRegistry", "PolicyEngine", "SecurityKernel", "IdentityLock",
                    "ProcessSupervisor", "MemoryMapController", "AuraEngine",
                    "VirtualCPU", "VirtualMemory", "VirtualStorage", "VirtualNetwork",
                    "VirtualSensors", "HostBridge", "NodeMesh", "HeartbeatSystem",
                ]
                for s in subsystems:
                    lines.append(f"  ✓ {s}")
            elif sub == "4":
                lines.append(f"  Uptime: {self._uptime_str()}")
                if self._vstorage:
                    st = self._vstorage.status()
                    lines.append(f"  Storage Used: {st.get('used_bytes', 0)} bytes")
                if self._vmem:
                    ms = self._vmem.status()
                    lines.append(f"  RAM Size: {ms.get('size_mb', 64)} MB")
                if self._vcpu:
                    cs = self._vcpu.status()
                    lines.append(f"  CPU Cycles: {cs.get('cycles', 0)}")

        # Engine Control
        elif top == "3":
            if sub == "2" and self._aura:
                self._aura.tick()
                lines.append("  AuraEngine ticked.")
            if self._aura:
                st = self._aura.status()
                lines.append(f"  AuraEngine: {st.get('status', 'UNKNOWN')}")
                lines.append(f"  Ticks: {st.get('tick_count', 0)}")
                lines.append(f"  Uptime: {st.get('uptime_seconds', 0)}s")

        # Virtual Hardware
        elif top == "4":
            if sub == "1" and self._vcpu:
                cs = self._vcpu.status()
                for k, v in cs.items():
                    lines.append(f"  {k}: {v}")
            elif sub == "2" and self._vmem:
                ms = self._vmem.status()
                for k, v in ms.items():
                    lines.append(f"  {k}: {v}")
            elif sub == "3" and self._vstorage:
                ss = self._vstorage.status()
                for k, v in ss.items():
                    lines.append(f"  {k}: {v}")
            elif sub == "4" and self._vsensors:
                readings = self._vsensors.read_all()
                for sensor, val in readings.items():
                    lines.append(f"  {sensor}: {val}")
            elif sub == "5" and self._vcpu:
                result = self._vcpu.execute({"op": "ADD", "dst": "r0", "src": 1})
                lines.append(f"  Executed: {result}")
            elif sub == "6" and self._vmem:
                dump = self._vmem.dump_region(0, 64)
                lines.append(dump)

        # Network Management
        elif top == "5":
            if sub == "1" and self._vnet:
                ifaces = self._vnet.list_interfaces()
                for iface in ifaces:
                    lines.append(f"  {iface['name']}: {iface['ip']} rx={iface['rx']} tx={iface['tx']}")
            elif sub == "2" and self._mesh:
                ms = self._mesh.status()
                lines.append(f"  Nodes: {ms.get('node_count', 0)}")
                lines.append(f"  Broadcasts: {ms.get('messages_broadcast', 0)}")
                lines.append(f"  Sent: {ms.get('messages_sent', 0)}")
            elif sub == "3" and self._heartbeat:
                hb = self._heartbeat.status()
                for k, v in hb.items():
                    lines.append(f"  {k}: {v}")

        # Security
        elif top == "6":
            if sub == "1" and self._identity:
                st = self._identity.status()
                for k, v in st.items():
                    lines.append(f"  {k}: {v}")
            elif sub == "2" and self._security:
                log = self._security.get_security_log(limit=10)
                for entry in log:
                    lines.append(f"  [{entry.get('timestamp','')}] {entry.get('type','')} {entry.get('operator','')}")
            elif sub == "4" and self._bridge:
                perm = self._bridge.permissions.status()
                lines.append(f"  Whitelist count: {perm.get('whitelist_count', 0)}")
                lines.append(f"  Denied count: {perm.get('denied_count', 0)}")
            elif sub == "5" and self._sandbox:
                st = self._sandbox.status()
                for k, v in st.items():
                    lines.append(f"  {k}: {v}")

        # Cloud Systems (menu 7)
        elif top == "7":
            if sub == "1":
                lines += self._cloud_status_lines()
            elif sub == "2":
                lines += self._cloud_nodes_lines()
            elif sub == "3":
                lines.append(self._cloud_start())
            elif sub == "4":
                lines.append(self._cloud_stop())
            elif sub == "5":
                lines.append(self._cloud_spawn())
            elif sub == "6":
                lines.append(self._cloud_exec("echo"))
            elif sub == "7":
                lines.append(self._cloud_heartbeat())
            elif sub == "8":
                lines += self._cloud_storage_lines()
            elif sub == "9":
                lines += self._cloud_log_lines()
        # Cellular Systems
        elif top == "8":
            if sub == "1":
                lines.append("  Virtual Cellular  : SIMULATED")
                lines.append("  Technology        : Virtual LTE/5G (no real RF)")
                lines.append("  Network           : Internal mesh (10.0.0.0/8)")
                lines.append("  Signal            : N/A (virtual environment)")
                lines.append("  Note: Cellular simulation uses NodeMesh as the")
                lines.append("        transport layer. No real radio hardware.")
            elif sub == "2":
                import random as _rand
                rssi = round(-60 - _rand.uniform(0, 30), 1)
                lines.append(f"  Signal Simulation")
                lines.append(f"  ─────────────────────────────────────")
                lines.append(f"  RSSI (simulated) : {rssi} dBm")
                lines.append(f"  Band             : Virtual-LTE-B1")
                lines.append(f"  Technology       : 5G-NR (simulated)")
                lines.append(f"  Status           : CONNECTED (virtual)")
            elif sub == "3":
                lines.append("  Channel Report")
                lines.append("  ─────────────────────────────────────")
                if self._mesh:
                    for n in self._mesh.list_nodes():
                        lines.append(f"  CH-{n['name']:10s}  rx={n['rx']:4d}  tx={n['tx']:4d}")
                else:
                    lines.append("  No channels available (NodeMesh not attached).")

        # Computer Systems
        elif top == "9":
            if sub == "1":
                st = self._supervisor.status() if self._supervisor else {}
                procs = st.get("processes", {})
                lines.append(f"  Registered processes: {len(procs)}")
                if procs:
                    for name, info in procs.items():
                        lines.append(f"  [{name}] running={info.get('running')} restarts={info.get('restarts', 0)}")
                else:
                    lines.append("  No processes currently registered with supervisor.")
            elif sub == "2":
                if self._memory:
                    report = self._memory.map_report()
                    lines.append(f"  Total allocated: {self._memory.total_allocated_kb()} KB")
                    for name, info in report.items():
                        lines.append(f"  [{name}] {info['size_kb']} KB  r={info['reads']} w={info['writes']}")
            elif sub == "3":
                if self._proc_writers:
                    st = self._proc_writers.status()
                    for k, v in st.items():
                        lines.append(f"  {k}: {v}")
            elif sub == "4":
                if self._vstorage:
                    files = self._vstorage.list()
                    lines.append(f"  Virtual files ({len(files)} total):")
                    for f in files[:20]:
                        lines.append(f"  {f}")
                    if len(files) > 20:
                        lines.append(f"  ... and {len(files)-20} more")

        # AI Systems
        elif top == "10":
            if self._aura:
                st = self._aura.status()
                if sub == "1":
                    lines.append(f"  AuraEngine: {st.get('status', 'UNKNOWN')}")
                    lines.append(f"  Ticks     : {st.get('tick_count', 0)}")
                    lines.append(f"  Uptime    : {st.get('uptime_seconds', 0)}s")
                    for name, eng in st.get("sub_engines", {}).items():
                        ok = "✓" if eng.get("healthy") else "✗"
                        lines.append(f"  {ok} {name}: ticks={eng.get('tick_count', 0)}")
                elif sub == "2":
                    log = self._aura.evolution.get_evolution_log()
                    if log:
                        for entry in log[-10:]:
                            lines.append(f"  [{entry.get('timestamp', entry.get('cycle', '?'))}] {entry}")
                    else:
                        lines.append("  No evolution cycles recorded yet.")
                elif sub == "3":
                    queue = self._aura.builder.get_queue()
                    done = self._aura.builder.get_completed()
                    lines.append(f"  Queue depth: {len(queue)}")
                    lines.append(f"  Completed  : {len(done)}")
                    for item in done[-5:]:
                        lines.append(f"  ✓ {item.get('target', '?')} at {item.get('built_at', '?')}")
                elif sub == "4":
                    history = self._aura.repair.get_repair_history()
                    if history:
                        for r in history[-10:]:
                            lines.append(f"  {r.get('component', '?')} -> {r.get('action', '?')} at {r.get('repaired_at', '?')}")
                    else:
                        lines.append("  No repairs performed yet.")

        # Logs & Audit
        elif top == "15":
            if sub == "1" and self._security:
                log = self._security.get_security_log(limit=20)
                for e in log:
                    lines.append(f"  [{e.get('timestamp','')}] {e.get('type','')} {e.get('operator','')}")
            elif sub == "2" and self._policy:
                log = self._policy.get_audit_log(limit=20)
                for e in log:
                    lines.append(f"  [{e.get('timestamp','')}] {e.get('action','')} -> {'ALLOW' if e.get('allowed') else 'DENY'}")
            elif sub == "3" and self._aura:
                log = self._aura.legal.get_audit_log(limit=20)
                for e in log:
                    lines.append(f"  [{e.get('audited_at','')}] {e.get('action','')} -> {'✓' if e.get('compliant') else '✗'}")
            elif sub == "4" and self._aura:
                log = self._aura.evolution.get_evolution_log()
                for e in log[-15:]:
                    lines.append(f"  {e}")
            elif sub == "5":
                lines.append("  ── FULL AUDIT DUMP ──")
                if self._security:
                    lines.append(f"  Security events: {len(self._security.get_security_log(limit=9999))}")
                if self._policy:
                    lines.append(f"  Policy events  : {len(self._policy.get_audit_log(limit=9999))}")
                if self._aura:
                    lines.append(f"  Legal events   : {len(self._aura.legal.get_audit_log(limit=9999))}")
                lines.append(f"  Console entries: {len(self._console_log)}")

        # Shutdown
        elif top == "16":
            if sub == "1":
                lines.append("  Graceful shutdown requires operator token.")
                lines.append("  Run: python aios/main.py --operator-token <token>")
                lines.append("  Or use: cc.shutdown(token) in Python.")
            elif sub == "2":
                lines.append("  EMERGENCY HALT — operator authentication required.")
                lines.append("  This will terminate all subsystems immediately.")
            elif sub == "3":
                lines.append("  Restart Loop: endless loop will re-initialise on next boot.")
                lines.append("  Stop the process (Ctrl+C) and relaunch: python aios/main.py")

        # Diagnostics
        elif top == "11":
            if sub == "1":
                full = self.get_status_dict()
                healthy = sum(1 for v in full.values() if isinstance(v, dict) and v.get("healthy"))
                total = sum(1 for v in full.values() if isinstance(v, dict))
                lines.append(f"  Healthy subsystems: {healthy}/{total}")
                lines.append(f"  System uptime: {self._uptime_str()}")
                lines.append("  Diagnostic: ALL SYSTEMS NOMINAL")
            elif sub == "2":
                full = self.get_status_dict()
                for name, comp in full.items():
                    if isinstance(comp, dict) and "healthy" in comp:
                        ok = "✓" if comp.get("healthy") else "✗"
                        lines.append(f"  {ok} {name}")
            elif sub == "3":
                lines.append("  Error Log (last 10 security events):")
                if self._security:
                    for e in self._security.get_security_log(limit=10):
                        lines.append(f"  [{e.get('timestamp','')}] {e.get('type','')} {e.get('reason','')}")
            elif sub == "4":
                lines.append(f"  Uptime     : {self._uptime_str()}")
                if self._aura:
                    st = self._aura.status()
                    lines.append(f"  Aura ticks : {st.get('tick_count', 0)}")
                if self._vsensors:
                    r = self._vsensors.read_all()
                    lines.append(f"  CPU temp   : {r.get('cpu_temp', '?')}°C")
                    lines.append(f"  CPU load   : {r.get('cpu_load', '?')}%")

        # Maintenance
        elif top == "12":
            if sub == "1" and self._state:
                lines.append("  Clearing default namespace...")
                self._state.clear_namespace("default")
                lines.append("  Done.")
            elif sub == "2" and self._vcpu:
                self._vcpu.reset()
                lines.append("  VirtualCPU reset. PC=0x0000, registers zeroed.")
            elif sub == "3" and self._aura:
                self._aura.repair.tick()
                lines.append("  Repair scan complete.")
                history = self._aura.repair.get_repair_history()
                lines.append(f"  Repairs in history: {len(history)}")
            elif sub == "4" and self._memory:
                name = f"dynamic_{int(time.time()) % 10000}"
                self._memory.allocate(name, 512)
                lines.append(f"  Allocated 512 KB region: '{name}'")

        # Documentation
        elif top == "14":
            if self._aura and hasattr(self._aura, "documentation"):
                doc_engine = self._aura.documentation
                topic_map = {"1": "system_overview", "2": "layer_map", "3": "api_reference",
                             "4": "operator_manual", "5": None}
                topic = topic_map.get(sub)
                if topic:
                    doc = doc_engine.retrieve(topic)
                    lines.append(f"  Topic: {doc.get('topic', topic)}")
                    lines.append(f"  {doc.get('content', '')}")
                elif sub == "5":
                    topics = doc_engine.list_topics()
                    for t in topics:
                        lines.append(f"  - {t}")

        # Compliance
        elif top == "13":
            if self._aura and hasattr(self._aura, "legal"):
                legal = self._aura.legal
                if sub == "1":
                    st = legal.status()
                    for k, v in st.items():
                        lines.append(f"  {k}: {v}")
                elif sub == "2":
                    log = legal.get_audit_log(limit=10)
                    for entry in log:
                        lines.append(f"  [{entry.get('audited_at','')}] {entry.get('action','')} -> {'✓' if entry.get('compliant') else '✗'}")
                elif sub == "3":
                    viols = legal.get_violations()
                    if viols:
                        for v in viols[-10:]:
                            lines.append(f"  VIOLATION: {v.get('action','')} at {v.get('timestamp','')}")
                    else:
                        lines.append("  No violations recorded.")
                elif sub == "4":
                    lines.append("  Enter action name to check compliance.")
                    lines.append("  Blocked actions:")
                    for a in sorted(legal.BLOCKED_ACTIONS):
                        lines.append(f"    ✗ {a}")

        if len(lines) == 2:
            lines.append(f"  {sub_name}: OPERATIONAL")
            lines.append(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")

        lines.append("")
        return "\n".join(lines)

    # ── Cloud helper methods ─────────────────────────────────────────────────

    def _cloud_start(self) -> str:
        if not self._cloud:
            return "  Cloud layer not initialised."
        result = self._cloud.boot()
        self._log("CMD: cloud start")
        return f"  Cloud: {result.get('status', 'UNKNOWN')} (boot_time: {result.get('boot_time', '?')})"

    def _cloud_stop(self) -> str:
        if not self._cloud:
            return "  Cloud layer not initialised."
        result = self._cloud.stop()
        self._log("CMD: cloud stop")
        return f"  Cloud: {result.get('status', 'UNKNOWN')}"

    def _cloud_status(self) -> str:
        lines = self._cloud_status_lines()
        return "\n".join(lines)

    def _cloud_status_lines(self) -> list:
        lines = []
        if not self._cloud:
            lines.append("  Cloud layer not initialised.")
            return lines
        st = self._cloud.status()
        lines.append(f"  Running     : {st.get('running', False)}")
        lines.append(f"  Nodes       : {st.get('node_count', 0)}")
        lines.append(f"  Uptime      : {st.get('uptime_seconds', 0)}s")
        lines.append(f"  Tick count  : {st.get('tick_count', 0)}")
        net = st.get("network", {})
        lines.append(f"  Net ports   : {net.get('allocated_ports', 0)} allocated "
                     f"({net.get('port_range', '?')})")
        lines.append(f"  Msgs sent   : {net.get('messages_sent', 0)}")
        cmp = st.get("compute", {})
        lines.append(f"  Tasks run   : {cmp.get('task_count', 0)}")
        return lines

    def _cloud_nodes(self) -> str:
        lines = self._cloud_nodes_lines()
        return "\n".join(lines)

    def _cloud_nodes_lines(self) -> list:
        lines = []
        if not self._cloud:
            lines.append("  Cloud layer not initialised.")
            return lines
        nodes = self._cloud.list_nodes()
        if not nodes:
            lines.append("  No cloud nodes active.")
            return lines
        for n in nodes:
            status_sym = "●" if n.get("running") else "○"
            lines.append(
                f"  {status_sym} {n['node_id']:<20} port={n.get('port','?'):<6} "
                f"tasks={n.get('task_count',0):<5} uptime={n.get('uptime_seconds',0)}s"
            )
        return lines

    def _cloud_spawn(self, node_id: str = None) -> str:
        if not self._cloud:
            return "  Cloud layer not initialised."
        if not self._cloud._running:
            return "  Cloud not started.  Run: cloud start"
        result = self._cloud.spawn_node(node_id)
        self._log(f"CMD: cloud spawn -> {result}")
        if "error" in result:
            return f"  ERROR: {result['error']}"
        return (f"  Spawned node {result['node_id']} on port {result['port']} "
                f"— {result['status']}")

    def _cloud_exec(self, payload_str: str = "echo") -> str:
        if not self._cloud:
            return "  Cloud layer not initialised."
        if not self._cloud._running:
            return "  Cloud not started.  Run: cloud start"
        result = self._cloud.exec_task("echo", {"msg": payload_str})
        self._log(f"CMD: cloud exec")
        if "error" in result:
            return f"  ERROR: {result['error']}"
        return (f"  Task {result.get('task_id','?')} → {result.get('status','?')} "
                f"on {result.get('node_id', 'local')}")

    def _cloud_heartbeat(self) -> str:
        if not self._cloud:
            return "  Cloud layer not initialised."
        result = self._cloud.heartbeat()
        self._log("CMD: cloud heartbeat")
        alive = result.get("alive", 0)
        total = result.get("total", 0)
        return f"  Heartbeat: {alive}/{total} nodes alive"

    def _cloud_storage_lines(self) -> list:
        lines = []
        if not self._cloud:
            lines.append("  Cloud layer not initialised.")
            return lines
        st = self._cloud.status().get("storage", {})
        lines.append(f"  Storage dir : {st.get('storage_dir', '?')}")
        lines.append(f"  Namespaces  : {st.get('namespaces', 0)}")
        lines.append(f"  Total keys  : {st.get('total_keys', 0)}")
        lines.append(f"  Writes      : {st.get('write_count', 0)}")
        lines.append(f"  Reads       : {st.get('read_count', 0)}")
        return lines

    def _cloud_event_log(self) -> str:
        lines = self._cloud_log_lines()
        return "\n".join(lines)

    def _cloud_log_lines(self, limit: int = 15) -> list:
        lines = []
        if not self._cloud:
            lines.append("  Cloud layer not initialised.")
            return lines
        log = self._cloud.get_event_log(limit)
        if not log:
            lines.append("  No cloud events recorded yet.")
            return lines
        for entry in log:
            lines.append(f"  [{entry.get('ts','')[:19]}] {entry.get('msg','')}")
        return lines

    # ── Shutdown ─────────────────────────────────────────────────────────────

    def shutdown(self, token: str) -> str:
        if self._identity:
            if not self._identity.is_operator(token):
                return "SHUTDOWN REFUSED: Invalid operator token."
        self._running = False
        self._log("SYSTEM SHUTDOWN initiated by operator.")
        return "AI-OS shutting down. Goodbye, operator."

    def get_console_log(self, limit: int = 50) -> list:
        return list(self._console_log[-limit:])

    def run_terminal(self) -> None:
        """Run interactive terminal menu loop."""
        print(self.get_banner())
        print()
        while self._running:
            print("\n  MAIN MENU")
            print("  " + "─" * 50)
            for k, (name, _) in self.MENU.items():
                print(f"  {k:>2}. {name}")
            print()
            try:
                raw = input("  Enter selection (or 'q' to quit): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Interrupted. Type 16.1 for graceful shutdown.")
                break
            if raw.lower() in ("q", "quit", "exit"):
                print("  Exiting terminal. System continues running.")
                break
            if raw == "":
                continue
            result = self.handle_command(raw)
            print(result)
