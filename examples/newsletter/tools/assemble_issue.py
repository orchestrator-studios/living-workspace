#!/usr/bin/env python3
"""assemble_issue.py — render one issue's newsletter file (grown). The deliverable is
a projection: assembled from the issue record and its article records, never
hand-written, regenerated after any change (OVERVIEW rule 4).

Carries OVERVIEW rule 3 — the closure guarantee: REFUSED if the issue references an
article that is missing, not included, or has no summary. The newsletter cannot carry
an unscreened or unsummarized paper, structurally.

Usage:  python tools/assemble_issue.py N-001         → writes newsletter-N-001.md
"""
import argparse
import sys

import repo


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble one issue's newsletter file.")
    ap.add_argument("issue_id")
    args = ap.parse_args()

    if not repo.exists("issue", args.issue_id):
        print(f"REFUSED: no issue '{args.issue_id}'")
        return 1
    issue = repo.load("issue", args.issue_id)

    articles = []
    for aid in issue["articles"]:
        if not repo.exists("article", aid):
            print(f"REFUSED: {args.issue_id} references {aid} — no such article")
            return 1
        article = repo.load("article", aid)
        if article["status"] != "included":
            print(f"REFUSED: {aid} is {article['status']}, not included "
                  f"({article.get('filter_reason') or 'unscreened'})")
            return 1
        if not article.get("summary"):
            print(f"REFUSED: {aid} is included but has no summary yet")
            return 1
        articles.append(article)

    lines = [f"# {issue['title']}", "",
             f"*Coverage: {issue['week_start']} to {issue['week_end']} · "
             f"{len(articles)} papers · issue {issue['id']} ({issue['status']})*", ""]
    if issue.get("executive_summary"):
        lines += ["## This week", "", issue["executive_summary"], ""]
    lines += ["## The papers", ""]
    for a in articles:
        lines += [f"### {a['title']}",
                  f"*{a['authors']} — {a['journal']}, {a['pub_date']} · "
                  f"[PMID {a['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{a['pmid']}/)*",
                  "", a["summary"], ""]
    lines += ["---", "",
              "*Assembled by tools/assemble_issue.py from the workspace record — "
              "regenerate, don't edit.*", ""]

    out = repo.ROOT / f"newsletter-{issue['id']}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out.name} — {len(articles)} papers, every one included and summarized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
