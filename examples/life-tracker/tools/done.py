#!/usr/bin/env python3
"""done.py — complete an action or a project (grown). The write path for OVERVIEW
rule 4: done is dated — history is data.

Takes either id form and does the right thing:
  - A-#### : marks the action done (optionally logging a final note), then reports
    whether its project just stalled (rule 2) or looks finished
  - P-###  : marks the project done — REFUSED while it still has open actions;
    complete or close those first (a closing note explains why, e.g.
    "obsolete — project closed")

Usage:  python tools/done.py <A-#### | P-###> [--date YYYY-MM-DD] [--note "how it ended"]

Prints "OK ..." or "REFUSED: ..." (exit 1). Validate after a batch:
python tools/validate.py.
"""
import argparse
import datetime
import sys

import repo

# Keep prints safe on Windows consoles whose codepage can't encode the arrows
# and dashes these messages use.
sys.stdout.reconfigure(encoding="utf-8")


def refuse(msg):
    print(f"REFUSED: {msg}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Complete an action or a project, dated.")
    ap.add_argument("rid", help="A-#### or P-###")
    ap.add_argument("--date", default=str(datetime.date.today()),
                    help="YYYY-MM-DD (default: today)")
    ap.add_argument("--note", help="final log entry (actions only)")
    args = ap.parse_args()

    kind = "action" if args.rid.startswith("A-") else \
           "project" if args.rid.startswith("P-") else None
    if not kind:
        return refuse(f"'{args.rid}' is neither an action (A-####) nor a project (P-###)")
    if not repo.exists(kind, args.rid):
        return refuse(f"no {kind} '{args.rid}'")
    record = repo.load(kind, args.rid)
    if record["status"] == "done":
        return refuse(f"{args.rid} is already done ({record['done']})")

    if kind == "project":
        open_actions = [a for a in repo.load_all("action")
                        if a["project_id"] == args.rid and a["status"] == "open"]
        if open_actions:
            listing = "; ".join(f"{a['id']} {a['description']}" for a in open_actions)
            return refuse(f"{args.rid} still has open action(s): {listing} — "
                          f"complete or close them first (python tools/done.py A-#### "
                          f"--note \"obsolete — project closed\")")
        record["status"] = "done"
        record["done"] = args.date
        repo.save("project", record)
        print(f"OK {args.rid} — {record['title']} done {args.date}")
        return 0

    if args.note:
        record["log"].append({"date": args.date, "note": args.note})
    record["status"] = "done"
    record["done"] = args.date
    repo.save("action", record)
    project = repo.load("project", record["project_id"])
    print(f"OK {args.rid} — done {args.date} ({record['description']})")
    remaining = [a for a in repo.load_all("action")
                 if a["project_id"] == project["id"] and a["status"] == "open"]
    if not remaining and project["status"] == "open":
        print(f"   {project['id']} {project['title']} is now stalled — decide the next "
              f"action (python tools/add_action.py {project['id']} \"...\"), or if the "
              f"outcome is reached: python tools/done.py {project['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
