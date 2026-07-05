#!/usr/bin/env python3
"""Log a time entry against a project.

Usage:
  python tools/add_time.py --project PR-001 --date 2026-07-03 --hours 1.5 \
      --description "What the time was spent on"

Enforces (see skills/time-tracking.md): the project must exist and be active;
hours in 0.25 increments; the new record must validate before it is kept.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--hours", required=True, type=float)
    ap.add_argument("--description", required=True)
    args = ap.parse_args()

    project_path = ROOT / "data/projects" / f"{args.project}.json"
    if not project_path.exists():
        print(f"REFUSED: project {args.project} does not exist.")
        return 1
    project = json.loads(project_path.read_text(encoding="utf-8"))
    if project["status"] != "active":
        print(f"REFUSED: project {args.project} is {project['status']}, not active.")
        return 1

    time_dir = ROOT / "data/time"
    time_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(time_dir.glob("TE-*.json"))
    next_n = (int(existing[-1].stem.split("-")[1]) + 1) if existing else 1
    new_id = f"TE-{next_n:04d}"

    record = {
        "id": new_id,
        "project_id": args.project,
        "date": args.date,
        "hours": args.hours,
        "description": args.description,
        "billed": False,
        "invoice_id": None,
    }
    out = time_dir / f"{new_id}.json"
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    result = subprocess.run([sys.executable, str(ROOT / "tools/validate.py")],
                            capture_output=True, text=True)
    if result.returncode != 0:
        out.unlink()
        print("REFUSED: record failed validation and was not kept.")
        print(result.stdout)
        return 1
    print(f"Logged {new_id}: {args.hours}h on {args.project} ({args.date}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
