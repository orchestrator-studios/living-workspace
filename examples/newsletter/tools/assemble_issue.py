#!/usr/bin/env python3
"""assemble_issue.py — assemble one issue's newsletter body (grown). The newsletter is
data: membership and body are *derived* onto the issue record, never hand-edited.

Membership is computed, not curated by hand: the issue's stories are the **included**
articles landed by the runs covering its window, in id order — so assembly is the one
definition of "what's in this issue" (issue.articles is written here, from that
derivation). REFUSED if any included story lacks a summary (rule 3's closure, in
newsletter form) — and REFUSED entirely on a final issue: final is frozen. On a final
issue only --export works, copying the stored body untouched.

Regenerate after any change while draft. A file copy (--export) is for sending —
ephemeral, never the truth.

Usage:  python tools/assemble_issue.py N-001 [--exec-summary "..."] [--export PATH]
"""
import argparse
import sys
from pathlib import Path

import repo


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble one issue's newsletter body.")
    ap.add_argument("issue_id")
    ap.add_argument("--exec-summary", help="set the executive summary on the record")
    ap.add_argument("--export", metavar="PATH",
                    help="also write the body to PATH — an ephemeral copy for sending")
    args = ap.parse_args()

    if not repo.exists("issue", args.issue_id):
        print(f"REFUSED: no issue '{args.issue_id}'")
        return 1
    issue = repo.load("issue", args.issue_id)

    if issue["status"] == "final":
        if args.export and (issue.get("body") or "").strip():
            Path(args.export).write_text(issue["body"], encoding="utf-8")
            print(f"Exported {issue['id']} (final, untouched) to {args.export}")
            return 0
        print(f"REFUSED: {issue['id']} is final — frozen. (--export still copies "
              f"its stored body.)")
        return 1

    stories = [a for a in repo.window_articles(issue["week_start"], issue["week_end"])
               if a["status"] == "included"]
    for story in stories:
        if not (story.get("summary") or "").strip():
            print(f"REFUSED: {story['id']} is included but has no summary yet")
            return 1

    if args.exec_summary:
        issue["executive_summary"] = args.exec_summary.strip()

    lines = [f"# {issue['title']}", "",
             f"*Coverage: {issue['week_start']} to {issue['week_end']} · "
             f"{len(stories)} stories · issue {issue['id']} ({issue['status']})*", ""]
    if issue.get("executive_summary"):
        lines += ["## This week", "", issue["executive_summary"], ""]
    lines += ["## The stories", ""]
    for a in stories:
        source_bits = " · ".join(filter(None, [a["source_name"], a.get("published", "")]))
        lines += [f"### [{a['title']}]({a['url']})",
                  f"*{source_bits}*", "", a["summary"], ""]
    lines += ["---", "",
              "*Assembled by tools/assemble_issue.py from the workspace record — "
              "regenerate, don't edit.*", ""]

    issue["articles"] = [a["id"] for a in stories]
    issue["body"] = "\n".join(lines)
    repo.save("issue", issue)
    print(f"Assembled {issue['id']} — {len(stories)} stories, membership derived from "
          f"the window's runs, body stored on the record.")

    if args.export:
        Path(args.export).write_text(issue["body"], encoding="utf-8")
        print(f"Exported a copy to {args.export} — a snapshot for sending; the record "
              f"stays the truth.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
