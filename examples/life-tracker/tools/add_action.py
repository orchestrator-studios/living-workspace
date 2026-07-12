#!/usr/bin/env python3
"""add_action.py — add one concrete next step to a project (grown). The capture
write path for steps; un-stalls a project.

Carries the rules a free-form edit would skip (OVERVIEW rules 1, 2):
  - the project must exist and not be done (reopen it, or capture a new project)
  - dedup: REFUSED if the project already holds an open action with the same
    description (case-insensitive)

Usage:  python tools/add_action.py <project-id> "call the DMV about form X"
                                   [--follow-up YYYY-MM-DD] [--note "context"]
                                   [--created YYYY-MM-DD]

--note lands as the first dated log entry. Prints "OK <id> — ..." or
"REFUSED: ..." (exit 1). Validate after a batch: python tools/validate.py.
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
    ap = argparse.ArgumentParser(description="Add one action to a project.")
    ap.add_argument("project_id")
    ap.add_argument("description")
    ap.add_argument("--follow-up", dest="follow_up",
                    help="YYYY-MM-DD — when this should resurface if nothing has happened")
    ap.add_argument("--note", help="initial context, lands as the first log entry")
    ap.add_argument("--created", default=str(datetime.date.today()),
                    help="YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    if not repo.exists("project", args.project_id):
        return refuse(f"no project '{args.project_id}'")
    project = repo.load("project", args.project_id)
    if project["status"] == "done":
        return refuse(f"{args.project_id} is done — reopen it or capture a new project")

    for other in repo.load_all("action"):
        if (other["project_id"] == args.project_id and other["status"] == "open"
                and other["description"].strip().lower() == args.description.strip().lower()):
            return refuse(f"duplicate of open action {other['id']}")

    record = {"id": repo.next_id("action"), "project_id": args.project_id,
              "description": args.description, "status": "open",
              "created": args.created, "log": []}
    if args.follow_up:
        record["follow_up"] = args.follow_up
    if args.note:
        record["log"].append({"date": args.created, "note": args.note})
    repo.save("action", record)
    print(f"OK {record['id']} — {args.description} → {args.project_id} {project['title']}"
          + (f" (follow up {args.follow_up})" if args.follow_up else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
