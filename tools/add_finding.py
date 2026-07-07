#!/usr/bin/env python3
"""Extract a finding from an INCLUDED source. This tool is the report's integrity guarantee:
it refuses any source that is not screened in, so nothing downstream can cite an excluded
or unscreened paper.

Usage:
  python tools/add_finding.py --source S-006 --outcome readmission --direction reduction \
      --claim "..." --evidence "n=1,022; 14.9% vs 19.6%; p=0.01" [--theme T-01]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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

    src_path = ROOT / "data/sources" / f"{args.source}.json"
    if not src_path.exists():
        print(f"REFUSED: source {args.source} does not exist.")
        return 1
    src = json.loads(src_path.read_text(encoding="utf-8"))
    status = src["screening"]["status"]
    if status != "included":
        detail = src["screening"].get("reason", "not yet screened")
        print(f"REFUSED: source {args.source} is {status} ({detail}). "
              "Findings may only cite included sources.")
        return 1
    if args.theme and not (ROOT / "data/themes" / f"{args.theme}.json").exists():
        print(f"REFUSED: theme {args.theme} does not exist.")
        return 1

    find_dir = ROOT / "data/findings"
    find_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(find_dir.glob("F-*.json"))
    next_n = (int(existing[-1].stem.split("-")[1]) + 1) if existing else 1
    new_id = f"F-{next_n:03d}"
    record = {"id": new_id, "source_id": args.source, "claim": args.claim,
              "outcome": args.outcome, "direction": args.direction,
              "evidence": args.evidence, "theme_id": args.theme}
    (find_dir / f"{new_id}.json").write_text(json.dumps(record, indent=2) + "\n",
                                             encoding="utf-8")
    print(f"Extracted {new_id} from {args.source} ({args.outcome}: {args.direction}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
