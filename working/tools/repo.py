#!/usr/bin/env python
"""repo.py — the data-access layer for reviews.

Single source of truth for *where* review data lives, *how* it is read and written,
and *what the canonical projections are*. Every tool (validate, screen, build_views,
build_report) and the dashboard server go through here. Nothing else should open
`protocol.json` / `records.json`, hardcode the `data/reviews` path, or re-derive the
pipeline funnel — if two callers need the same number, it is defined once, here.

Three layers, low to high:
  1. paths + raw json     — review_dir, list_reviews, load_protocol/records, save_records
  2. shared helpers       — citation, query_labels
  3. projections          — pipeline(): the funnel counts, exclusion breakdowns, and
                            per-query retrieval that the PRISMA view, the HTML report,
                            and the live dashboard all render.

The projections read from disk on every call, so a dashboard that polls `pipeline()`
sees screening progress as it lands in `records.json` — that is the whole "real-time"
story: one projection, read live, rendered many ways.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REVIEWS = DATA / "reviews"
SCHEMAS = ROOT / "schemas"


# ----------------------------------------------------------------------------
# 1. paths + raw json
# ----------------------------------------------------------------------------
def review_dir(slug):
    return REVIEWS / slug


def views_dir(slug):
    return review_dir(slug) / "views"


def list_reviews():
    if not REVIEWS.exists():
        return []
    return sorted(p.name for p in REVIEWS.iterdir() if p.is_dir())


def _read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _write_json(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def has_protocol(slug):
    return (review_dir(slug) / "protocol.json").exists()


def load_protocol(slug):
    return _read_json(review_dir(slug) / "protocol.json")


def load_records(slug):
    p = review_dir(slug) / "records.json"
    return _read_json(p) if p.exists() else []


def save_records(slug, records):
    _write_json(review_dir(slug) / "records.json", records)


def load_review(slug):
    """The whole review as the views bind it: {protocol, records}."""
    return {"protocol": load_protocol(slug), "records": load_records(slug)}


# ----------------------------------------------------------------------------
# 2. shared helpers (formerly copy-pasted per tool)
# ----------------------------------------------------------------------------
def citation(r):
    a = r.get("authors") or []
    lead = a[0].split()[0] if a else "?"
    etal = " et al." if len(a) > 1 else ""
    return f"{lead}{etal} {r.get('year', 'n.d.')}"


def query_labels(protocol):
    """Query labels in execution order, parsed from each search's `note` (label=...)."""
    out = []
    for s in protocol.get("searches", []):
        m = re.search(r"label=([^;]+)", s.get("note", "") or "")
        if m:
            out.append(m.group(1).strip())
    return out


def search_by_label(protocol):
    out = {}
    for s in protocol.get("searches", []):
        m = re.search(r"label=([^;]+)", s.get("note", "") or "")
        if m:
            out[m.group(1).strip()] = s
    return out


# ----------------------------------------------------------------------------
# 3. projections — the canonical pipeline funnel, defined once
# ----------------------------------------------------------------------------
def _is_ta_excluded(r):
    return r.get("status") == "excluded" and r.get("screening_stage") == "title-abstract"


def _is_ft_excluded(r):
    return r.get("status") == "excluded" and r.get("screening_stage") == "full-text"


def pipeline(slug):
    """Read a review live and return its canonical funnel projection."""
    return pipeline_from(load_protocol(slug), load_records(slug), slug)


def pipeline_from(protocol, records, slug=None):
    """The pipeline funnel derived from an in-memory (protocol, records).

    This is the single definition of the review's flow. The PRISMA markdown view,
    the HTML report, and the live dashboard all render *this* shape — they never
    recompute stage counts themselves.
    """
    labels = query_labels(protocol)
    by_label = search_by_label(protocol)

    N = len(records)
    included = [r for r in records if r.get("status") == "included"]
    ta_excluded = [r for r in records if _is_ta_excluded(r)]
    ft_excluded = [r for r in records if _is_ft_excluded(r)]
    unscreened = [r for r in records if r.get("status") == "unscreened"]
    needs_adj = [r for r in records if r.get("status") == "needs-adjudication"]

    # per-query retrieval, cumulative-new in execution order
    seen = set()
    raw_retrievals = 0
    queries = []
    for lbl in labels:
        ret = [r for r in records if lbl in (r.get("found_by") or [])]
        new = [r for r in ret if r["pmid"] not in seen]
        for r in ret:
            seen.add(r["pmid"])
        raw_retrievals += len(ret)
        s = by_label.get(lbl, {})
        queries.append({
            "label": lbl,
            "database": s.get("database", ""),
            "date": s.get("date", ""),
            "query": s.get("query", ""),
            "returned": len(ret),
            "added": len(new),
            "cumulative": len(seen),
            "included": sum(1 for r in ret if r.get("status") == "included"),
        })

    def reason_break(subset):
        return Counter(r.get("exclusion_reason", "unspecified") for r in subset).most_common()

    # records returned by exactly k queries (dedup overlap)
    overlap = Counter(len(r.get("found_by") or []) for r in records)

    n_arms = sum(len((r.get("extraction") or {}).get("arms", [])) for r in included)
    methods = {s.get("method") for r in records for s in (r.get("screening") or {}).values()}

    return {
        "slug": slug,
        "title": protocol.get("title", slug),
        "question": protocol.get("question", ""),
        "source": f"data/reviews/{slug}" if slug else None,
        "totals": {
            "retrieved": raw_retrievals,
            "unique": N,
            # floored: a review with records but no labeled-search provenance has
            # raw_retrievals=0, which would otherwise make this go negative.
            "duplicates_removed": max(0, raw_retrievals - N),
            "unscreened": len(unscreened),
            "ta_excluded": len(ta_excluded),
            "passed_ta": N - len(ta_excluded),
            "ft_excluded": len(ft_excluded),
            "included": len(included),
            "needs_adjudication": len(needs_adj),
            "extraction_arms": n_arms,
        },
        "exclusions": {
            "title-abstract": reason_break(ta_excluded),
            "full-text": reason_break(ft_excluded),
        },
        "queries": queries,
        "overlap": {str(k): overlap[k] for k in sorted(overlap)},
        "screening_methods": sorted(m for m in methods if m),
        "included_studies": [
            {"pmid": r["pmid"], "citation": citation(r), "title": r.get("title", ""),
             "year": r.get("year")}
            for r in sorted(included, key=lambda r: -(r.get("year") or 0))
        ],
    }
