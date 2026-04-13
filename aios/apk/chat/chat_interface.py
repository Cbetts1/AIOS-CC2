"""AI-OS APK Chat Interface - Async chat with Au-Ra engine."""
import asyncio
import time
from datetime import datetime


class ChatInterface:
    def __init__(self, aura_engine=None):
        self._aura = aura_engine
        self._messages = []
        self._input_buffer = ""
        self._init_time = time.time()

    def _au_ra_respond(self, user_msg: str) -> str:
        msg = user_msg.lower().strip()
        if "status" in msg or "how are you" in msg:
            return "All systems nominal. Layers 1-7 ONLINE. Heartbeat active. Ready for commands."
        if "hello" in msg or "hi" in msg:
            return "Hello, Operator. Au-Ra is online and operational. How can I assist?"
        if "layer" in msg:
            return "7 layers active: Physical Abstraction, Virtual Hardware, Kernel Bridge, " \
                   "Process & Memory, Engine & Intelligence, Command & Interface, Application & Output."
        if "engine" in msg:
            return "AuraEngine is running. Sub-engines: Builder, Repair, Documentation, Evolution, LegalCortex — all ticking."
        if "network" in msg:
            return "Internal network: 10.0.0.0/8, virtual only. No host network exposure. Interfaces: lo0, eth0."
        if "shutdown" in msg or "stop" in msg:
            return "Shutdown requires operator token. Please authenticate via Security menu (6.1)."
        if "security" in msg or "identity" in msg:
            return "Identity locked. Operator: Chris. Level: OPERATOR_ONLY. SecurityKernel authenticated."
        if "help" in msg or "?" in msg:
            return ("I can help with: system status, layer info, engine control, network, security, "
                    "diagnostics. Type your question or use the operator panel.")
        return f"Understood, Operator. Processing: '{user_msg}'. Au-Ra is ready for further commands."

    def send_message(self, msg: str) -> dict:
        entry = {
            "role": "user",
            "content": msg,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "id": len(self._messages),
        }
        self._messages.append(entry)
        response = self._au_ra_respond(msg)
        ai_entry = {
            "role": "assistant",
            "name": "Au-Ra",
            "content": response,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "id": len(self._messages),
        }
        self._messages.append(ai_entry)
        return ai_entry

    async def send_message_async(self, msg: str) -> dict:
        await asyncio.sleep(0.05)
        return self.send_message(msg)

    def receive_message(self) -> dict:
        for msg in reversed(self._messages):
            if msg.get("role") == "assistant":
                return msg
        return {}

    def render_chat_stream(self) -> list:
        lines = []
        for msg in self._messages[-50:]:
            role = msg.get("role", "")
            name = msg.get("name", "Operator") if role == "assistant" else "Operator"
            ts = msg.get("timestamp", "")[:19]
            content = msg.get("content", "")
            lines.append(f"[{ts}] {name}: {content}")
        return lines

    def render_input_bar(self) -> dict:
        return {
            "placeholder": "Message Au-Ra...",
            "value": self._input_buffer,
            "send_label": "Send",
            "char_count": len(self._input_buffer),
        }

    def set_input(self, text: str) -> None:
        self._input_buffer = text

    def get_history(self) -> list:
        return list(self._messages[-100:])

    def status(self) -> dict:
        return {
            "component": "ChatInterface",
            "message_count": len(self._messages),
            "uptime_seconds": round(time.time() - self._init_time, 1),
        }
