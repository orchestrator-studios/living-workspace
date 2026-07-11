#!/usr/bin/env python3
"""repo.py — the data-access layer. Part of the standard kit.

The only door to the record. The truth lives as plain files in data/; every read and
write goes through here. Every tool and every view is a client — nothing else opens a
record, hardcodes a data path, or re-derives a count.

Three layers, low to high:
  1. primitives     — load, load_all, save, next_id: domain-blind CRUD, plus the kind
                      table derived from schemas/ (the kit ships these)
  2. shared helpers — grown here the moment two tools start repeating themselves
  3. named queries  — each a question about the record, written down once and recomputed
                      from the files on every ask; publishing one in QUERIES serves it
                      live at /api/<name> by tools/server.py. A query may take keyword
                      arguments — see "parameterized queries" below

A query belongs to a question, never to a consumer — if two surfaces need the same
number, it is defined once, here, and both ask it. The kit ships layer 1 and the empty
registry. Everything else is the workspace's own — grown, in place, as the work demands it.

Parameterized queries. Some questions are only well-posed about one thing — "table T-001",
not "every table" — and a workspace that answers only the whole-record question ends up
shipping the whole record to every page. So a query may take keyword arguments, which the
server fills from the URL's query string (`/api/table?table_id=T-001` and
`/view/table?table_id=T-001` alike). Three rules keep them honest:

  - Every parameter has a default, and a bare ask answers helpfully rather than raising —
    the dashboard's index links every published query with no arguments at all.
  - Values arrive as strings. A query that wants an int coerces it, and says so when it
    can't.
  - A parameter narrows a question; it never changes which question is being asked.
    `table(table_id=...)` is one question asked of one table. If you find yourself
    passing a parameter that switches the answer's *shape* — a `mode=` or a `format=` —
    that is two questions wearing one name, and it wants two queries.
"""
import glob
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMAS = ROOT / "schemas"
VIEWS = ROOT / "views"

# ---- the bound substrate: Claude Code's own state tree, read-only ----------
# This workspace owns no data/. Its system of record is ~/.claude/, read live and never
# written (OVERVIEW: "the substrate is bound"). The reach lives here; the meaning in
# capabilities/reading-sessions.md.
CLAUDE_HOME = Path(os.environ.get("CLAUDE_HOME") or (Path.home() / ".claude"))
PROJECTS = CLAUDE_HOME / "projects"

# The two grades of "active", defined once (OVERVIEW rule 3). They ride along in every
# projection's `thresholds` so views never restate the numbers.
CURRENTLY_ACTIVE_S = 2      # mtime within 2s  → someone is in this session right now
RECENTLY_ACTIVE_S = 300     # mtime within 5m  → touched lately, probably still warm

# A schema is its kind's single declaration: "x-kind" names the data/ folder, and the
# id pattern (e.g. ^S-[0-9]{3}$) carries the id prefix and pad width. Everything below
# is derived from schemas/ — growing a kind is one act: writing the schema.
_ID_PATTERN = re.compile(r"\^([A-Za-z]+)-\[0-9\]\{(\d+)\}\$")


def _scan_schemas():
    kinds, schema_for_kind = {}, {}
    if SCHEMAS.exists():
        for path in sorted(SCHEMAS.glob("*.schema.json")):
            try:  # utf-8-sig: tolerate a BOM from hand edits on Windows
                schema = json.loads(path.read_text(encoding="utf-8-sig"))
            except ValueError as err:
                raise ValueError(f"schemas/{path.name} is not valid JSON: {err}") from err
            kind = schema.get("x-kind")
            if not kind:
                continue  # declares no kind — tools/validate.py flags it
            schema_for_kind[kind] = path.name
            id_pattern = schema.get("properties", {}).get("id", {}).get("pattern", "")
            match = _ID_PATTERN.fullmatch(id_pattern)
            if match:
                kinds[kind] = (match.group(1), int(match.group(2)))
    return kinds, schema_for_kind


KINDS, SCHEMA_FOR_KIND = _scan_schemas()   # kind → (prefix, width) · kind → schema file


# ----------------------------------------------------------------------------
# 1. primitives — paths + raw json
# ----------------------------------------------------------------------------
def path_for(kind, rid):
    return DATA / kind / f"{rid}.json"


def exists(kind, rid):
    return path_for(kind, rid).exists()


def load(kind, rid):
    return json.loads(path_for(kind, rid).read_text(encoding="utf-8"))


def load_all(kind):
    folder = DATA / kind
    if not folder.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(folder.glob("*.json"))]


def save(kind, record):
    folder = DATA / kind
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{record['id']}.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")


def next_id(kind):
    if kind not in KINDS:
        raise KeyError(f"no schema in schemas/ declares kind '{kind}' "
                       f"(an x-kind plus a standard id pattern like ^X-[0-9]{{3}}$)")
    prefix, width = KINDS[kind]
    folder = DATA / kind
    existing = sorted(folder.glob(f"{prefix}-*.json")) if folder.exists() else []
    n = (int(existing[-1].stem.split("-")[1]) + 1) if existing else 1
    return f"{prefix}-{n:0{width}d}"


# ----------------------------------------------------------------------------
# 2. shared helpers — the reach into ~/.claude
# ----------------------------------------------------------------------------
_cwd_cache = {}   # transcript path → its cwd. A file's cwd never changes, so memoizing
                  # it keeps steady-state polls stat-only (new files are read once).


