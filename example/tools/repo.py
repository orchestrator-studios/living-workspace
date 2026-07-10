#!/usr/bin/env python3
"""repo.py — the data-access layer. The kit's skeleton, plus this review's own growth.

The only door to the record. The truth lives as plain files in data/; every read and
write goes through here. Every tool (add_source, screen, add_finding, validate,
assemble_report) and the dashboard server are clients — nothing else opens a record,
hardcodes a data path, or re-derives a count.

Three layers, low to high:
  1. primitives     — load, load_all, save, next_id: domain-blind CRUD (the kit ships these)
  2. shared helpers — cite (grown: the report and the board both format citations)
  3. named queries  — screening_board (grown): a question about the record, written down
                      once. Publishing it in QUERIES serves it at /api/screening_board.

A query belongs to a question, never to a consumer: the live board and the assembled
report render the same screening_board(). Queries recompute from the files on every call
and store nothing — an answer cannot go stale, and every derived number has exactly one
definition, here.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMAS = ROOT / "schemas"
VIEWS = ROOT / "views"

# record kinds → (id prefix, pad width), e.g. S-001 but T-01 — matching the records
KINDS = {"sources": ("S", 3), "findings": ("F", 3), "themes": ("T", 2), "searches": ("Q", 2)}


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
