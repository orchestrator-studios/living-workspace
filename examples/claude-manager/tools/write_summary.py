#!/usr/bin/env python3
"""write_summary.py — persist a session summary (grown). The write path for the
delegated summarizer (capabilities/summarize-session.md).

Carries the one rule the summary needs: the **watermark**. The summary is worthless to
the trigger algo without a record of *what it summarized*, so this tool — not the agent —
stamps `source_size` (and the mtime and turn count) from the live transcript at write
time. The agent supplies judgment (the text); the tool supplies the watermark, so
`repo.summaries_due()` can later tell whether the transcript has moved on.

One summary per session, keyed by the session uuid; writing again overwrites (a
resummary). Read-only toward ~/.claude; the only thing this workspace ever writes is here,
under data/summary/.

Usage:  python tools/write_summary.py <session_id> --text "..." [--model claude-...]
        echo "the summary" | python tools/write_summary.py <session_id> --stdin
"""
import argparse
import sys
import time
from pathlib import Path

import repo


def main() -> int:
    ap = argparse.ArgumentParser(description="Write or refresh a session's summary.")
    ap.add_argument("session_id")
    ap.add_argument("--text", help="the summary text (or use --stdin)")
    ap.add_argument("--stdin", action="store_true", help="read the summary text from stdin")
    ap.add_argument("--model", help="who wrote it, e.g. claude-fable-5")
    args = ap.parse_args()

    path = next((f for f in repo._session_files() if Path(f).stem == args.session_id), None)
    if path is None:
        print(f"REFUSED: no session '{args.session_id}'")
        return 1
    text = sys.stdin.read() if args.stdin else (args.text or "")
    text = " ".join(text.split())
    if not text:
        print("REFUSED: an empty summary is not a summary")
        return 1

    stat = __import__("os").stat(path)      # watermark from the live transcript, now
    detail = repo.session(args.session_id)  # turn count for context (exact, full parse)
    repo.save("summary", {
        "id": args.session_id,
        "session_id": args.session_id,
        "text": text,
        "generated_at": repo._iso(time.time()),
        "source_size": stat.st_size,
        "source_last_active": repo._iso(stat.st_mtime),
        "user_turns_at_gen": detail.get("user_turns"),
        "model": args.model,
    })
    print(f"OK summary for {args.session_id} ({detail.get('project')}) — "
          f"watermark {stat.st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
