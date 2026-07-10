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
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def column_violation(value, column):
    """Does a value conform to its column's declared type? None if fine, else the
    complaint. The single definition of the type rule (OVERVIEW rule 4) — used by
    validate.py after every write and by any tool that coerces values on the way in.
    null is always fine here: it means unknown; required-ness is a row-level check."""
    if value is None:
        return None
    kind = column["type"]
    if kind == "text":
        ok = isinstance(value, str)
    elif kind == "number":
        ok = isinstance(value, (int, float)) and not isinstance(value, bool)
    elif kind == "date":
        ok = isinstance(value, str) and _DATE.match(value)
    elif kind == "boolean":
        ok = isinstance(value, bool)
    elif kind == "select":
        ok = isinstance(value, str) and value in column.get("options", [])
    else:
        return f"column '{column['key']}' has unknown type '{kind}'"
    if not ok:
        want = f"one of {column.get('options')}" if kind == "select" else kind
        return f"expected {want}, got {value!r}"
    return None


# ----------------------------------------------------------------------------
# 3. named queries — each question about the record, answered here, once
# ----------------------------------------------------------------------------
# This workspace is where the kit's parameterized queries earn their keep: a table's
# rows are only a well-posed question about *one* table. Note the division — `tables`
# answers "what tables exist?" and never carries row data; `table` answers "what does
# this one say?" and takes the id. Two questions, two queries, neither a mode of the
# other. See the "Parameterized queries" note in the module docstring.

def tables():
    """The catalog: every table, with its shape and row count — never the row data."""
    row_counts = {}
    for row in load_all("row"):
        row_counts[row["table_id"]] = row_counts.get(row["table_id"], 0) + 1
    return [{"id": t["id"], "name": t["name"], "description": t.get("description", ""),
             "columns": len(t["columns"]), "rows": row_counts.get(t["id"], 0),
             "created": t["created"], "bottom_line": t.get("bottom_line")}
            for t in load_all("table")]


def table(table_id=None):
    """One table, whole: its definition and its rows. Parameterized — asks about exactly
    one table, never all of them. Asked bare (as the dashboard index links it), it names
    the tables that exist rather than raising."""
    if not table_id:
        return {"error": "which table? pass ?table_id=T-001",
                "tables": [t["id"] for t in load_all("table")]}
    if not exists("table", table_id):
        return {"error": f"no table '{table_id}'"}
    return {"table": load("table", table_id),
            "rows": [r for r in load_all("row") if r["table_id"] == table_id]}


# Publishing: every query registered here is served at /api/<name> by tools/server.py,
# and a template named views/<name>.template.html is bound to it automatically. A
# parameterized query's live page must poll with its own location.search.
QUERIES = {"tables": tables, "table": table}
