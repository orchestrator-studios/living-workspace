#!/usr/bin/env python3
"""archive_session.py — set a session aside, or bring it back (grown).

Archiving is workspace-owned state about a bound session: we can't write to the
transcript in ~/.claude, so the archived bit lives in a contained record here, and its
mere existence means archived. The rule lives once in repo.archive / repo.unarchive; this
CLI and the dashboard's POST /action/archive both call it. The board reflects it live.

Usage:  python tools/archive_session.py <session_id> [--reason "..."]   # archive
        python tools/archive_session.py <session_id> --undo             # unarchive
"""
import argparse
import sys

import repo


def main() -> int:
    ap = argparse.ArgumentParser(description="Archive or unarchive a session.")
    ap.add_argument("session_id")
    ap.add_argument("--reason", help="optional note on why")
    ap.add_argument("--undo", action="store_true", help="unarchive (remove the record)")
    args = ap.parse_args()

    result = (repo.unarchive(args.session_id) if args.undo
              else repo.archive(args.session_id, reason=args.reason))
    if not result.get("ok"):
        print(f"REFUSED: {result.get('error')}")
        return 1
    print(f"OK {args.session_id} {'unarchived' if args.undo else 'archived'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
