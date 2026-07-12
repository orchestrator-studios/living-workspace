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
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMAS = ROOT / "schemas"
VIEWS = ROOT / "views"

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
# 2. shared helpers
# ----------------------------------------------------------------------------
import datetime


def _as_of(date_str):
    """Coerce a query's ?date= string to a date; empty or malformed means today."""
    if date_str:
        try:
            return datetime.date.fromisoformat(str(date_str))
        except ValueError:
            pass
    return datetime.date.today()


def last_touch(action):
    """When an action was last touched: its newest log entry, else its creation.
    Staleness — days since this — is the single derived time signal (OVERVIEW open
    question 1's placeholder: derived from the log, never stored)."""
    return max((e["date"] for e in action["log"]), default=action["created"])


def _action_view(action, as_of):
    touched = last_touch(action)
    return {"id": action["id"], "description": action["description"],
            "status": action["status"], "follow_up": action.get("follow_up"),
            "done": action.get("done"), "last_touch": touched,
            "days_stale": (as_of - datetime.date.fromisoformat(touched)).days}


# ----------------------------------------------------------------------------
# 3. named queries — each question about the record, answered here, once
# ----------------------------------------------------------------------------
# (grown: e.g.  def screening_board(): ...  — the answer a view renders)
#
# A query may take keyword arguments, filled from the URL's query string, when the
# question is only well-posed about one thing:
#
#     def table(table_id=None):
#         """One table, whole. Asked bare, it says which tables exist."""
#         if not table_id:
#             return {"error": "which table? pass ?table_id=T-001",
#                     "tables": [t["id"] for t in load_all("table")]}
#         ...
#
# Give every parameter a default, answer a bare ask helpfully (the index links queries
# with no arguments), and remember values arrive as strings.

def board(date=""):
    """The whole tree, one ask: every area, its projects, their actions — with each
    open project's stalled flag (OVERVIEW rule 2) and each action's staleness.
    ?date=YYYY-MM-DD computes staleness as of another day (default: today)."""
    as_of = _as_of(date)
    actions_by_project = {}
    for a in load_all("action"):
        actions_by_project.setdefault(a["project_id"], []).append(_action_view(a, as_of))
    area_views, totals = [], {"projects_open": 0, "projects_someday": 0,
                              "projects_done": 0, "actions_open": 0, "stalled": 0}
    projects = load_all("project")
    for area in load_all("area"):
        project_views = []
        for p in [p for p in projects if p["area_id"] == area["id"]]:
            acts = actions_by_project.get(p["id"], [])
            open_acts = [a for a in acts if a["status"] == "open"]
            stalled = p["status"] == "open" and not open_acts
            project_views.append({"id": p["id"], "title": p["title"],
                                  "done_looks_like": p["done_looks_like"],
                                  "status": p["status"], "done": p.get("done"),
                                  "stalled": stalled, "actions": acts})
            totals[f"projects_{p['status']}"] += 1
            totals["actions_open"] += len(open_acts)
            totals["stalled"] += stalled
        area_views.append({"id": area["id"], "name": area["name"],
                           "good_shape": area["good_shape"], "projects": project_views})
    return {"as_of": str(as_of), "totals": {"areas": len(area_views), **totals},
            "areas": area_views}


def run_down(date=""):
    """The daily driver: "what should I run down today?" — OVERVIEW rule 6's
    placeholder ordering, until open question 2 (prioritization) is settled.
      due     — open actions whose follow-up has arrived, oldest follow-up first
      next    — open actions with no follow-up, stalest first
      parked  — count of open actions whose follow-up is still in the future
      stalled — open projects with no open action: a next step needs deciding
    ?date=YYYY-MM-DD answers as of another day (default: today)."""
    as_of = _as_of(date)
    projects = {p["id"]: p for p in load_all("project")}
    areas = {a["id"]: a for a in load_all("area")}

    def whose(view, pid):
        p = projects[pid]
        return {**view, "project_id": pid, "project": p["title"],
                "area": areas[p["area_id"]]["name"]}

    due, upcoming, parked = [], [], 0
    for a in load_all("action"):
        if a["status"] != "open":
            continue
        view = whose(_action_view(a, as_of), a["project_id"])
        if not a.get("follow_up"):
            upcoming.append(view)
        elif a["follow_up"] <= str(as_of):
            due.append(view)
        else:
            parked += 1
    due.sort(key=lambda v: v["follow_up"])
    upcoming.sort(key=lambda v: -v["days_stale"])

    with_open = {a["project_id"] for a in load_all("action") if a["status"] == "open"}
    stalled = [{"id": p["id"], "title": p["title"], "area": areas[p["area_id"]]["name"],
                "done_looks_like": p["done_looks_like"]}
               for p in projects.values()
               if p["status"] == "open" and p["id"] not in with_open]
    return {"as_of": str(as_of), "due": due, "next": upcoming,
            "parked": parked, "stalled": stalled}


# Publishing: every query registered here is served at /api/<name> by tools/server.py,
# and a template named views/<name>.template.html is bound to it automatically. A
# parameterized query's live page must poll with its own location.search.
QUERIES = {"board": board, "run_down": run_down}
