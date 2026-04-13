"""AI-OS Web Server - HTTP server on port 1313 serving web UI."""
import json
import os
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class AIWebHandler(SimpleHTTPRequestHandler):
    _command_center = None
    _web_dir = None

    def log_message(self, format, *args):
        pass  # Suppress default HTTP logging

    def do_GET(self):
        if self.path == "/api/status" or self.path == "/api/status/":
            self._serve_status()
        elif self.path == "/api/heartbeat":
            self._serve_heartbeat()
        else:
            # Serve static files from web directory
            if self._web_dir:
                os.chdir(self._web_dir)
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/command" or self.path == "/api/command/":
            self._handle_command()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_command(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(body.decode("utf-8"))
            cmd = str(payload.get("cmd", "")).strip()
            if not cmd:
                result_text = "No command provided. Enter a menu number like 1, 1.1, or 11.1"
            elif self._command_center:
                result_text = self._command_center.handle_command(cmd)
            else:
                result_text = f"Command received: {cmd} (CommandCenter not attached)"
            resp = json.dumps({"result": result_text, "cmd": cmd}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp)
        except Exception as exc:
            error = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error)))
            self.end_headers()
            self.wfile.write(error)

    def do_OPTIONS(self):
        # Allow CORS preflight for the POST endpoint
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _serve_status(self):
        try:
            if self._command_center:
                data = self._command_center.get_status_dict()
            else:
                data = {
                    "status": "ONLINE",
                    "version": "2.0.0-CC2",
                    "operator": "Chris",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "layers": {str(i): "ONLINE" for i in range(1, 8)},
                }
            body = json.dumps(data, default=str).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            error = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error)))
            self.end_headers()
            self.wfile.write(error)

    def _serve_heartbeat(self):
        data = {
            "alive": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if self._command_center and self._command_center._heartbeat:
            data.update(self._command_center._heartbeat.last_beat())
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def translate_path(self, path):
        if self._web_dir:
            path = path.split("?")[0].split("#")[0]
            path = path.lstrip("/")
            if not path:
                path = "index.html"
            return str(Path(self._web_dir) / path)
        return super().translate_path(path)


class _ReusingHTTPServer(HTTPServer):
    allow_reuse_address = True


class AIWebServer:
    PORT = 1313

    def __init__(self, command_center=None):
        self._cc = command_center
        self._server = None
        self._thread = None
        self._running = False
        self._web_dir = str(Path(__file__).parent)

    def start(self) -> None:
        AIWebHandler._command_center = self._cc
        AIWebHandler._web_dir = self._web_dir

        self._server = _ReusingHTTPServer(("0.0.0.0", self.PORT), AIWebHandler)
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while self._running:
            try:
                self._server.handle_request()
            except Exception:
                pass

    def stop(self) -> None:
        self._running = False
        if self._server:
            self._server.shutdown()

    def status(self) -> dict:
        return {
            "component": "AIWebServer",
            "port": self.PORT,
            "running": self._running,
            "url": f"http://localhost:{self.PORT}",
            "web_dir": self._web_dir,
            "healthy": self._running,
        }