def _iso(epoch):
    """A wall-clock ISO timestamp in local time, to the second."""
    return datetime.fromtimestamp(epoch, timezone.utc).astimezone().isoformat(timespec="seconds")


def _session_files():
    """Every top-level session transcript. Subagent transcripts live one level deeper
    (<uuid>/subagents/*.jsonl) and are deliberately excluded — they are not sessions."""
    return glob.glob(str(PROJECTS / "*" / "*.jsonl"))


def _resolve_cwd(path):
    """The authoritative project path: the `cwd` the transcript records on its early
    lines (OVERVIEW rule 2 — never decode the lossy folder name). Cached forever."""
    key = str(path)
    if key in _cwd_cache:
        return _cwd_cache[key]
    cwd = None
    try:
        with open(path, encoding="utf-8") as handle:
            for _ in range(30):            # cwd appears within the opening lines
                line = handle.readline()
                if not line:
                    break
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if record.get("cwd"):
                    cwd = record["cwd"]
                    break
    except OSError:
        pass
    _cwd_cache[key] = cwd
    return cwd


def _subagent_count(path):
    """How many subagent transcripts this session spawned."""
    sub = Path(path).with_suffix("") / "subagents"
    return len(glob.glob(str(sub / "*.jsonl"))) if sub.exists() else 0


# ----------------------------------------------------------------------------
# 3. named queries — each question about the record, answered here, once
# ----------------------------------------------------------------------------
def sessions():
    """Every Claude Code session on this machine, most-recently-active first. A live
    projection over ~/.claude: each ask restats the transcripts, so the answer is never
    stale (and, being a bound read, is recomputed every poll). Cheap by construction —
    stat() for timing, a cached first-line read for the project path; whole transcripts
    are never parsed here (that is `session()` below). The two active flags are computed
    against 'now' on every ask, which is why polling shows liveness change."""
    now = time.time()
    rows = []
    for path in _session_files():
        try:
            stat = os.stat(path)
        except OSError:
            continue
        idle = now - stat.st_mtime
        cwd = _resolve_cwd(path)
        rows.append({
            "id": Path(path).stem,
            "project": os.path.basename(cwd) if cwd else Path(path).parent.name,
            "path": cwd or f"(unresolved: {Path(path).parent.name})",
            "last_active": _iso(stat.st_mtime),
            "created": _iso(stat.st_ctime),
            "idle_seconds": round(idle, 1),
            "age_seconds": round(now - stat.st_ctime, 1),
            "size_bytes": stat.st_size,
            "subagents": _subagent_count(path),
            "currently_active": idle <= CURRENTLY_ACTIVE_S,
            "recently_active": idle <= RECENTLY_ACTIVE_S,
        })
    rows.sort(key=lambda r: r["idle_seconds"])
    return {
        "now": _iso(now),
        "total": len(rows),
        "currently_active": sum(r["currently_active"] for r in rows),
        "recently_active": sum(r["recently_active"] for r in rows),
        "projects": len({r["path"] for r in rows}),
        "thresholds": {"currently_s": CURRENTLY_ACTIVE_S, "recently_s": RECENTLY_ACTIVE_S},
        "sessions": rows,
    }


def session(session_id=None):
    """One session in full: its transcript parsed — turn counts, first human prompt,
    model, git branch, subagents. Parameterized, because a session's detail is only a
    well-posed question about one session; asked bare (as the index links it), it lists
    the session ids. This is the only query that reads a whole transcript."""
    files = _session_files()
    if not session_id:
        return {"error": "which session? pass ?session_id=<uuid>",
                "sessions": [Path(f).stem for f in files]}
    match = next((f for f in files if Path(f).stem == session_id), None)
    if match is None:
        return {"error": f"no session '{session_id}'"}

    now = time.time()
    stat = os.stat(match)
    user_turns = assistant_turns = 0
    first_prompt = model = branch = cwd = first_ts = last_ts = None
    with open(match, encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            cwd = record.get("cwd") or cwd
            branch = record.get("gitBranch") or branch
            stamp = record.get("timestamp")
            if stamp:
                first_ts = first_ts or stamp
                last_ts = stamp
            kind = record.get("type")
            message = record.get("message") or {}
            if kind == "user":
                user_turns += 1
                content = message.get("content")
                if first_prompt is None and isinstance(content, str) and content.strip():
                    first_prompt = content.strip()[:400]
            elif kind == "assistant":
                assistant_turns += 1
                if isinstance(message.get("model"), str):
                    model = message["model"]

    idle = now - stat.st_mtime
    return {
        "id": session_id,
        "project": os.path.basename(cwd) if cwd else Path(match).parent.name,
        "path": cwd,
        "git_branch": branch,
        "model": model,
        "first_prompt": first_prompt,
        "started": first_ts,
        "last_message": last_ts,
        "last_active": _iso(stat.st_mtime),
        "created": _iso(stat.st_ctime),
        "idle_seconds": round(idle, 1),
        "size_bytes": stat.st_size,
        "user_turns": user_turns,
        "assistant_turns": assistant_turns,
        "subagents": _subagent_count(match),
        "currently_active": idle <= CURRENTLY_ACTIVE_S,
        "recently_active": idle <= RECENTLY_ACTIVE_S,
    }


# Publishing: every query registered here is served at /api/<name> by tools/server.py,
# and a template named views/<name>.template.html is bound to it automatically. A
# parameterized query's live page must poll with its own location.search.
QUERIES = {"sessions": sessions, "session": session}
