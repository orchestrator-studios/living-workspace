#!/usr/bin/env python3
"""finalize_issue.py — freeze an issue (grown). The user's gate, made durable: only a
person decides an issue is done, and after this, done means done.

REFUSED if the issue has no assembled body, or if candidates in its window still await
a verdict (screen them, or pass --allow-pending to ship without the stragglers). Once
final: tools/assemble_issue.py refuses to re-render it, and re-runs of the pipeline
cannot touch it — what subscribers received is a fact, not a draft.

Usage:  python tools/finalize_issue.py N-001 [--allow-pending]
"""
import argparse
import sys

import repo


def main() -> int:
    ap = argparse.ArgumentParser(description="Freeze an issue as final.")
    ap.add_argument("issue_id")
    ap.add_argument("--allow-pending", action="store_true",
                    help="finalize even with unscreened candidates in the window")
    args = ap.parse_args()

    if not repo.exists("issue", args.issue_id):
        print(f"REFUSED: no issue '{args.issue_id}'")
        return 1
    issue = repo.load("issue", args.issue_id)
    if issue["status"] == "final":
        print(f"REFUSED: {issue['id']} is already final — final is frozen")
        return 1
    if not (issue.get("body") or "").strip():
        print(f"REFUSED: {issue['id']} has no assembled body — "
              f"run tools/assemble_issue.py {issue['id']} first")
        return 1

    pending = [a["id"] for a in repo.window_articles(issue["week_start"], issue["week_end"])
               if a["status"] == "candidate"]
    if pending and not args.allow_pending:
        print(f"REFUSED: {len(pending)} candidate(s) in this window still await a "
              f"verdict ({', '.join(pending)}) — screen them, or --allow-pending")
        return 1

    issue["status"] = "final"
    repo.save("issue", issue)
    print(f"OK {issue['id']} is final — frozen: re-assembly now refuses; the body on "
          f"the record is the sent truth. Export a copy of it anytime: "
          f"python tools/assemble_issue.py {issue['id']} --export <path>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
