#!/usr/bin/env python3
"""archive_session.py — set a session aside, or bring it back (grown).

Archiving is workspace-owned state about a bound session: we can't write to the
transcript in ~/.claude, so the archived bit lives in a contained record here, and its
mere existence means archived. This tool is the only writer; the read-only dashboard
just reflects and filters on it (the conversation is the interface — you ask to archive,
the board updates live).

Usage:  python tools/archive_session.py <session_id> [--reason "..."]   # archive
        python tools/archive_session.py <session_id> --undo             # unarchive
"""
import argparse
import sys
import time

import repo


def main() -> int:
    ap = argparse.ArgumentParser(description="Archive or unarchive a session.")
    ap.add_argument("session_id")
    ap.add_argument("--reason", help="optional note on why")
    ap.add_argument("--undo", action="store_true", help="unarchive (remove the record)")
    args = ap.parse_args()

    known = {repo.Path(f).stem for f in repo._session_files()}
    if args.session_id not in known:
        print(f"REFUSED: no session '{args.session_id}'")
        return 1

    if args.undo:
        path = repo.path_for("archive", args.session_id)
        if not path.exists():
            print(f"OK {args.session_id} was not archived — nothing to undo")
            return 0
        path.unlink()
        print(f"OK {args.session_id} unarchived")
        return 0

    if repo.exists("archive", args.session_id):
        print(f"OK {args.session_id} already archived")
        return 0
    repo.save("archive", {
        "id": args.session_id,
        "session_id": args.session_id,
        "archived_at": repo._iso(time.time()),
        "reason": args.reason,
    })
    print(f"OK {args.session_id} archived")
    return 0


if __name__ == "__main__":
    sys.exit(main())
