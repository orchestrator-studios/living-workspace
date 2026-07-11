---
name: dashboard
description: Keeping the live dashboard up for the user. Use at the first data-touching
  action of a session — before adding, searching, screening, or transforming anything.
runs: in-context
---

# Capability: keeping the dashboard up

*Runs in-context: it is three commands and a link that must land in this conversation.
Nothing here is worth a fresh context.*

The dashboard (`tools/server.py` → http://127.0.0.1:8765/) is the user's window into the
workspace: the index of everything it can show, each view updating live as data lands. A
user working in one terminal will not start a second long-running server on their own —
so *you* keep it up for them. Treat a running dashboard as a precondition for data work,
the way validation is a postcondition.

## The rule

At the **first data-touching action of a session**, make sure the server is running
**before** the slow work starts, and hand the user the link. Once per session; don't
re-announce on every action.

Bring it up *first* so the live magic lands: the user should have the page open before the
work runs, so they watch it happen — not discover a finished result after the fact.

## The recipe

1. **Probe — never assume, never double-launch.** The health endpoint makes the check
   cheap and idempotent:

       python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=1)"

   Exit 0 → already up; just give the link (first time this session). Non-zero → launch it.

2. **Launch in the background** (the server is CWD-independent — its paths come from
   `repo.py`), so it outlives the turn:

       python tools/server.py

   Re-probe until it answers (well under a second). If the port is held by a foreign
   process (the health check doesn't return our `{"ok": true}`, or the bind fails),
   relaunch with `--port 8766` and use that port in the link.

3. **Tell the user, once**, framed as *watch it live*: "The dashboard is up at
   http://127.0.0.1:8765/ — open it and you'll see the work land as it happens."

## Lifecycle

The background server dies with the session; next session the probe finds it down and you
relaunch. It is read-only and holds no state — never offer to shut it down unless asked,
and never start a second one when the probe says one is up.

## Growing what it shows

The server itself never changes. A new live view is exactly two grown pieces: a named
query in `tools/repo.py` (published in `QUERIES`) and a template in `views/` with the same
name. The server binds them automatically — `/view/<name>` for the page, `/api/<name>` for
the answer it polls — and the new view appears on the index the moment the template exists.
