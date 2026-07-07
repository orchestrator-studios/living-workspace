#!/usr/bin/env python
"""Regenerate a review's views from its data: PRISMA account + extraction table.

Usage:
    python tools/build_views.py <slug>

Writes:
    views/<slug>-prisma.md         PRISMA-style flow with exclusion-reason breakdown
    views/<slug>-extraction.md     one row per (study, gene arm)

Views are projections. Never hand-edit them; re-run this after any data change.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEWS = ROOT / "data" / "reviews"
VIEWS = ROOT / "views"


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def citation(r):
    a = r.get("authors") or []
    lead = a[0].split()[0] if a else "?"
    etal = " et al." if len(a) > 1 else ""
    return f"{lead}{etal} {r.get('year','n.d.')}"


def build_prisma(slug, protocol, records):
    total = len(records)
    included = [r for r in records if r.get("status") == "included"]
    excluded = [r for r in records if r.get("status") == "excluded"]
    unscreened = [r for r in records if r.get("status") == "unscreened"]
    by_reason = Counter(r.get("exclusion_reason", "unspecified") for r in excluded)
    by_stage = Counter(r.get("screening_stage", "?") for r in excluded)

    lines = [f"# PRISMA account — {protocol.get('title', slug)}", ""]
    lines.append("_Generated from data by `tools/build_views.py` — do not edit by hand._\n")
    lines.append("## Search")
    for s in protocol.get("searches", []):
        lines.append(f"- **{s['database']}** ({s['date']}): {s['count']} hits — `{s['query']}`")
    lines.append("")
    lines.append("## Flow")
    lines.append(f"- Records after de-duplication: **{total}**")
    lines.append(f"- Excluded at title/abstract: **{by_stage.get('title-abstract', 0)}**")
    lines.append(f"- Excluded at full-text: **{by_stage.get('full-text', 0)}**")
    if unscreened:
        lines.append(f"- Still unscreened: **{len(unscreened)}**")
    lines.append(f"- **Included: {len(included)}**")
    lines.append("")
    lines.append("## Exclusion reasons")
    lines.append("| Reason | n |")
    lines.append("|---|---|")
    for reason, n in by_reason.most_common():
        lines.append(f"| {reason} | {n} |")
    lines.append("")
    lines.append("## Included studies")
    for r in sorted(included, key=lambda r: -(r.get("year") or 0)):
        lines.append(f"- {citation(r)} — {r['title']} (PMID {r['pmid']})")
    return "\n".join(lines) + "\n"


def build_extraction(slug, protocol, records):
    included = [r for r in records if r.get("status") == "included"]
    lines = [f"# Extraction table — {protocol.get('title', slug)}", ""]
    lines.append("_Generated from data by `tools/build_views.py` — do not edit by hand._\n")
    cols = ["Study (PMID)", "Gene", "Modification", "Mouse model", "Asbestos", "Route",
            "Comparator", "MM incidence", "Latency", "Effect"]
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for r in sorted(included, key=lambda r: (r.get("extraction", {}).get("arms", [{}])[0].get("gene", ""))):
        cite = f"{citation(r)} ({r['pmid']})"
        for arm in r.get("extraction", {}).get("arms", []):
            def c(k):
                return (arm.get(k, "") or "").replace("|", "\\|").replace("\n", " ")
            lines.append("| " + " | ".join([
                cite, c("gene"), c("modification"), c("mouse_model"), c("asbestos_type"),
                c("route"), c("comparator"), c("incidence"), c("latency"), c("effect_direction"),
            ]) + " |")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) < 2:
        print("usage: python tools/build_views.py <slug>")
        sys.exit(2)
    slug = sys.argv[1]
    revdir = REVIEWS / slug
    protocol = load(revdir / "protocol.json")
    records = load(revdir / "records.json")
    VIEWS.mkdir(exist_ok=True)
    (VIEWS / f"{slug}-prisma.md").write_text(build_prisma(slug, protocol, records), encoding="utf-8")
    (VIEWS / f"{slug}-extraction.md").write_text(build_extraction(slug, protocol, records), encoding="utf-8")
    print(f"wrote views/{slug}-prisma.md and views/{slug}-extraction.md")


if __name__ == "__main__":
    main()
