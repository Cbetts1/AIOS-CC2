"""AI-OS Web Server - HTTP server on port 1313 serving web UI.

Authentication
--------------
Mutating / sensitive endpoints require the admin password supplied in the
request.  Pass it in one of two ways (either is accepted):

  • HTTP header:   X-Admin-Password: 7212
  • JSON body key: {"password": "7212", "cmd": "..."}   (POST /api/command)
  • Query param:   ?password=7212                        (GET  /api/debug)

Protected endpoints:  POST /api/command,  GET /api/debug
Open endpoints:       GET /api/status, GET /api/heartbeat,
                      GET /api/health,  GET /api/proc
"""
import json
import os
import socket
import threading
import time
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

_ADMIN_PASSWORD = "7212"

# Default port — override with the AIOS_PORT environment variable or --port flag.
_DEFAULT_PORT = int(os.environ.get("AIOS_PORT", 1313))


def _is_port_available(host: str, port: int) -> bool:
    """Return True if *port* on *host* is free to bind right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
            return True
        except OSError:
            return False


class AIWebHandler(SimpleHTTPRequestHandler):
    _command_center = None
    _web_dir = None
    _start_time = time.time()

    def log_message(self, format, *args):
        pass  # Suppress default HTTP logging

    # ── Auth helper ──────────────────────────────────────────────────────────

    def _check_password(self, payload: dict = None, query: dict = None) -> bool:
        """Return True if the request carries the correct admin password."""
        # 1. Header check (works for GET and POST)
        if self.headers.get("X-Admin-Password") == _ADMIN_PASSWORD:
            return True
        # 2. JSON body key (POST)
        if payload and str(payload.get("password", "")) == _ADMIN_PASSWORD:
            return True
        # 3. Query param (GET)
        if query and query.get("password", [""])[0] == _ADMIN_PASSWORD:
            return True
        return False

    def _send_forbidden(self):
        body = json.dumps({"error": "Forbidden: admin password required."}).encode()
        self.send_response(403)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    # ── Routing ──────────────────────────────────────────────────────────────

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        if path == "/api/status":
            self._serve_status()
        elif path == "/api/heartbeat":
            self._serve_heartbeat()
        elif path == "/api/health":
            self._serve_health()
        elif path == "/api/debug":
            if not self._check_password(query=query):
                self._send_forbidden()
            else:
                self._serve_debug()
        elif path == "/api/proc":
            self._serve_proc()
        else:
            # Serve static files — translate_path() handles _web_dir, no os.chdir() needed
            super().do_GET()

    def do_POST(self):
        if self.path.rstrip("/") == "/api/command":
            self._handle_command()
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, X-Admin-Password")
        self.end_headers()

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _handle_command(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(body.decode("utf-8"))

            if not self._check_password(payload=payload):
                self._send_forbidden()
                return

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

    def _serve_health(self):
        """Readiness / liveness probe — always open, no auth required."""
        cc = self._command_center
        uptime = round(time.time() - self._start_time, 1)
        data = {
            "status": "OK",
            "version": "2.0.0-CC2",
            "uptime_seconds": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "running": bool(cc and cc._running),
        }
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_debug(self):
        """Full StateRegistry dump — requires admin password."""
        try:
            data: dict = {}
            if self._command_center and self._command_center._state:
                data = self._command_center._state.dump()
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

    def _serve_proc(self):
        """List and read virtual /proc/aios/ files — open, no auth required."""
        try:
            data: dict = {"proc_files": []}
            cc = self._command_center
            if cc and cc._proc_writers:
                names = cc._proc_writers.list_procs()
                data["proc_files"] = names
                data["entries"] = {
                    n: cc._proc_writers.read_proc(n) for n in names
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
    PORT = _DEFAULT_PORT

    def __init__(self, command_center=None):
        self._cc = command_center
        self._server = None
        self._thread = None
        self._running = False
        self._bound = False
        self._web_dir = str(Path(__file__).parent)

    def start(self) -> None:
        """Bind the HTTP server and start serving in a background thread.

        Raises ``OSError`` if the port is already in use so callers can
        report a clear error and fall back gracefully.
        """
        AIWebHandler._command_center = self._cc
        AIWebHandler._web_dir = self._web_dir
        AIWebHandler._start_time = time.time()

        if not _is_port_available("0.0.0.0", self.PORT):
            raise OSError(
                f"[Errno 98] Address already in use — port {self.PORT} is taken. "
                f"Stop the process using that port or set a different port with "
                f"--port or the AIOS_PORT environment variable."
            )

        self._server = _ReusingHTTPServer(("0.0.0.0", self.PORT), AIWebHandler)
        self._bound = True
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
        """Stop the server and release the bound port."""
        self._running = False
        if self._server:
            try:
                self._server.server_close()
            except Exception:
                pass
            self._server = None
        self._bound = False

    def is_bound(self) -> bool:
        """Return True if the server successfully bound to its port."""
        return self._bound

    def status(self) -> dict:
        return {
            "component": "AIWebServer",
            "port": self.PORT,
            "running": self._running,
            "bound": self._bound,
            "url": f"http://localhost:{self.PORT}",
            "web_dir": self._web_dir,
            "healthy": self._bound and self._running,
        }
