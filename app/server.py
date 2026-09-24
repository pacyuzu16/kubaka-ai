"""KUBAKA AI demo server.

Standard library only — no extra dependencies. Serves the static
front-end and exposes one JSON endpoint.

    python -m app.server            # http://localhost:8000
    python -m app.server --port 9000
"""
import argparse
import json
import sys
import threading
import traceback
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
sys.path.insert(0, str(ROOT.parent))

from src.pipeline import triage          # noqa: E402
from src.llm import health, which_backend  # noqa: E402

_lock = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(STATIC), **kw)

    def log_message(self, fmt, *args):
        if "/api/" in (self.path or ""):
            sys.stderr.write(f"  {self.command} {self.path}\n")

    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            ok, msg = health()
            return self._json({"ok": ok, "detail": msg, "backend": which_backend()})
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/triage":
            return self._json({"error": "not found"}, 404)
        try:
            length = int(self.headers.get("Content-Length") or 0)
            message = json.loads(self.rfile.read(length) or b"{}").get("message", "").strip()
        except Exception:
            return self._json({"error": "bad request"}, 400)
        if not message:
            return self._json({"error": "empty message"}, 400)
        try:
            # The CLI backend spawns a process per call; serialise to keep
            # a demo click from queueing three of them at once.
            with _lock:
                result = triage(message)
            return self._json(result.to_ticket())
        except Exception as exc:
            traceback.print_exc()
            return self._json({"error": str(exc)}, 500)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"KUBAKA AI demo  ->  http://localhost:{args.port}")
    print(f"backend: {which_backend()}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
