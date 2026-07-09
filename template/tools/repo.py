#!/usr/bin/env python3
"""repo.py — the data-access layer. Part of the standard kit.

Single source of truth for *where* data lives, *how* it is read and written, and *what
the canonical projections are*. Every tool and every view goes through here; nothing
else opens a record in data/, hardcodes a data path, or re-derives a count. If two
surfaces need the same number, it is defined once, here.

Three layers, low to high:
  1. paths + raw json — load, load_all, save, next_id (the kit ships these)
  2. shared helpers   — grown here the moment two tools start repeating themselves
  3. projections      — the derived shapes views render; each one registered in
                        PROJECTIONS is served live at /api/<name> by tools/server.py

The kit ships layer 1 and the empty registry. Everything else is the workspace's own —
grown, in place, as the work demands it.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMAS = ROOT / "schemas"
VIEWS = ROOT / "views"

# record kinds → (id prefix, pad width), e.g. {"sources": ("S", 3)} for S-001.
# Grown as the workspace's first schemas land.
KINDS = {}


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
# (grown: the citation formatter, the label parser — whatever starts repeating)


# ----------------------------------------------------------------------------
# 3. projections — the canonical derived shapes, defined once, rendered anywhere
# ----------------------------------------------------------------------------
# (grown: e.g.  def screening_board(): ...  — the shape a view renders)

# Every projection registered here is served at /api/<name>, and a template named
# views/<name>.template.html is bound to it automatically by tools/server.py.
PROJECTIONS = {}
