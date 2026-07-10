#!/usr/bin/env python3
"""export_csv.py — render one table as a CSV file (grown). The static view.

The export is a projection: assembled from the same named query the live board renders
(repo.table), never hand-written, regenerated after any change. It never opens data/
itself — rule 8, one door to the record.

Columns come from the table's definition, in declared order. A null value exports as an
empty cell — an honest unknown, not a guess. With --provenance, each column is followed
by a "<label> (source)" column, so the export carries what the board shows on hover.

Usage:  python tools/export_csv.py T-001 [--provenance] [--out path.csv]
"""
import argparse
import csv
import sys

import repo


def main() -> int:
    ap = argparse.ArgumentParser(description="Export one table as CSV.")
    ap.add_argument("table_id")
    ap.add_argument("--provenance", action="store_true",
                    help="include a source column after each value column")
    ap.add_argument("--out", help="output path (default: <table-name>.csv at the root)")
    args = ap.parse_args()

    answer = repo.table(table_id=args.table_id)
    if "error" in answer:
        print(f"REFUSED: {answer['error']}")
        return 1
    table, rows = answer["table"], answer["rows"]
    columns = table["columns"]

    slug = "".join(ch if ch.isalnum() else "-" for ch in table["name"].lower()).strip("-")
    out = repo.ROOT / (args.out or f"{slug}.csv")

    header = []
    for column in columns:
        header.append(column["label"])
        if args.provenance:
            header.append(f"{column['label']} (source)")
    header.append("researched")

    with open(out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            line = []
            for column in columns:
                value = row["values"].get(column["key"])
                line.append("" if value is None else value)
                if args.provenance:
                    line.append(row["provenance"].get(column["key"], ""))
            line.append(row.get("researched", ""))
            writer.writerow(line)

    print(f"Wrote {out.name} — {len(rows)} rows x {len(columns)} columns"
          f"{' with provenance' if args.provenance else ''}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
