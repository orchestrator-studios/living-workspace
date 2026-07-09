#!/usr/bin/env python3
"""repo.py — the data-access layer. The kit's skeleton, plus this review's own growth.

Single source of truth for *where* the data lives, *how* it is read and written, and
*what the canonical projections are*. Every tool (add_source, screen, add_finding,
validate, assemble_report) and the dashboard server go through here. Nothing else opens
a record in data/, hardcodes a data path, or re-derives a count — if two surfaces need
the same number, it is defined once, here.

Three layers, low to high:
  1. paths + raw json — load, load_all, save, next_id (the kit ships these)
  2. shared helpers   — cite (grown: the report and the board both format citations)
  3. projections      — screening_board (grown), registered in PROJECTIONS so the
                        server serves it at /api/screening_board

Projections read from disk on every call, so a page that polls sees screening decisions
the moment they land — one projection, read live.
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
# 1. paths + raw json
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
# 3. projections — the canonical derived shapes, defined once, rendered anywhere
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
            # included cards show the deciding criterion; excluded cards the reason
            "detail": (scr.get("reason") or scr.get("criterion") or "") if scr.get("criterion") else "",
        })
    return {
        "totals": {"sources": len(sources), "findings": len(findings),
                   "unscreened": len(cols["unscreened"]),
                   "included": len(cols["included"]),
                   "excluded": len(cols["excluded"])},
        "columns": [{"status": st, "count": len(cards), "cards": cards}
                    for st, cards in cols.items()],
    }


# every projection registered here is served at /api/<name>, and a template named
# views/<name>.template.html is bound to it automatically by tools/server.py
PROJECTIONS = {"screening_board": screening_board}
