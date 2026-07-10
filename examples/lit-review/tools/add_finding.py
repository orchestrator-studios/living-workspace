#!/usr/bin/env python3
"""Extract a finding from an INCLUDED source. This tool is the report's integrity guarantee:
it refuses any source that is not screened in, so nothing downstream can cite an excluded
or unscreened paper.

Usage:
  python tools/add_finding.py --source S-006 --outcome readmission --direction reduction \
      --claim "..." --evidence "n=1,022; 14.9% vs 19.6%; p=0.01" [--theme T-01]
"""
import argparse
import sys

import repo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--claim", required=True)
    ap.add_argument("--outcome", required=True,
                    choices=["readmission", "mortality", "adherence", "cost"])
    ap.add_argument("--direction", required=True,
                    choices=["reduction", "no_effect", "increase", "mixed"])
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--theme", default=None)
    args = ap.parse_args()

    if not repo.exists("sources", args.source):
        print(f"REFUSED: source {args.source} does not exist.")
        return 1
    src = repo.load("sources", args.source)
    status = src["screening"]["status"]
    if status != "included":
        detail = src["screening"].get("reason", "not yet screened")
        print(f"REFUSED: source {args.source} is {status} ({detail}). "
              "Findings may only cite included sources.")
        return 1
    if args.theme and not repo.exists("themes", args.theme):
        print(f"REFUSED: theme {args.theme} does not exist.")
        return 1

    new_id = repo.next_id("findings")
    record = {"id": new_id, "source_id": args.source, "claim": args.claim,
              "outcome": args.outcome, "direction": args.direction,
              "evidence": args.evidence, "theme_id": args.theme}
    repo.save("findings", record)
    print(f"Extracted {new_id} from {args.source} ({args.outcome}: {args.direction}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
