"""AI-OS Web Server - HTTP server on port 1313 serving web UI."""
import json
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class AIWebHandler(SimpleHTTPRequestHandler):
    _command_center = None
    _web_dir = None
    _operator_token = None  # SHA-256 hex; None = auth disabled

    def log_message(self, format, *args):
        pass  # Suppress default HTTP logging

    # ── Token verification ──────────────────────────────────────────────────

    def _get_request_token(self) -> str:
        """Extract token from Authorization header or ?token= query param."""
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:].strip()
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        tokens = params.get("token", [])
        return tokens[0] if tokens else ""

    def _verify_token(self) -> bool:
        """Return True if the request carries a valid operator token."""
        expected = self.__class__._operator_token
        if expected is None:
            return True  # auth not configured — allow all
        return self._get_request_token() == expected

    def _serve_401(self):
        body = json.dumps({"error": "Unauthorized — operator token required"}).encode("utf-8")
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("WWW-Authenticate", 'Bearer realm="AI-OS"')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    # ── HTTP verbs ──────────────────────────────────────────────────────────

    def do_GET(self):
        clean = self.path.split("?")[0].rstrip("/")
        if clean == "/api/status":
            if not self._verify_token():
                self._serve_401()
                return
            self._serve_status()
        elif clean == "/api/heartbeat":
            if not self._verify_token():
                self._serve_401()
                return
            self._serve_heartbeat()
        elif clean == "/api/login":
            self._serve_login()  # no auth required — this IS the auth step
        elif clean == "/api/stream":
            if not self._verify_token():
                self._serve_401()
                return
            self._serve_sse()
        else:
            # Serve static files — translate_path() handles path resolution
            super().do_GET()

    def do_POST(self):
        clean = self.path.split("?")[0].rstrip("/")
        if clean == "/api/command":
            if not self._verify_token():
                self._serve_401()
                return
            self._handle_command()
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    # ── Route handlers ──────────────────────────────────────────────────────

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

    def _serve_login(self):
        """GET /api/login?token=<hex> — validate token; no prior auth required."""
        expected = self.__class__._operator_token
        provided = self._get_request_token()
        if expected is None or provided == expected:
            ok = True
            msg = "Authentication successful"
        else:
            ok = False
            msg = "Invalid token"
        body = json.dumps({"ok": ok, "message": msg}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_sse(self):
        """GET /api/stream — Server-Sent Events; pushes status every second."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            while True:
                if self._command_center:
                    data = self._command_center.get_status_dict()
                else:
                    data = {
                        "status": "ONLINE",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                payload = json.dumps(data, default=str)
                self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                self.wfile.flush()
                time.sleep(1)
        except Exception:
            pass  # client disconnected

    def translate_path(self, path):
        if self._web_dir:
            path = path.split("?")[0].split("#")[0]
            path = path.lstrip("/")
            if not path:
                path = "index.html"
            return str(Path(self._web_dir) / path)
        return super().translate_path(path)


class _ReusingHTTPServer(ThreadingHTTPServer):
    """Thread-per-request HTTP server (required for concurrent SSE connections)."""
    allow_reuse_address = True


class AIWebServer:
    PORT = 1313

    def __init__(self, command_center=None):
        self._cc = command_center
        self._server = None
        self._thread = None
        self._running = False
        self._web_dir = str(Path(__file__).parent)

    def set_operator_token(self, token: str) -> None:
        """Set the operator token required to access /api/* endpoints."""
        AIWebHandler._operator_token = token

    def start(self) -> None:
        AIWebHandler._command_center = self._cc
        AIWebHandler._web_dir = self._web_dir

        # Auto-detect operator token from CommandCenter when not explicitly set
        if AIWebHandler._operator_token is None and self._cc is not None:
            try:
                identity = getattr(self._cc, "_identity", None)
                if identity is not None:
                    AIWebHandler._operator_token = identity.get_operator_token()
            except Exception:
                pass

        self._server = _ReusingHTTPServer(("0.0.0.0", self.PORT), AIWebHandler)
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        self._server.serve_forever()

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
            "auth_enabled": AIWebHandler._operator_token is not None,
            "healthy": self._running,
        }
