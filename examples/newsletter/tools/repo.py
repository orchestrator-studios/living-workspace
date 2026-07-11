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
def runs_in_window(week_start, week_end):
    """The runs that fed a window — a run counts if its window overlaps."""
    return [r for r in load_all("run")
            if r["window_start"] <= week_end and r["window_end"] >= week_start]


def window_articles(week_start, week_end):
    """The articles a window's runs landed, in id order — the one definition of
    'what belongs to this issue' (assembly and the issues view both ask here)."""
    ids = sorted({aid for r in runs_in_window(week_start, week_end)
                  for aid in r["added"]})
    return [load("article", aid) for aid in ids if exists("article", aid)]


# ----------------------------------------------------------------------------
# 3. named queries — each question about the record, answered here, once
# ----------------------------------------------------------------------------
def issues(issue=None):
    """The newsletter shelf: every issue for the left rail, and one issue in full for
    the right panel — its articles, the runs that fed its window, and the retrieval
    config those runs executed. `issue` narrows which one is open; default: the latest."""
    records = sorted(load_all("issue"), key=lambda i: i["id"], reverse=True)
    shelf = [{"id": i["id"], "title": i["title"], "status": i["status"],
              "week_start": i["week_start"], "week_end": i["week_end"],
              "article_count": len(i["articles"])} for i in records]
    target = issue or (records[0]["id"] if records else None)
    selected = next((i for i in records if i["id"] == target), None)
    if selected is None:
        return {"issues": shelf, "selected": None,
                "error": f"no issue '{target}'" if target else None}

    all_articles = {a["id"]: a for a in load_all("article")}
    runs = []
    for r in runs_in_window(selected["week_start"], selected["week_end"]):
        outcome = {"included": 0, "excluded": 0, "candidate": 0}
        for aid in r["added"]:
            if aid in all_articles:
                outcome[all_articles[aid]["status"]] += 1
        config = (load("retrieval_config", r["config"])
                  if exists("retrieval_config", r["config"]) else None)
        runs.append({"id": r["id"], "date": r["date"],
                     "window_start": r["window_start"], "window_end": r["window_end"],
                     "matched": r["matched"], "added": len(r["added"]),
                     "skipped": len(r["skipped_urls"]), "outcome": outcome,
                     "config": config and {"id": config["id"], "name": config["name"],
                                           "source": config["source"],
                                           "query": config["query"]}})

    # the working state a draft shows: candidates its window's runs landed that
    # still await a verdict (0 once the filter+record stages are done)
    pending = sum(r["outcome"]["candidate"] for r in runs)

    return {"issues": shelf, "error": None,
            "selected": {"id": selected["id"], "title": selected["title"],
                         "status": selected["status"], "created": selected["created"],
                         "pending_candidates": pending,
                         "week_start": selected["week_start"],
                         "week_end": selected["week_end"],
                         "executive_summary": selected.get("executive_summary"),
                         "has_body": bool(selected.get("body")),
                         "articles": [{"id": a["id"], "url": a["url"],
                                       "title": a["title"],
                                       "source_name": a["source_name"],
                                       "published": a.get("published", ""),
                                       "summary": a.get("summary")}
                                      for a in (all_articles.get(aid) for aid in selected["articles"])
                                      if a],
                         "runs": runs}}


# Publishing: every query registered here is served at /api/<name> by tools/server.py,
# and a template named views/<name>.template.html is bound to it automatically. A
# parameterized query's live page must poll with its own location.search.
QUERIES = {"issues": issues}
