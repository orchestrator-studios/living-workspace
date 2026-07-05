#!/usr/bin/env python3
"""Answer the recurring questions from the data.

Usage:
  python tools/report.py unbilled     # unbilled hours and value, by client
  python tools/report.py projects    # project summary with hours to date
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_all(subdir):
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((ROOT / "data" / subdir).glob("*.json"))]


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "unbilled"
    clients = {c["id"]: c for c in load_all("clients")}
    projects = {p["id"]: p for p in load_all("projects")}
    time_entries = load_all("time")

    if mode == "unbilled":
        by_client = {}
        for te in time_entries:
            if te["billed"]:
                continue
            pr = projects[te["project_id"]]
            row = by_client.setdefault(pr["client_id"], {"hours": 0.0, "value": 0.0})
            row["hours"] += te["hours"]
            row["value"] += te["hours"] * pr["rate"]
        if not by_client:
            print("No unbilled time.")
            return 0
        print(f"{'Client':<28}{'Unbilled hrs':>14}{'Value (USD)':>14}")
        for cid, row in sorted(by_client.items()):
            print(f"{clients[cid]['name']:<28}{row['hours']:>14.2f}{row['value']:>14,.2f}")
        return 0

    if mode == "projects":
        print(f"{'Project':<32}{'Client':<28}{'Status':<11}{'Hours':>7}")
        for pid, pr in sorted(projects.items()):
            hours = sum(te["hours"] for te in time_entries if te["project_id"] == pid)
            print(f"{pr['name']:<32}{clients[pr['client_id']]['name']:<28}"
                  f"{pr['status']:<11}{hours:>7.2f}")
        return 0

    print(f"Unknown report '{mode}'. Try: unbilled | projects")
    return 1


if __name__ == "__main__":
    sys.exit(main())
