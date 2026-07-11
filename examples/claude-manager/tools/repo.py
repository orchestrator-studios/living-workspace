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
from collections import defaultdict
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
HISTORY = CLAUDE_HOME / "history.jsonl"          # every prompt: display, project, sessionId, timestamp(ms)
STATS_CACHE = CLAUDE_HOME / "stats-cache.json"   # daily message/tool/session counts (may lag behind today)
PLUGINS = CLAUDE_HOME / "plugins"                # installed plugins + the skills/commands they ship
COMMANDS = CLAUDE_HOME / "commands"              # user-defined slash commands

# The two grades of "active", defined once (OVERVIEW rule 3). They ride along in every
# projection's `thresholds` so views never restate the numbers.
CURRENTLY_ACTIVE_S = 2      # mtime within 2s  → someone is in this session right now
RECENTLY_ACTIVE_S = 300     # mtime within 5m  → touched lately, probably still warm

# Summary staleness — the trigger algo's knobs (OVERVIEW: "when to (re)summarize"). A
# session is due for a summary when it has SETTLED (so we never summarize mid-turn) and
# has changed materially since its last summary's watermark. Size is the cheap proxy for
# "materially changed" — the algo stays stat-only, no parsing. Tune here, once.
SUMMARY_SETTLE_S = 120        # leave a session alone until it's been idle this long
SUMMARY_GROWTH_BYTES = 20000  # resummarize once the transcript grew this much past the mark

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


def _local_date(epoch):
    """The local calendar date (YYYY-MM-DD) an epoch-seconds instant falls on."""
    return datetime.fromtimestamp(epoch).date().isoformat()


_history_cache = {}   # {"mtime":.., "rows":[{ts, project, session}]} — reparsed on change


