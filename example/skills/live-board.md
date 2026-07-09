---
description: Keeping the live screening board up for the user. Use at the first
  data-touching action of a session — before searching, screening, or extracting.
---

# Skill: keeping the live board up

The board (`tools/server.py` → http://127.0.0.1:8765/) is the user's window into the
review: the columns filling as decisions land. A user working in one terminal will not
start a second long-running server on their own — so *you* keep it up for them. Treat a
running board as a precondition for review work, the way validation is a postcondition.

## The rule

At the **first data-touching action of a session** — add, search, screen, extract — make
sure the server is running **before** the slow work starts, and hand the user the link.
Once per session; don't re-announce on every action.

## The recipe

1. **Probe — never assume, never double-launch.** The health endpoint makes the check
   cheap and idempotent:

       python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=1)"

   Exit 0 → already up; just give the link (first time this session). Non-zero → launch it.

2. **Launch in the background** (the server is CWD-independent — its paths come from
   `repo.py`), so it outlives the turn:

       python tools/server.py

   Re-probe until it answers (well under a second). If the port is held by a foreign
   process, relaunch with `--port 8766` and use that port in the link.

3. **Tell the user, once**, framed as *watch it live*: "The board is up at
   http://127.0.0.1:8765/ — open it and you'll see decisions land as I screen."

## Lifecycle

The background server dies with the session; next session the probe finds it down and you
relaunch. It is read-only and holds no state — never offer to shut it down unless asked,
and never start a second one when the probe says one is up.
