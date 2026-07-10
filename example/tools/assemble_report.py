#!/usr/bin/env python3
"""Assemble the client report from themes, findings, and included sources.

The report is assembled from the record — generated, never hand-written. Citation
integrity is structural: findings can only exist against included sources (enforced by
tools/add_finding.py and checked by tools/validate.py), so the report cannot cite
anything that wasn't screened in. Excluded sources appear only in the appendix, with
their reasons.

Usage:  python tools/assemble_report.py --date 2026-07-06     (writes report.md)
"""
import argparse
import sys

import repo
from repo import ROOT, cite


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (report date)")
    args = ap.parse_args()

    sources = {s["id"]: s for s in repo.load_all("sources")}
    findings = repo.load_all("findings")
    themes = repo.load_all("themes")
    searches = repo.load_all("searches")

    included = {sid: s for sid, s in sources.items()
                if s["screening"]["status"] == "included"}
    excluded = {sid: s for sid, s in sources.items()
                if s["screening"]["status"] == "excluded"}
    unscreened = [sid for sid, s in sources.items()
                  if s["screening"]["status"] == "unscreened"]
    if unscreened:
        print(f"REFUSED: {len(unscreened)} source(s) still unscreened "
              f"({', '.join(unscreened)}). Screen everything before assembling.")
        return 1

    L = []
    L.append("# Remote Patient Monitoring for Heart Failure: a Structured Evidence Review")
    L.append("")
    L.append(f"*Prepared for Lakeshore Health System · {args.date} · "
             "All sources, decisions, and extractions in this review are recorded in this "
             "workspace; every claim below cites an included source.*")
    L.append("")
    L.append("> *This is a worked example with fictional client, papers, and data.*")
    L.append("")
    L.append("## Question")
    L.append("")
    L.append("Does remote patient monitoring (RPM) of heart-failure patients after discharge "
             "reduce hospital readmissions? Secondary outcomes: mortality, adherence, cost. "
             "Criteria per the client brief (`seed/brief.md`).")
    L.append("")
    L.append("## Method")
    L.append("")
    L.append(f"- Seeded from the client's flagged list: "
             f"{sum(1 for s in sources.values() if s['found_via'] == 'seeded')} papers.")
    for q in searches:
        L.append(f"- Search {q['id']} ({q['date']}, {q['database']}): `{q['query']}` — "
                 f"{q['hits']} hits, {len(q['added'])} added.")
    L.append(f"- Screened: {len(sources)} sources → **{len(included)} included, "
             f"{len(excluded)} excluded** (appendix). Every decision records its criterion.")
    L.append("")
    for theme in themes:
        theme_findings = [f for f in findings if f["theme_id"] == theme["id"]]
        if not theme_findings:
            continue
        L.append(f"## {theme['name']}")
        L.append("")
        L.append(theme["summary"])
        L.append("")
        for f in theme_findings:
            src = sources[f["source_id"]]
            L.append(f"- {f['claim']} — {cite(src)} [{f['source_id']}]. "
                     f"*{f['evidence']}*")
        L.append("")
    L.append("## Included sources")
    L.append("")
    for sid, s in sorted(included.items()):
        authors = "; ".join(s["authors"])
        L.append(f"- **[{sid}]** {authors} ({s['year']}). {s['title']}. "
                 f"*{s['venue']}*. doi:{s['doi']}")
    L.append("")
    L.append("## Appendix — excluded sources")
    L.append("")
    for sid, s in sorted(excluded.items()):
        L.append(f"- **[{sid}]** {s['title']} ({s['year']}) — excluded: "
                 f"{s['screening']['reason']} ({s['screening']['criterion']}).")
    L.append("")

    out = ROOT / "report.md"
    out.write_text("\n".join(L), encoding="utf-8")
    themed = sum(1 for f in findings if f["theme_id"])
    print(f"Wrote report.md — {len([t for t in themes if any(f['theme_id'] == t['id'] for f in findings)])} themes, "
          f"{themed} findings, {len(included)} included sources; "
          f"every claim cites an included source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
