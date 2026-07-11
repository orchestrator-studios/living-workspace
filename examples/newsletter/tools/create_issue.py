#!/usr/bin/env python3
"""create_issue.py — open the next issue as a draft (grown). Stage 0 of the weekly
pipeline: the issue exists *before* retrieval, so the issues view tracks the run from
the first second and an interrupted run has an anchor.

Windows tile — the stream's coverage promise: the new window starts the day after the
previous issue's week_end (first issue: the trailing --days ending today) and ends
today. REFUSED if a draft is already open or the window would overlap an existing
issue; gap-free, overlap-free coverage is enforced here and checked in validate.py.

Usage:  python tools/create_issue.py [--title "..."] [--days 7]
"""
import argparse
import datetime
import sys

import repo


def main() -> int:
    ap = argparse.ArgumentParser(description="Open the next issue as a draft.")
    ap.add_argument("--title", help="default: AI News — <window>")
    ap.add_argument("--days", type=int, default=7,
                    help="first-issue window length (later issues tile)")
    args = ap.parse_args()

    issues = sorted(repo.load_all("issue"), key=lambda i: i["week_end"])
    draft = next((i for i in issues if i["status"] == "draft"), None)
    if draft:
        print(f"REFUSED: {draft['id']} is still a draft — one open issue at a time "
              f"(finalize it, or keep working in it)")
        return 1

    today = datetime.date.today()
    if issues:
        prev_end = datetime.date.fromisoformat(issues[-1]["week_end"])
        week_start = prev_end + datetime.timedelta(days=1)
        if week_start > today:
            print(f"REFUSED: coverage already runs through {prev_end} — "
                  f"nothing new to cover yet")
            return 1
    else:
        week_start = today - datetime.timedelta(days=args.days)

    issue_id = repo.next_id("issue")
    issue = {"id": issue_id,
             "title": args.title or f"AI News — {week_start} to {today}",
             "week_start": week_start.isoformat(), "week_end": today.isoformat(),
             "created": today.isoformat(), "articles": [],
             "executive_summary": None, "status": "draft", "body": None}
    repo.save("issue", issue)
    print(f"OK {issue_id} — draft open, window {issue['week_start']} to "
          f"{issue['week_end']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
