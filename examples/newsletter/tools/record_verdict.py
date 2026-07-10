#!/usr/bin/env python3
"""record_verdict.py — persist a filter verdict (grown). The only way an article
leaves candidate.

This tool does not screen. The judgment is the semantic filter's
(capabilities/semantic-filter.md — a delegated analysis that returns verdicts and
writes nothing); this is the persistence step its caller runs with that analysis.
Carries OVERVIEW rule 2 — every verdict has its reason: no reason, no move.

Usage:  python tools/record_verdict.py A-001 --status included --reason "..." [--summary "..."]
        python tools/record_verdict.py A-002 --status excluded --reason "..."
"""
import argparse
import sys

import repo


def main() -> int:
    ap = argparse.ArgumentParser(description="Persist a filter verdict.")
    ap.add_argument("article_id")
    ap.add_argument("--status", required=True, choices=["included", "excluded"])
    ap.add_argument("--reason", required=True)
    ap.add_argument("--summary", help="newsletter summary — included articles")
    args = ap.parse_args()

    if not repo.exists("article", args.article_id):
        print(f"REFUSED: no article '{args.article_id}'")
        return 1
    if not args.reason.strip():
        print("REFUSED: an empty reason is not a reason")
        return 1
    article = repo.load("article", args.article_id)
    article["status"] = args.status
    article["filter_reason"] = args.reason.strip()
    if args.summary:
        article["summary"] = args.summary.strip()
    repo.save("article", article)
    print(f"OK {args.article_id} is {args.status}: {args.reason.strip()[:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
