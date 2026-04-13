"""AI-OS APK UI Blueprint - Operator and Chat mode layouts."""
import time
from datetime import datetime


class APKUIMain:
    MODE_OPERATOR = "operator"
    MODE_CHAT = "chat"

    def __init__(self, command_center=None):
        self._cc = command_center
        self._mode = self.MODE_OPERATOR
        self._gesture_log = []
        self._init_time = time.time()

    def operator_mode(self) -> dict:
        self._mode = self.MODE_OPERATOR
        layout = {
            "mode": "operator",
            "layout": {
                "top_bar": {
                    "title": "AI-OS Command Center",
                    "status_indicator": "ONLINE",
                    "clock": datetime.utcnow().isoformat() + "Z",
                },
                "left_panel": {
                    "type": "slide-in",
                    "content": "main_menu",
                    "trigger": "swipe_right",
                },
                "main_content": {
                    "type": "dashboard",
                    "widgets": ["system_status", "layer_health", "sensor_readings",
                                "heartbeat", "engine_status", "network_status"],
                },
                "bottom_bar": {
                    "buttons": ["Status", "Engines", "Network", "Security", "Chat"],
                },
            },
            "gesture_map": {
                "swipe_left": "open_dashboard",
                "swipe_right": "open_menu",
                "long_press": "activate_root_mode",
                "double_tap": "refresh_status",
            },
        }
        return layout

    def chat_mode(self) -> dict:
        self._mode = self.MODE_CHAT
        layout = {
            "mode": "chat",
            "layout": {
                "chat_stream": {
                    "type": "scrollable_messages",
                    "auto_scroll": True,
                    "ai_name": "Au-Ra",
                    "user_name": "Operator",
                },
                "input_bar": {
                    "type": "text_input",
                    "placeholder": "Message Au-Ra...",
                    "send_button": True,
                    "voice_button": False,
                },
                "top_bar": {
                    "title": "Chat — Au-Ra",
                    "back_button": True,
                },
            },
        }
        return layout

    def handle_gesture(self, gesture: str) -> dict:
        result = {
            "gesture": gesture,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": "none",
        }
        gesture_actions = {
            "swipe_left": "open_dashboard",
            "swipe_right": "open_menu",
            "long_press": "activate_root_mode",
            "double_tap": "refresh_status",
            "pinch": "zoom_out",
            "spread": "zoom_in",
        }
        action = gesture_actions.get(gesture, "none")
        result["action"] = action
        self._gesture_log.append(result)
        if len(self._gesture_log) > 100:
            self._gesture_log = self._gesture_log[-50:]
        return result

    def current_mode(self) -> str:
        return self._mode

    def status(self) -> dict:
        return {
            "component": "APKUIMain",
            "mode": self._mode,
            "gesture_count": len(self._gesture_log),
            "uptime_seconds": round(time.time() - self._init_time, 1),
        }