def _history():
    """Every prompt ever typed, from history.jsonl: {ts (seconds), project, session}.
    Cached by mtime — the 3.7MB file is reparsed only when it grows."""
    try:
        stat = os.stat(HISTORY)
    except OSError:
        return []
    cached = _history_cache.get("v")
    if cached and cached["mtime"] == stat.st_mtime:
        return cached["rows"]
    rows = []
    try:
        with open(HISTORY, encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                ts = record.get("timestamp")
                if not ts:
                    continue
                rows.append({"ts": ts / 1000.0, "project": record.get("project") or "",
                             "session": record.get("sessionId")})
    except OSError:
        return []
    _history_cache["v"] = {"mtime": stat.st_mtime, "rows": rows}
    return rows


_hist_proj_cache = {}   # {"mtime":.., "map":{sessionId: project path}}


def _history_projects():
    """sessionId → its project path, from history.jsonl. The authoritative fallback when a
    transcript's own cwd can't be read (e.g. a brand-new session): the encoded folder name
    is lossy, but history records the real path per session. Cached with the file."""
    try:
        stat = os.stat(HISTORY)
    except OSError:
        return {}
    cached = _hist_proj_cache.get("v")
    if cached and cached["mtime"] == stat.st_mtime:
        return cached["map"]
    mapping = {}
    for row in _history():
        if row.get("session") and row.get("project"):
            mapping[row["session"]] = row["project"]   # last one wins (project is stable)
    _hist_proj_cache["v"] = {"mtime": stat.st_mtime, "map": mapping}
    return mapping


def _project_for(path, session_id):
    """The real project path of a session: its transcript cwd, else history's record for
    that session id, else None. Never the lossy encoded folder name."""
    return _resolve_cwd(path) or _history_projects().get(session_id)


def _stats_cache():
    """Claude Code's own daily-activity cache (messages / tool calls / sessions per day).
    May lag today by weeks — its lastComputedDate travels in the usage payload so views
    can say so."""
    try:
        return json.loads(STATS_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


_inventory_cache = {}   # {"at":.., "data":{...}} — install counts, refreshed on a TTL


def _install_inventory(ttl=60):
    """Counts of what's installed — skills, plugins, commands, MCP servers needing auth.
    Globbing the plugin tree on every 2s poll would be wasteful, and installs change
    rarely, so this is memoized on a short TTL rather than per-request."""
    cached = _inventory_cache.get("v")
    if cached and (time.time() - cached["at"]) < ttl:
        return cached["data"]
    skills = len(glob.glob(str(PLUGINS / "**" / "skills" / "*" / "SKILL.md"), recursive=True))
    commands = (len(glob.glob(str(COMMANDS / "*.md")))
                + len(glob.glob(str(PLUGINS / "**" / "commands" / "*.md"), recursive=True)))
    plugins = 0
    try:
        installed = json.loads((PLUGINS / "installed_plugins.json").read_text(encoding="utf-8"))
        plugins = len(installed.get("plugins", {}))
    except (OSError, ValueError):
        pass
    mcp_need_auth = 0
    try:
        auth = json.loads((CLAUDE_HOME / "mcp-needs-auth-cache.json").read_text(encoding="utf-8"))
        mcp_need_auth = len(auth) if isinstance(auth, (list, dict)) else 0
    except (OSError, ValueError):
        pass
    data = {"skills": skills, "plugins": plugins, "commands": commands,
            "mcp_need_auth": mcp_need_auth}
    _inventory_cache["v"] = {"at": time.time(), "data": data}
    return data


CLIP = 280   # one clip length for every prompt/response field, catalog and detail alike


def _clip(text):
    if not text:
        return None
    text = " ".join(text.split())
    return text[:CLIP] + "…" if len(text) > CLIP else text


def _human_text(message):
    """A human prompt is a user message whose content is a plain string. User messages
    carrying a list are tool results, not prompts."""
    content = message.get("content")
    return content.strip() if isinstance(content, str) and content.strip() else None


def _assistant_text(message):
    """The human-facing reply: the text blocks of an assistant message. A turn that only
    calls tools has no text and is not a 'response'."""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip() or None
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        joined = " ".join(p.strip() for p in parts if p.strip())
        return joined or None
    return None


_first_cache = {}    # path → first_prompt (immutable per transcript)
_tail_cache = {}     # path → {"mtime": ..., "last_prompt": ..., "last_response": ...}


def _first_prompt(path):
    """The opening human prompt. Near the top of the file and immutable — read once."""
    if path in _first_cache:
        return _first_cache[path]
    prompt = None
    try:
        with open(path, encoding="utf-8") as handle:
            for _ in range(400):                 # opening prompt is early, but after setup lines
                line = handle.readline()
                if not line:
                    break
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if record.get("type") == "user":
                    prompt = _human_text(record.get("message") or {})
                    if prompt:
                        break
    except OSError:
        pass
    _first_cache[path] = prompt
    return prompt


def _tail_exchange(path, mtime, size, budget=524288):
    """The last human prompt and last assistant reply. These live at the end of the file
    and change as a session runs, so the cache is keyed by mtime — an idle session is
    free, only a session that just wrote is re-read. Reads only the trailing `budget`
    bytes (512 KB); in a session with more tool traffic than that since the last human
    turn, the catalog's last_prompt reads as null — the detail query, which parses the
    whole transcript, always resolves it. A cheap approximation in the list, exact in
    the drill-in."""
    cached = _tail_cache.get(path)
    if cached and cached["mtime"] == mtime:
        return cached
    last_prompt = last_response = None
    try:
        with open(path, "rb") as handle:
            if size > budget:
                handle.seek(size - budget)
                handle.readline()                # drop the partial first line
            lines = handle.read().decode("utf-8", "replace").splitlines()
        for line in reversed(lines):
            if last_prompt and last_response:
                break
            try:
                record = json.loads(line)
            except ValueError:
                continue
            kind, message = record.get("type"), record.get("message") or {}
            if last_response is None and kind == "assistant":
                last_response = _assistant_text(message)
            elif last_prompt is None and kind == "user":
                last_prompt = _human_text(message)
    except OSError:
        pass
    result = {"mtime": mtime, "last_prompt": last_prompt, "last_response": last_response}
    _tail_cache[path] = result
    return result


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
        sid = Path(path).stem
        cwd = _project_for(path, sid)
        tail = _tail_exchange(path, stat.st_mtime, stat.st_size)
        summary = load("summary", sid) if exists("summary", sid) else None
        archive = load("archive", sid) if exists("archive", sid) else None
        rows.append({
            "id": sid,
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
            "first_prompt": _clip(_first_prompt(path)),
            "last_prompt": _clip(tail["last_prompt"]),
            "last_response": _clip(tail["last_response"]),
            "has_summary": summary is not None,
            "summary_stale": bool(summary) and
                (stat.st_size - summary.get("source_size", 0)) >= SUMMARY_GROWTH_BYTES,
            "summary": summary.get("text") if summary else None,
            "archived": archive is not None,
            "archived_at": archive.get("archived_at") if archive else None,
        })
    rows.sort(key=lambda r: r["idle_seconds"])
    live_rows = [r for r in rows if not r["archived"]]
    return {
        "now": _iso(now),
        "total": len(rows),
        "archived": sum(r["archived"] for r in rows),
        # tiles count the non-archived board; the archived filter reveals the rest
        "currently_active": sum(r["currently_active"] for r in live_rows),
        "recently_active": sum(r["recently_active"] for r in live_rows),
        "projects": len({r["path"] for r in live_rows}),
        "thresholds": {"currently_s": CURRENTLY_ACTIVE_S, "recently_s": RECENTLY_ACTIVE_S},
        "sessions": rows,
    }


def _summary_path_for(session_id):
    match = next((f for f in _session_files() if Path(f).stem == session_id), None)
    return match


def summaries_due():
    """The trigger algo (deterministic): which sessions need a (re)summary, and why. A
    session is DUE when it is settled (idle ≥ SUMMARY_SETTLE_S — never summarize a session
    mid-turn) AND either has no summary yet, or its transcript has grown at least
    SUMMARY_GROWTH_BYTES past the watermark its last summary recorded. Stat-only over the
    transcripts plus a read of the small summary records — cheap enough to poll. It decides
    *when*; the delegated `summarize-session` capability does the *what*."""
    now = time.time()
    due = []
    for path in _session_files():
        try:
            stat = os.stat(path)
        except OSError:
            continue
        idle = now - stat.st_mtime
        if idle < SUMMARY_SETTLE_S:          # still warm — let it settle first
            continue
        sid = Path(path).stem
        if exists("archive", sid):           # archived — set aside, don't queue it
            continue
        summary = load("summary", sid) if exists("summary", sid) else None
        if summary is None:
            reason, grew = "no summary yet", stat.st_size
        else:
            grew = stat.st_size - summary.get("source_size", 0)
            if grew < SUMMARY_GROWTH_BYTES:
                continue                     # summary still current enough
            reason = f"grew {grew:,} bytes since last summary"
        cwd = _resolve_cwd(path)
        due.append({
            "id": sid,
            "project": os.path.basename(cwd) if cwd else Path(path).parent.name,
            "path": cwd,
            "reason": reason,
            "grew_bytes": grew,
            "size_bytes": stat.st_size,
            "idle_seconds": round(idle, 1),
        })
    due.sort(key=lambda d: d["grew_bytes"], reverse=True)
    return {
        "now": _iso(now),
        "settle_s": SUMMARY_SETTLE_S,
        "growth_bytes": SUMMARY_GROWTH_BYTES,
        "count": len(due),
        "due": due,
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
    first_prompt = last_prompt = last_response = None
    model = branch = cwd = first_ts = last_ts = None
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
                human = _human_text(message)
                if human:
                    first_prompt = first_prompt or human
                    last_prompt = human
            elif kind == "assistant":
                assistant_turns += 1
                if isinstance(message.get("model"), str):
                    model = message["model"]
                reply = _assistant_text(message)
                if reply:
                    last_response = reply

    idle = now - stat.st_mtime
    cwd = cwd or _history_projects().get(session_id)   # history fallback for an unread cwd
    # join the contained summary and archive state, if any
    summary = load("summary", session_id) if exists("summary", session_id) else None
    summary_stale = bool(summary) and (stat.st_size - summary.get("source_size", 0)) >= SUMMARY_GROWTH_BYTES
    archive = load("archive", session_id) if exists("archive", session_id) else None
    return {
        "id": session_id,
        "project": os.path.basename(cwd) if cwd else Path(match).parent.name,
        "path": cwd,
        "git_branch": branch,
        "model": model,
        "first_prompt": _clip(first_prompt),
        "last_prompt": _clip(last_prompt),
        "last_response": _clip(last_response),
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
        "summary": summary.get("text") if summary else None,
        "summarized_at": summary.get("generated_at") if summary else None,
        "summary_stale": summary_stale,
        "archived": archive is not None,
        "archived_at": archive.get("archived_at") if archive else None,
        "archive_reason": archive.get("reason") if archive else None,
    }


# Publishing: every query registered here is served at /api/<name> by tools/server.py,
# and a template named views/<name>.template.html is bound to it automatically. A
# parameterized query's live page must poll with its own location.search.
_FRONTMATTER = re.compile(r"^﻿?---\s*\n(.*?)\n---", re.S)
_VERSIONDIR = re.compile(r"^\d+(\.\d+)+")


def _frontmatter(text):
    """A minimal YAML-frontmatter reader — enough for SKILL.md / agent / command headers:
    top-level `key: value` pairs. Not a full YAML parser; nested/list values are skipped."""
    match = _FRONTMATTER.match(text)
    fields = {}
    if not match:
        return fields
    for line in match.group(1).splitlines():
        if line[:1] in (" ", "\t", "-"):        # continuation or list item — skip
            continue
        pair = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if pair:
            fields[pair.group(1).lower()] = pair.group(2).strip()
    return fields


def _plugin_and_marketplace(path, anchor_folder):
    """From a path like plugins/cache/<mkt>/<plugin>/<ver>/<anchor>/... or
    plugins/marketplaces/<mkt>/**/<plugin>/<anchor>/..., pull (plugin, marketplace,
    installed). Installed = it lives under cache/ (an installed plugin's real files)."""
    parts = Path(path).parts
    try:
        ai = parts.index(anchor_folder)
    except ValueError:
        return None, None, False
    plugin = parts[ai - 1]
    if _VERSIONDIR.match(plugin):               # cache path: skills sit under <ver>/skills
        plugin = parts[ai - 2]
    marketplace = None
    for root in ("cache", "marketplaces"):
        if root in parts:
            i = parts.index(root)
            marketplace = parts[i + 1] if i + 1 < len(parts) else None
            break
    installed = "cache" in parts
    return plugin, marketplace, installed


def _collect_extensions():
    """Everything installed or available that extends Claude, unified: plugins, skills,
    agents, commands, MCP servers. Each item: {kind, name, description, source, installed,
    ...kind extras}. Deduped by (kind, source, name), an installed instance winning over a
    marketplace one."""
    items = {}

    def add(rec):
        key = (rec["kind"], rec.get("source"), rec["name"])
        if key not in items or (rec["installed"] and not items[key]["installed"]):
            items[key] = rec

    enabled = {}
    try:
        enabled = json.loads((CLAUDE_HOME / "settings.json").read_text(encoding="utf-8")).get("enabledPlugins", {})
    except (OSError, ValueError):
        pass
    # plugin ref is "name@marketplace"; index enabled by bare plugin name so a skill/agent
    # shipped by a disabled plugin reads as disabled, not active.
    enabled_by_name = {ref.partition("@")[0]: bool(v) for ref, v in enabled.items()}

    # plugins (authoritative inventory)
    try:
        installed = json.loads((PLUGINS / "installed_plugins.json").read_text(encoding="utf-8"))
        for ref, entries in installed.get("plugins", {}).items():
            name, _, marketplace = ref.partition("@")
            entry = (entries or [{}])[0]
            add({"kind": "plugin", "name": name, "description": None, "source": marketplace,
                 "installed": True, "enabled": bool(enabled.get(ref, True)),
                 "version": entry.get("version"), "model": None, "status": None,
                 "path": entry.get("installPath")})
    except (OSError, ValueError):
        pass

    # skills and agents (frontmatter-bearing markdown under a plugin folder)
    for kind, anchor in (("skill", "skills"), ("agent", "agents")):
        for path in glob.glob(str(PLUGINS / "**" / anchor / "*" / "*.md"), recursive=True) \
                + glob.glob(str(PLUGINS / "**" / anchor / "*.md"), recursive=True):
            if os.path.basename(path) not in ("SKILL.md",) and anchor == "skills":
                continue
            try:
                fm = _frontmatter(Path(path).read_text(encoding="utf-8"))
            except OSError:
                continue
            plugin, marketplace, installed = _plugin_and_marketplace(path, anchor)
            add({"kind": kind, "name": fm.get("name") or Path(path).parent.name,
                 "description": fm.get("description"), "source": plugin,
                 "installed": installed,
                 "enabled": enabled_by_name.get(plugin, True) if installed else None,
                 "version": None, "model": fm.get("model"), "status": None, "path": path})

    # commands (user-defined + plugin)
    for path in glob.glob(str(COMMANDS / "*.md")):
        try:
            fm = _frontmatter(Path(path).read_text(encoding="utf-8"))
        except OSError:
            fm = {}
        add({"kind": "command", "name": Path(path).stem, "description": fm.get("description"),
             "source": "user", "installed": True, "enabled": None, "version": None,
             "model": None, "status": None, "path": path})
    for path in glob.glob(str(PLUGINS / "**" / "commands" / "*.md"), recursive=True):
        plugin, marketplace, installed = _plugin_and_marketplace(path, "commands")
        try:
            fm = _frontmatter(Path(path).read_text(encoding="utf-8"))
        except OSError:
            fm = {}
        add({"kind": "command", "name": Path(path).stem, "description": fm.get("description"),
             "source": plugin, "installed": installed,
             "enabled": enabled_by_name.get(plugin, True) if installed else None,
             "version": None, "model": None, "status": None, "path": path})

    # MCP servers (only those the auth cache knows about — a full inventory isn't on disk)
    try:
        auth = json.loads((CLAUDE_HOME / "mcp-needs-auth-cache.json").read_text(encoding="utf-8"))
        for name in (auth if isinstance(auth, dict) else []):
            add({"kind": "mcp", "name": name, "description": None, "source": None,
                 "installed": True, "enabled": None, "version": None, "model": None,
                 "status": "needs re-auth", "path": None})
    except (OSError, ValueError):
        pass

    # derive state: what's actually affecting Claude vs the marketplace catalog
    for rec in items.values():
        rec["state"] = ("available" if not rec["installed"]
                        else "disabled" if rec.get("enabled") is False
                        else "active")
    return list(items.values())


_ext_cache = {}   # {"at":.., "data":[...]} — the extension scan, refreshed on a TTL


def usage(days=90):
    """Activity over time (volume only): prompts per day from history.jsonl — complete and
    current — enriched with Claude Code's own message/tool/session counts from
    stats-cache.json where that cache reaches (it lags today, so recent days show prompts
    only). Plus a per-project breakdown. The `days` parameter windows the daily series for
    the chart; totals are computed over everything."""
    try:
        days = max(1, int(days))
    except (TypeError, ValueError):
        days = 90
    now = time.time()
    cutoff7, cutoff30 = now - 7 * 86400, now - 30 * 86400

    day_prompts = defaultdict(int)
    active30 = set()
    prompts_7d = prompts_30d = 0
    projects = defaultdict(lambda: {"prompts": 0, "prompts_30d": 0, "last_ts": 0.0, "path": ""})
    for row in _history():
        date = _local_date(row["ts"])
        day_prompts[date] += 1
        name = os.path.basename(row["project"]) if row["project"] else "(none)"
        proj = projects[name]
        proj["prompts"] += 1
        proj["path"] = row["project"]
        proj["last_ts"] = max(proj["last_ts"], row["ts"])
        if row["ts"] >= cutoff30:
            prompts_30d += 1
            proj["prompts_30d"] += 1
            active30.add(date)
        if row["ts"] >= cutoff7:
            prompts_7d += 1

    stats = _stats_cache()
    by_date = {a["date"]: a for a in stats.get("dailyActivity", [])}
    all_dates = sorted(set(day_prompts) | set(by_date))
    day_rows = [{"date": d,
                 "prompts": day_prompts.get(d, 0),
                 "messages": by_date.get(d, {}).get("messageCount"),
                 "tool_calls": by_date.get(d, {}).get("toolCallCount"),
                 "sessions": by_date.get(d, {}).get("sessionCount")}
                for d in all_dates]

    project_rows = sorted(
        ({"project": name, "path": p["path"], "prompts": p["prompts"],
          "prompts_30d": p["prompts_30d"],
          "last_active": _iso(p["last_ts"]) if p["last_ts"] else None}
         for name, p in projects.items()),
        key=lambda r: (r["prompts_30d"], r["prompts"]), reverse=True)

    return {
        "now": _iso(now),
        "as_of_statscache": stats.get("lastComputedDate"),
        "span": {"from": all_dates[0] if all_dates else None,
                 "to": all_dates[-1] if all_dates else None},
        "totals": {
            "prompts_7d": prompts_7d,
            "prompts_30d": prompts_30d,
            "active_days_30d": len(active30),
            "messages_all": sum(a.get("messageCount", 0) for a in stats.get("dailyActivity", [])),
            "tool_calls_all": sum(a.get("toolCallCount", 0) for a in stats.get("dailyActivity", [])),
        },
        "days": day_rows[-days:],
        "projects": project_rows,
    }


def overview():
    """The cockpit: at-a-glance numbers across every module, plus what needs attention.
    Deliberately cheap — session counts come from stat() alone (no head/tail parsing),
    contained state from counting files, install counts from the memoized inventory."""
    now = time.time()
    files = _session_files()
    live = recent = 0
    stats = []
    for path in files:
        try:
            st = os.stat(path)
        except OSError:
            continue
        idle = now - st.st_mtime
        live += idle <= CURRENTLY_ACTIVE_S
        recent += idle <= RECENTLY_ACTIVE_S
        stats.append((idle, path))
    stats.sort(key=lambda x: x[0])

    recently_active = []
    for idle, path in stats[:6]:
        cwd = _project_for(path, Path(path).stem)
        recently_active.append({
            "id": Path(path).stem,
            "project": os.path.basename(cwd) if cwd else Path(path).parent.name,
            "idle_seconds": round(idle, 1),
            "currently_active": idle <= CURRENTLY_ACTIVE_S,
            "recently_active": idle <= RECENTLY_ACTIVE_S,
        })

    inventory = _install_inventory()
    use = usage()
    attention = []
    if live:
        attention.append({"kind": "live", "text": f"{live} session{'s' if live != 1 else ''} live right now"})
    if inventory["mcp_need_auth"]:
        attention.append({"kind": "mcp", "text": f"{inventory['mcp_need_auth']} MCP server(s) need re-auth"})

    return {
        "now": _iso(now),
        "sessions": {
            "total": len(files),
            "live": live,
            "recent": recent,
            "summarized": len(glob.glob(str(DATA / "summary" / "*.json"))),
            "archived": len(glob.glob(str(DATA / "archive" / "*.json"))),
        },
        "usage": {
            "prompts_7d": use["totals"]["prompts_7d"],
            "prompts_30d": use["totals"]["prompts_30d"],
            "days": use["days"][-30:],
        },
        "install": inventory,
        "recently_active": recently_active,
        "attention": attention,
    }


def extensions():
    """Everything that extends Claude on this machine — plugins, skills, agents, commands,
    MCP servers — in one unified list, sorted by kind. Cached (the scan reads ~100 header
    files); the Extensions module filters it by kind and installed/available client-side."""
    cached = _ext_cache.get("v")
    if cached and (time.time() - cached["at"]) < 60:
        rows = cached["data"]
    else:
        rows = _collect_extensions()
        _ext_cache["v"] = {"at": time.time(), "data": rows}
    kind_order = {"plugin": 0, "skill": 1, "agent": 2, "command": 3, "mcp": 4}
    state_order = {"active": 0, "disabled": 1, "available": 2}
    rows = sorted(rows, key=lambda r: (state_order.get(r["state"], 3),
                                       kind_order.get(r["kind"], 9),
                                       (r["source"] or ""), r["name"].lower()))
    by_kind, by_state = {}, {}
    for r in rows:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
        by_state[r["state"]] = by_state.get(r["state"], 0) + 1
    return {
        "now": _iso(time.time()),
        "total": len(rows),
        "installed": sum(1 for r in rows if r["installed"]),
        "available": sum(1 for r in rows if not r["installed"]),
        "kinds": ["plugin", "skill", "agent", "command", "mcp"],
        "states": ["active", "disabled", "available"],
        "by_kind": by_kind,
        "by_state": by_state,
        "extensions": rows,
    }


QUERIES = {"overview": overview, "usage": usage, "extensions": extensions,
           "sessions": sessions, "session": session, "summaries_due": summaries_due}


# ----------------------------------------------------------------------------
# 4. actions — the write counterpart of queries
# ----------------------------------------------------------------------------
# The tracker reads sessions from ~/.claude (never writes there), but it OWNS its
# contained state and may write that. Archiving is the one write the dashboard drives: a
# card button POSTs to /action/archive. These are the single home of the archive rule —
# tools/archive_session.py (the CLI) calls the same functions, so nothing restates it.

def archive(session_id=None, reason=None):
    """Set a session aside. Idempotent — archiving an archived session is a no-op."""
    if not session_id:
        return {"ok": False, "error": "session_id required"}
    if session_id not in {Path(f).stem for f in _session_files()}:
        return {"ok": False, "error": f"no session '{session_id}'"}
    if not exists("archive", session_id):
        save("archive", {"id": session_id, "session_id": session_id,
                         "archived_at": _iso(time.time()), "reason": reason})
    return {"ok": True, "session_id": session_id, "archived": True}


def unarchive(session_id=None):
    """Bring a session back. Idempotent — removes the archive record if present."""
    if not session_id:
        return {"ok": False, "error": "session_id required"}
    path = path_for("archive", session_id)
    if path.exists():
        path.unlink()
    return {"ok": True, "session_id": session_id, "archived": False}


ACTIONS = {"archive": archive, "unarchive": unarchive}
