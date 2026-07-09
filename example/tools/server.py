#!/usr/bin/env python3
"""server.py — a small read-only HTTP server behind the live screening board.

It never touches data/ directly: every response is built from tools/repo.py, the same
data-access layer every other tool uses. So the board shows, by construction, the same
numbers every other surface renders — one definition of the pipeline, served fresh on
each request. The server holds no state and writes nothing; the files stay the ground
truth under it.

Routes
    GET /            → the screening board (views/screening_board.template.html, live)
    GET /api/board   → the canonical board projection (polled by the page)
    GET /health      → {ok: true}

Usage
    python tools/server.py [--host 127.0.0.1] [--port 8765]

Stdlib only — no framework, no build step, consistent with the rest of the workspace.
"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import repo

TEMPLATE = repo.ROOT / "views" / "screening_board.template.html"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet; the board polls frequently
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        try:
            if path == "/":
                html = (TEMPLATE.read_text(encoding="utf-8")
                        .replace("__DATA__", json.dumps(repo.board()))
                        .replace("__LIVE__", "true"))
                return self._send(200, html, "text/html; charset=utf-8")
            if path == "/api/board":
                return self._send(200, repo.board())
            if path == "/health":
                return self._send(200, {"ok": True})
            return self._send(404, {"error": f"no route for {path}"})
        except Exception as e:  # never leak a stack trace to the client
            return self._send(500, {"error": f"{type(e).__name__}: {e}"})


def main():
    ap = argparse.ArgumentParser(description="Live screening-board server.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"serving on http://{args.host}:{args.port}  (Ctrl-C to stop)")
    print(f"  open this ->  http://{args.host}:{args.port}/   (the board; updates as decisions land)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
