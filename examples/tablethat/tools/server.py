#!/usr/bin/env python3
"""server.py — the dashboard server. Part of the standard kit.

A small read-only HTTP server that makes the workspace visible while it works. It never
touches data/ directly: every response is answered fresh through tools/repo.py — the
same named queries every other surface renders — so the dashboard shows, by
construction, the same numbers as everything else. The server holds no state and writes
nothing; the files stay the ground truth under it.

Routes
    GET /               → the index: every view and published query the workspace has,
                          live — new ones appear on the page as they are grown
    GET /view/<name>    → views/<name>.template.html, bound to its query, served live
    GET /api/<name>     → the query published as <name> in repo.QUERIES, asked fresh
    GET /api/_index     → {workspace, views, queries} (the index page polls this)
    GET /health         → {ok: true}

Parameters (grown here for tablethat): URL query-string values are passed to the
query as keyword arguments, on /api/<name> and when binding /view/<name> alike —
/api/table?table_id=T-001 answers repo.QUERIES["table"](table_id="T-001"). Values
arrive as strings; a query that takes no parameters is unaffected. A live page that
depends on its parameters polls its api with its own location.search.

Template binding — the whole wiring convention: a template named <name>.template.html
gets __DATA__ replaced by repo.QUERIES[<name>]() when a query of that name is published
(else null), and __LIVE__ replaced by true. Grow a view by growing exactly two things:
a query in repo.py and a template in views/. The server needs no changes.

Liveness is polling, on purpose: pages re-ask their query every couple of seconds and
repaint on change. Queries recompute from the record on every ask, so change detection
is free at read time; pushing would make it a duty of every writer instead.

Usage
    python tools/server.py [--host 127.0.0.1] [--port 8765]

Stdlib only — no framework, no build step.
"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import repo


def view_names():
    if not repo.VIEWS.exists():
        return []
    return sorted(p.name[:-len(".template.html")]
                  for p in repo.VIEWS.glob("*.template.html")
                  if p.name != "index.template.html")


def index_payload():
    return {"workspace": repo.ROOT.name,
            "views": view_names(),
            "queries": sorted(repo.QUERIES)}


def render(name, params=None):
    """Bind views/<name>.template.html to its query and return the page."""
    template = (repo.VIEWS / f"{name}.template.html").read_text(encoding="utf-8")
    if name == "index":
        data = index_payload()
    else:
        query = repo.QUERIES.get(name)
        data = query(**(params or {})) if query else None
    return (template.replace("__DATA__", json.dumps(data))
                    .replace("__LIVE__", "true"))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet; live pages poll frequently
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)) or body is None:
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
        url = urlparse(self.path)
        path = url.path.rstrip("/") or "/"
        parts = [p for p in path.split("/") if p]
        # query-string → keyword arguments for the named query (last value wins)
        params = {k: v[-1] for k, v in parse_qs(url.query).items()}
        try:
            if path == "/":
                return self._send(200, render("index"), "text/html; charset=utf-8")
            if path == "/health":
                return self._send(200, {"ok": True})
            if parts[0] == "view" and len(parts) == 2:
                name = parts[1]
                if name == "index" or not (repo.VIEWS / f"{name}.template.html").exists():
                    return self._send(404, {"error": f"no view '{name}'"})
                return self._send(200, render(name, params), "text/html; charset=utf-8")
            if parts[0] == "api" and len(parts) == 2:
                name = parts[1]
                if name == "_index":
                    return self._send(200, index_payload())
                query = repo.QUERIES.get(name)
                if query is None:
                    return self._send(404, {"error": f"no query '{name}'"})
                try:
                    return self._send(200, query(**params))
                except TypeError as e:  # a parameter the query doesn't take
                    return self._send(400, {"error": f"bad parameters: {e}"})
            return self._send(404, {"error": f"no route for {path}"})
        except Exception as e:  # never leak a stack trace to the client
            return self._send(500, {"error": f"{type(e).__name__}: {e}"})


def main():
    ap = argparse.ArgumentParser(description="The workspace dashboard server.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"serving on http://{args.host}:{args.port}  (Ctrl-C to stop)")
    print(f"  open this ->  http://{args.host}:{args.port}/   "
          "(the workspace; views appear here as they are grown)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
