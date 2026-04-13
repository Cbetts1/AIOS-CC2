"""AI-OS APK Operator Panel - Dashboard for operator mode."""
import time
from datetime import datetime, timezone


class OperatorPanel:
    def __init__(self, command_center=None):
        self._cc = command_center
        self._init_time = time.time()
        self._panel_open = False

    def open(self) -> dict:
        self._panel_open = True
        return {
            "action": "open",
            "panel": "operator",
            "animation": "slide_in_left",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def close(self) -> dict:
        self._panel_open = False
        return {
            "action": "close",
            "panel": "operator",
            "animation": "slide_out_left",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_menu(self) -> list:
        return [
            {"id": 1,  "label": "System Status",      "icon": "●"},
            {"id": 2,  "label": "Layer Control",       "icon": "≡"},
            {"id": 3,  "label": "Engine Control",      "icon": "⚙"},
            {"id": 4,  "label": "Virtual Hardware",    "icon": "□"},
            {"id": 5,  "label": "Network",             "icon": "⟳"},
            {"id": 6,  "label": "Security",            "icon": "🔒"},
            {"id": 7,  "label": "Diagnostics",         "icon": "✦"},
            {"id": 8,  "label": "Legal & Compliance",  "icon": "§"},
            {"id": 9,  "label": "Documentation",       "icon": "≈"},
            {"id": 10, "label": "Shutdown",            "icon": "✖"},
        ]

    def get_dashboard_widgets(self) -> list:
        data = {}
        if self._cc:
            try:
                data = self._cc.get_status_dict()
            except Exception:
                pass
        widgets = [
            {
                "id": "uptime",
                "label": "Uptime",
                "value": data.get("uptime_seconds", 0),
                "type": "numeric",
            },
            {
                "id": "operator",
                "label": "Operator",
                "value": data.get("operator", "Chris"),
                "type": "text",
            },
            {
                "id": "heartbeat",
                "label": "Heartbeat",
                "value": "ALIVE",
                "type": "indicator",
                "color": "cyan",
            },
            {
                "id": "layers",
                "label": "Layer Health",
                "value": "7/7 ONLINE",
                "type": "health",
                "color": "green",
            },
        ]
        return widgets

    def status(self) -> dict:
        return {
            "component": "OperatorPanel",
            "panel_open": self._panel_open,
            "uptime_seconds": round(time.time() - self._init_time, 1),
        }
