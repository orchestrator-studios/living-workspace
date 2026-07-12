#!/usr/bin/env python3
"""log.py — record progress on an action (grown). The write path for OVERVIEW
rule 3: when something happens — a call, a discovery, a blocker — it lands here
as a dated log entry, not in the conversation. The record, not the chat, is the
memory.

Usage:  python tools/log.py <action-id> "called 7/10 — need the title first"
                            [--date YYYY-MM-DD] [--follow-up YYYY-MM-DD | --clear-follow-up]

--follow-up moves (or sets) when the action resurfaces; --clear-follow-up removes
it, leaving staleness-from-log as the only signal. Prints "OK ..." or
"REFUSED: ..." (exit 1).
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
    ap = argparse.ArgumentParser(description="Append a dated progress note to an action.")
    ap.add_argument("action_id")
    ap.add_argument("note")
    ap.add_argument("--date", default=str(datetime.date.today()),
                    help="YYYY-MM-DD (default: today)")
    ap.add_argument("--follow-up", dest="follow_up",
                    help="YYYY-MM-DD — set or move the resurface date")
    ap.add_argument("--clear-follow-up", action="store_true", dest="clear_follow_up")
    args = ap.parse_args()

    if args.follow_up and args.clear_follow_up:
        return refuse("--follow-up and --clear-follow-up are contradictory")
    if not repo.exists("action", args.action_id):
        return refuse(f"no action '{args.action_id}'")
    action = repo.load("action", args.action_id)
    if action["status"] == "done":
        return refuse(f"{args.action_id} is done — progress belongs on an open action "
                      f"(add a new one: python tools/add_action.py {action['project_id']} \"...\")")

    action["log"].append({"date": args.date, "note": args.note})
    moved = ""
    if args.follow_up:
        action["follow_up"] = args.follow_up
        moved = f"; follow-up → {args.follow_up}"
    elif args.clear_follow_up and action.pop("follow_up", None):
        moved = "; follow-up cleared"
    repo.save("action", action)
    print(f"OK {args.action_id} — logged {args.date}{moved}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
