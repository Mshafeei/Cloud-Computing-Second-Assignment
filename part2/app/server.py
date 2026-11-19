"""HTTP API for the lab queue.

Bodies are plain text, not JSON:
  GET  /health                  200  ok
  POST /join   {"name": "..."}  200  ticket number, or 400 if the name is rejected
  POST /next                    200  name, or 404 empty

Listen on PORT (default 8000). The queue file is DATA_DIR/queue.txt
(DATA_DIR defaults to /data). main() must bind 0.0.0.0 so the published
port is reachable. serve() must use the host it is given.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.queue import join, take

def make_handler(queue_path: Path) -> type[BaseHTTPRequestHandler]:
    class QueueHandler(BaseHTTPRequestHandler):
        def _send_text(self, status: int, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            route = self.path.split("?", 1)[0]
            if route == "/health":
                self._send_text(200, "ok")
                return
            self._send_text(404, "not found")

        def do_POST(self) -> None:
            route = self.path.split("?", 1)[0]

            if route == "/join":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self._send_text(400, "invalid content-length")
                    return

                raw = self.rfile.read(length) if length > 0 else b""
                try:
                    data = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._send_text(400, "invalid json")
                    return

                if not isinstance(data, dict) or not isinstance(data.get("name"), str):
                    self._send_text(400, "invalid name")
                    return

                try:
                    ticket = join(queue_path, data["name"])
                except ValueError:
                    self._send_text(400, "invalid name")
                    return

                self._send_text(200, str(ticket))
                return

            if route == "/next":
                try:
                    name = take(queue_path)
                except LookupError:
                    self._send_text(404, "empty")
                    return

                self._send_text(200, name)
                return

            self._send_text(404, "not found")

    return QueueHandler


def serve(host: str, port: int, data_dir: str) -> None:
    """Listen until the process is stopped. Use join and take from app.queue."""
    queue_path = Path(data_dir) / "queue.txt"
    handler_cls = make_handler(queue_path)
    with ThreadingHTTPServer((host, port), handler_cls) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    data_dir = os.environ.get("DATA_DIR", "/data")
    serve("0.0.0.0", port, data_dir)


if __name__ == "__main__":
    main()
