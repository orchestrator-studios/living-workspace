#!/usr/bin/env python3
"""Create an invoice for a client from their unbilled time.

Usage:
  python tools/make_invoice.py --client CL-001 --date 2026-07-04

Enforces (see skills/invoicing.md):
- Draws ONLY unbilled time entries for the client's projects.
- Refuses to run if the client has no unbilled time.
- Marks every drawn entry billed and stamps it with the invoice id, so the
  same hour can never be invoiced twice.
- Invoice ids are INV-<year>-<seq>, sequential within the year.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (invoice date)")
    args = ap.parse_args()

    client_path = ROOT / "data/clients" / f"{args.client}.json"
    if not client_path.exists():
        print(f"REFUSED: client {args.client} does not exist.")
        return 1

    projects = {p.stem: load(p) for p in (ROOT / "data/projects").glob("*.json")
                if load(p)["client_id"] == args.client}
    if not projects:
        print(f"REFUSED: client {args.client} has no projects.")
        return 1

    drawn = []
    for te_path in sorted((ROOT / "data/time").glob("TE-*.json")):
        te = load(te_path)
        if te["project_id"] in projects and not te["billed"]:
            drawn.append((te_path, te))
    if not drawn:
        print(f"REFUSED: client {args.client} has no unbilled time.")
        return 1

    year = args.date[:4]
    inv_dir = ROOT / "data/invoices"
    inv_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(inv_dir.glob(f"INV-{year}-*.json"))
    next_n = (int(existing[-1].stem.split("-")[2]) + 1) if existing else 1
    inv_id = f"INV-{year}-{next_n:03d}"

    line_items = []
    for _, te in drawn:
        rate = projects[te["project_id"]]["rate"]
        line_items.append({
            "time_entry_id": te["id"],
            "project_id": te["project_id"],
            "date": te["date"],
            "hours": te["hours"],
            "rate": rate,
            "amount": round(te["hours"] * rate, 2),
        })
    invoice = {
        "id": inv_id,
        "client_id": args.client,
        "date": args.date,
        "line_items": line_items,
        "total": round(sum(li["amount"] for li in line_items), 2),
        "currency": "USD",
        "status": "draft",
    }
    save(inv_dir / f"{inv_id}.json", invoice)

    for te_path, te in drawn:
        te["billed"] = True
        te["invoice_id"] = inv_id
        save(te_path, te)

    print(f"Created {inv_id} for {args.client}: "
          f"{len(line_items)} line items, total ${invoice['total']:,.2f}. "
          f"{len(drawn)} time entries marked billed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
