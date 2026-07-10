#!/usr/bin/env python3
"""add_row.py — add one row to a table (grown). The populate/enrich write path.

Carries the rules a free-form edit would skip (OVERVIEW rules 2–5):
  - the table must exist; value keys must be its column keys
  - every value must conform to its column's type (repo.column_violation — the
    type rule's single definition); required columns must be non-null
  - every non-null value must carry provenance (a source URL or stated basis)
  - dedup: REFUSED if the table already holds a row with the same values on
    every required column (case-insensitive for strings)

Usage:  python tools/add_row.py <table-id> [--file row.json]     (default: stdin)
        row.json = {"values": {...}, "provenance": {...}, "researched": "YYYY-MM-DD"}

Prints "OK <id> — ..." or "REFUSED: ..." (exit 1). Validate after a batch:
python tools/validate.py.
"""
import argparse
import json
import sys

import repo


def refuse(msg):
    print(f"REFUSED: {msg}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Add one row to a table.")
    ap.add_argument("table_id")
    ap.add_argument("--file", help="JSON file with values/provenance/researched "
                                   "(default: read stdin)")
    args = ap.parse_args()

    if not repo.exists("table", args.table_id):
        return refuse(f"no table '{args.table_id}'")
    table = repo.load("table", args.table_id)
    columns = {c["key"]: c for c in table["columns"]}

    raw = open(args.file, encoding="utf-8-sig").read() if args.file else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except ValueError as err:
        return refuse(f"input is not valid JSON: {err}")
    values = payload.get("values", {})
    provenance = payload.get("provenance", {})
    researched = payload.get("researched", "")

    for key in list(values) + list(provenance):
        if key not in columns:
            return refuse(f"'{key}' is not a column of {args.table_id}")
    for key, value in values.items():
        complaint = repo.column_violation(value, columns[key])
        if complaint:
            return refuse(f"values.{key}: {complaint}")
        if value is not None and not provenance.get(key):
            return refuse(f"values.{key} has no provenance — every researched value "
                          f"carries its source")
    for col in table["columns"]:
        if col.get("required") and values.get(col["key"]) is None:
            return refuse(f"values.{col['key']}: required by {args.table_id}")

    required = [c["key"] for c in table["columns"] if c.get("required")]

    def fingerprint(vals):
        return tuple(str(vals.get(k, "")).strip().lower() for k in required)

    for other in repo.load_all("row"):
        if other["table_id"] == args.table_id and fingerprint(other["values"]) == fingerprint(values):
            return refuse(f"duplicate of {other['id']} "
                          f"({', '.join(f'{k}={values.get(k)!r}' for k in required)})")

    rid = repo.next_id("row")
    repo.save("row", {"id": rid, "table_id": args.table_id, "values": values,
                      "provenance": provenance, "researched": researched})
    name_key = required[0] if required else next(iter(columns))
    print(f"OK {rid} — {values.get(name_key)} added to {args.table_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
