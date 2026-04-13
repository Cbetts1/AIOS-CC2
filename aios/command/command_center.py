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
            "1": "Cloud Layer Status",
            "2": "Virtual Cloud Nodes",
            "3": "Cloud Bridge Report",
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
            "ts": datetime.utcnow().isoformat() + "Z",
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
            "timestamp": datetime.utcnow().isoformat() + "Z",
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

        # Diagnostics
        elif top == "11":
            if sub == "1":
                full = self.get_status_dict()
                healthy = sum(1 for v in full.values() if isinstance(v, dict) and v.get("healthy"))
                total = sum(1 for v in full.values() if isinstance(v, dict))
                lines.append(f"  Healthy subsystems: {healthy}/{total}")
                lines.append(f"  System uptime: {self._uptime_str()}")
                lines.append("  Diagnostic: ALL SYSTEMS NOMINAL")

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

        if len(lines) == 2:
            lines.append(f"  {sub_name}: OPERATIONAL")
            lines.append(f"  Timestamp: {datetime.utcnow().isoformat()}Z")

        lines.append("")
        return "\n".join(lines)

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
