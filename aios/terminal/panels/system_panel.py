"""AI-OS Terminal Panels - System status panel."""
import time
from datetime import datetime, timezone


class SystemPanel:
    def __init__(self, command_center=None):
        self._cc = command_center

    def render(self, width: int = 60) -> list:
        lines = []
        lines.append("┌─ SYSTEM STATUS " + "─" * (width - 18) + "┐")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"│  Timestamp : {now:<{width-16}}│")

        if self._cc:
            status = self._cc.get_status_dict()
            uptime = status.get("uptime_seconds", 0)
            h, rem = divmod(int(uptime), 3600)
            m, s = divmod(rem, 60)
            uptime_str = f"{h:02d}:{m:02d}:{s:02d}"
            lines.append(f"│  Uptime    : {uptime_str:<{width-16}}│")
            lines.append(f"│  Operator  : {status.get('operator', 'Chris'):<{width-16}}│")
            lines.append(f"│  Version   : {status.get('version', '2.0.0-CC2'):<{width-16}}│")
        else:
            lines.append(f"│  Status    : {'ONLINE':<{width-16}}│")
            lines.append(f"│  Operator  : {'Chris':<{width-16}}│")

        layers = [
            ("L1 Physical Abstraction", "ONLINE"),
            ("L2 Virtual Hardware",     "ONLINE"),
            ("L3 Kernel Bridge",        "ONLINE"),
            ("L4 Process & Memory",     "ONLINE"),
            ("L5 Engine & Intelligence","ONLINE"),
            ("L6 Command & Interface",  "ONLINE"),
            ("L7 Application & Output", "ONLINE"),
        ]
        lines.append(f"│  {'─'*50}  │"[:width + 1])
        for name, state in layers:
            indicator = "✓" if state == "ONLINE" else "✗"
            lines.append(f"│  {indicator} {name:<35} {state:<8}│")

        lines.append("└" + "─" * (width - 1) + "┘")
        return lines

    def render_text(self, width: int = 60) -> str:
        return "\n".join(self.render(width))
