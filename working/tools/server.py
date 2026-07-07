#!/usr/bin/env python
"""server.py — a small read-only HTTP server behind the live pipeline dashboard.

It never touches the data directories directly: every response is built from
`tools/repo.py`, the same data-access layer the offline views use. So the numbers
on the live dashboard are, by construction, the same projection the PRISMA view and
the HTML report render — there is one definition of the pipeline, and this just
serves it over HTTP, read fresh on each request.

Routes
    GET /                                  → index: the reviews, linking to dashboards
    GET /dashboard/<slug>                  → the live dashboard page (views/dashboard.template.html)
    GET /api/reviews                       → [{slug, title, totals}]  (list)
    GET /api/reviews/<slug>                → {protocol, records}      (full review)
    GET /api/reviews/<slug>/pipeline       → the canonical funnel projection (polled live)
    GET /health                            → {ok: true}

Usage
    python tools/server.py [--host 127.0.0.1] [--port 8765]

Stdlib only — no framework, no build step, consistent with the rest of the workspace.
"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import build_report
import repo

TEMPLATE = repo.ROOT / "views" / "dashboard.template.html"


def _reviews_index():
    out = []
    for slug in repo.list_reviews():
        if not repo.has_protocol(slug):
            continue
        p = repo.pipeline(slug)
        out.append({"slug": slug, "title": p["title"], "question": p["question"],
                    "totals": p["totals"]})
    return out


def _render_index():
    rows = "".join(
        f'<li><a href="/dashboard/{r["slug"]}">{r["title"]}</a>'
        f' <span class="muted">— {r["totals"]["included"]} included / '
        f'{r["totals"]["unique"]} records</span></li>'
        for r in _reviews_index()
    ) or '<li class="muted">No reviews yet.</li>'
    return (
        '<!doctype html><meta charset="utf-8"><title>Living Review — dashboards</title>'
        '<style>body{font:15px/1.6 system-ui,sans-serif;max-width:640px;margin:60px auto;'
        'padding:0 20px;color:#1b2529}a{color:#214b5b}.muted{color:#7f8b90}'
        'h1{font-size:20px}li{margin:8px 0}</style>'
        '<h1>Live review dashboards</h1><ul>' + rows + '</ul>'
    )


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet; the dashboard polls frequently
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _err(self, code, msg):
        self._send(code, {"error": msg})

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        parts = [p for p in path.split("/") if p]
        try:
            if path == "/":
                return self._send(200, _render_index(), "text/html; charset=utf-8")
            if path == "/health":
                return self._send(200, {"ok": True})

            if parts[0] == "dashboard" and len(parts) == 2:
                slug = parts[1]
                if not repo.has_protocol(slug):
                    return self._err(404, f"no review '{slug}'")
                html = TEMPLATE.read_text(encoding="utf-8")
                return self._send(200, html, "text/html; charset=utf-8")

            # export: regenerate the static report from the data-access layer and serve it
            if parts[0] == "report" and len(parts) == 2:
                slug = parts[1]
                if not repo.has_protocol(slug):
                    return self._err(404, f"no review '{slug}'")
                build_report.write(slug)                 # refresh the on-disk snapshot too
                html = build_report.render(slug)
                return self._send(200, html, "text/html; charset=utf-8")

            if parts[0] == "api" and len(parts) >= 2 and parts[1] == "reviews":
                if len(parts) == 2:
                    return self._send(200, _reviews_index())
                slug = parts[2]
                if not repo.has_protocol(slug):
                    return self._err(404, f"no review '{slug}'")
                if len(parts) == 3:
                    return self._send(200, repo.load_review(slug))
                if len(parts) == 4 and parts[3] == "pipeline":
                    return self._send(200, repo.pipeline(slug))
                return self._err(404, "unknown review sub-resource")

            return self._err(404, f"no route for {path}")
        except Exception as e:  # never leak a stack trace to the client
            return self._err(500, f"{type(e).__name__}: {e}")


def main():
    ap = argparse.ArgumentParser(description="Live pipeline dashboard server.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"serving on http://{args.host}:{args.port}  (Ctrl-C to stop)")
    print(f"  index      http://{args.host}:{args.port}/")
    for slug in repo.list_reviews():
        print(f"  dashboard  http://{args.host}:{args.port}/dashboard/{slug}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
