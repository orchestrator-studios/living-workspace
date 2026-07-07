#!/usr/bin/env python3
"""Record a screening decision against the brief's criteria.

Usage:
  python tools/screen.py --source S-006 --decision included \
      --criterion "HF population; RPM intervention; readmission outcome; pragmatic RCT" \
      --date 2026-07-04
  python tools/screen.py --source S-009 --decision excluded \
      --criterion "exclusion: no outcome of interest" \
      --reason "Device accuracy only; no outcome of interest" --date 2026-07-04

Enforces (see skills/screening.md): decisions record the criterion; exclusions record the
reason; a decided source is frozen — re-screening is refused.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--decision", required=True, choices=["included", "excluded"])
    ap.add_argument("--criterion", required=True)
    ap.add_argument("--reason")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    path = ROOT / "data/sources" / f"{args.source}.json"
    if not path.exists():
        print(f"REFUSED: source {args.source} does not exist.")
        return 1
    record = json.loads(path.read_text(encoding="utf-8"))
    if record["screening"]["status"] != "unscreened":
        print(f"REFUSED: {args.source} is already {record['screening']['status']} — "
              "screening decisions are frozen. Revisions happen as a new versioned pass.")
        return 1
    if args.decision == "excluded" and not args.reason:
        print("REFUSED: exclusions must record a reason.")
        return 1

    record["screening"] = {"status": args.decision, "criterion": args.criterion,
                           "date": args.date}
    if args.reason:
        record["screening"]["reason"] = args.reason
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"{args.source} {args.decision} ({args.criterion}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
