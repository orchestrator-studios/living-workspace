#!/usr/bin/env python3
"""add_project.py — add one project to an area (grown). The capture write path for
outcomes.

Carries the rules a free-form edit would skip (OVERVIEW rules 1, 2):
  - the area must exist (everything hangs on the tree)
  - dedup: REFUSED if the area already holds a non-done project with the same
    title (case-insensitive)
  - reminds you that a new open project is stalled until it has a next action

Usage:  python tools/add_project.py <area-id> "title" --done-when "what done looks like"
                                    [--status open|someday] [--created YYYY-MM-DD]

Prints "OK <id> — ..." or "REFUSED: ..." (exit 1). Validate after a batch:
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
    ap = argparse.ArgumentParser(description="Add one project to an area.")
    ap.add_argument("area_id")
    ap.add_argument("title")
    ap.add_argument("--done-when", required=True, dest="done_when",
                    help="a plain statement of what done looks like")
    ap.add_argument("--status", choices=["open", "someday"], default="open")
    ap.add_argument("--created", default=str(datetime.date.today()),
                    help="YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    if not repo.exists("area", args.area_id):
        areas = ", ".join(f"{a['id']} {a['name']}" for a in repo.load_all("area"))
        return refuse(f"no area '{args.area_id}' — areas: {areas or 'none yet'}")
    area = repo.load("area", args.area_id)

    for other in repo.load_all("project"):
        if (other["area_id"] == args.area_id and other["status"] != "done"
                and other["title"].strip().lower() == args.title.strip().lower()):
            return refuse(f"duplicate of {other['id']} ({other['status']}) in {area['name']}")

    pid = repo.next_id("project")
    repo.save("project", {"id": pid, "area_id": args.area_id, "title": args.title,
                          "done_looks_like": args.done_when, "status": args.status,
                          "created": args.created})
    print(f"OK {pid} — {args.title} ({area['name']}, {args.status})")
    if args.status == "open":
        print(f"   stalled until it has a next action: "
              f"python tools/add_action.py {pid} \"...\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
