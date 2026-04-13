"""AI-OS Terminal Panels - Network status panel."""
from datetime import datetime


class NetworkPanel:
    def __init__(self, vnetwork=None, mesh=None, heartbeat=None):
        self._vnet = vnetwork
        self._mesh = mesh
        self._hb = heartbeat

    def render(self, width: int = 60) -> list:
        lines = []
        lines.append("┌─ NETWORK STATUS " + "─" * (width - 19) + "┐")
        lines.append(f"│  Internal Network : {'10.0.0.0/8':<{width-22}}│")
        lines.append(f"│  Host Exposure    : {'NONE - VIRTUAL ONLY':<{width-22}}│")

        if self._vnet:
            st = self._vnet.status()
            lines.append(f"│  Interfaces       : {st.get('interfaces', 0):<{width-22}}│")
            lines.append(f"│  Packets Sent     : {st.get('packets_sent', 0):<{width-22}}│")
            lines.append(f"│  Packets Received : {st.get('packets_received', 0):<{width-22}}│")
            for iface in st.get("interface_list", []):
                label = f"  [{iface['name']}] {iface['ip']} rx={iface['rx']} tx={iface['tx']}"
                lines.append(f"│{label:<{width-1}}│")

        if self._mesh:
            ms = self._mesh.status()
            lines.append(f"│  Mesh Nodes       : {ms.get('node_count', 0):<{width-22}}│")
            lines.append(f"│  Broadcasts       : {ms.get('messages_broadcast', 0):<{width-22}}│")

        if self._hb:
            hbs = self._hb.status()
            indicator = "● ALIVE" if hbs.get("running") else "○ STOPPED"
            lines.append(f"│  Heartbeat        : {indicator:<{width-22}}│")
            lines.append(f"│  Beat Count       : {hbs.get('beat_count', 0):<{width-22}}│")
            lines.append(f"│  Last Beat        : {str(hbs.get('last_beat_ts', 'N/A')):<{width-22}}│")

        lines.append("└" + "─" * (width - 1) + "┘")
        return lines

    def render_text(self, width: int = 60) -> str:
        return "\n".join(self.render(width))
