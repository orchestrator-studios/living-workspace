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

Template binding — the whole wiring convention: a template named <name>.template.html
gets __DATA__ replaced by repo.QUERIES[<name>]() when a query of that name is published
(else null), and __LIVE__ replaced by true. Grow a view by growing exactly two things:
a query in repo.py and a template in views/. The server needs no changes.

Parameters — some questions are only well-posed about one thing: not "every table" but
"table T-001". So a named query may take keyword arguments, and the URL's query string
supplies them, identically on both surfaces:

    /api/table?table_id=T-001      → repo.QUERIES["table"](table_id="T-001")
    /view/table?table_id=T-001     → the same answer, bound into the template

Values arrive as strings — a query wanting an int coerces its own. A query taking no
parameters is unaffected, and an unknown parameter is a 400, not a silent ignore. Two
obligations follow for whoever grows one. A parameterized query gives every parameter a
default and answers helpfully when asked bare (`/api/table` should say which tables
exist, not raise) — the index page links every published query without arguments. And a
live page whose identity includes its query string must poll with it:
`fetch("/api/table" + location.search)`, not a bare path, or it will repaint itself with
another thing's data.

Liveness is polling, on purpose: pages re-ask their query every couple of seconds and
repaint on change. Queries recompute from the record on every ask, so change detection
is free at read time; pushing would make it a duty of every writer instead.

Freshness of code, not just data: the server re-imports the query layer whenever
repo.py or a schema changes on disk, so a long-lived process serves the workspace's
*current* definition — a query grown after the server started appears without a
restart. (The same staleness rule the views obey, applied to the registry itself.)
/health names the workspace and its queries, so a stale or foreign process is
diagnosable at a glance.

Usage
    python tools/server.py [--host 127.0.0.1] [--port 8765]

Stdlib only — no framework, no build step.
"""
import argparse
import importlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import repo

# --- code freshness -----------------------------------------------------------
# The registry (repo.QUERIES) and the kind table are derived from code and schemas
# at import. A server that kept its import-time copy would serve stale definitions
# forever — so before every request, re-import the query layer if its sources
# changed. importlib.reload mutates the module in place; every `repo.X` below
# resolves against the fresh definition.
_reload_lock = threading.Lock()


def _sources_fingerprint():
    paths = [Path(repo.__file__)]
    if repo.SCHEMAS.exists():
        paths += sorted(repo.SCHEMAS.glob("*.schema.json"))
    return tuple((str(p), p.stat().st_mtime_ns) for p in paths)


_fingerprint = _sources_fingerprint()


def refresh_repo():
    global _fingerprint
    with _reload_lock:
        current = _sources_fingerprint()
        if current != _fingerprint:
            importlib.reload(repo)
            _fingerprint = _sources_fingerprint()  # schema set may have changed


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
    """Bind views/<name>.template.html to its query and return the page. Any URL
    parameters reach the query as keyword arguments, so a view and its api answer the
    same question when asked the same way."""
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
        refresh_repo()  # serve the workspace's current definition, never a stale one
        url = urlparse(self.path)
        path = url.path.rstrip("/") or "/"
        parts = [p for p in path.split("/") if p]
        # the query string becomes the named query's keyword arguments (last value wins)
        params = {k: v[-1] for k, v in parse_qs(url.query).items()}
        try:
            if path == "/":
                return self._send(200, render("index"), "text/html; charset=utf-8")
            if path == "/health":
                return self._send(200, {"ok": True, "workspace": repo.ROOT.name,
                                        "queries": sorted(repo.QUERIES)})
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
                except TypeError as e:  # a parameter this query doesn't take
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
