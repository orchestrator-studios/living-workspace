#!/usr/bin/env python3
"""repo.py — the data-access layer. The kit's skeleton, plus this review's own growth.

The only door to the record. The truth lives as plain files in data/; every read and
write goes through here. Every tool (add_source, screen, add_finding, validate,
assemble_report) and the dashboard server are clients — nothing else opens a record,
hardcodes a data path, or re-derives a count.

Three layers, low to high:
  1. primitives     — load, load_all, save, next_id: domain-blind CRUD, plus the kind
                      table derived from schemas/ (the kit ships these)
  2. shared helpers — cite (grown: the report and the board both format citations)
  3. named queries  — screening_board (grown): a question about the record, written down
                      once. Publishing it in QUERIES serves it at /api/screening_board.

A query belongs to a question, never to a consumer: the live board and the assembled
report render the same screening_board(). Queries recompute from the files on every call
and store nothing — an answer cannot go stale, and every derived number has exactly one
definition, here.
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
def cite(source):
    first = source["authors"][0].split()[0]
    return f"{first} et al. ({source['year']})" if len(source["authors"]) > 1 \
        else f"{first} ({source['year']})"


# ----------------------------------------------------------------------------
# 3. named queries — each question about the record, answered here, once
# ----------------------------------------------------------------------------
def screening_board():
    """The screening board: every source as a card in its status column.

    The one definition of "what's unscreened / included / excluded" — the live board
    renders exactly this, and anything else that needs the split asks here.
    """
    sources = load_all("sources")
    findings = load_all("findings")
    cols = {"unscreened": [], "included": [], "excluded": []}
    for s in sources:
        scr = s["screening"]
        authors = s["authors"][0] + (" et al." if len(s["authors"]) > 1 else "")
        cols[scr["status"]].append({
            "id": s["id"],
            "title": s["title"],
            "meta": f"{authors} · {s['year']} · via {s['found_via']}",
            # excluded cards show the reason; included cards the deciding criterion
            "detail": scr.get("reason") or scr.get("criterion") or "",
        })
    return {
        "totals": {"sources": len(sources), "findings": len(findings),
                   "unscreened": len(cols["unscreened"]),
                   "included": len(cols["included"]),
                   "excluded": len(cols["excluded"])},
        "columns": [{"status": st, "count": len(cards), "cards": cards}
                    for st, cards in cols.items()],
    }


# publishing: every query registered here is served at /api/<name> by tools/server.py,
# and a template named views/<name>.template.html is bound to it automatically
QUERIES = {"screening_board": screening_board}
