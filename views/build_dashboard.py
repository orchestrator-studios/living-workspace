#!/usr/bin/env python3
"""Generate views/dashboard.html — a self-contained practice dashboard.

Reads data/, writes a static HTML file. Regenerate after any data change:
    python views/build_dashboard.py
Open the result directly in a browser (no server needed).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "views" / "dashboard.html"


def load_all(subdir):
    folder = ROOT / "data" / subdir
    if not folder.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(folder.glob("*.json"))]


def main() -> int:
    clients = {c["id"]: c for c in load_all("clients")}
    projects = {p["id"]: p for p in load_all("projects")}
    time_entries = load_all("time")
    invoices = load_all("invoices")

    unbilled = [te for te in time_entries if not te["billed"]]
    unbilled_hours = sum(te["hours"] for te in unbilled)
    unbilled_value = sum(te["hours"] * projects[te["project_id"]]["rate"] for te in unbilled)
    active_projects = sum(1 for p in projects.values() if p["status"] == "active")

    by_client = {}
    for te in unbilled:
        cid = projects[te["project_id"]]["client_id"]
        by_client[cid] = by_client.get(cid, 0.0) + te["hours"] * projects[te["project_id"]]["rate"]
    max_value = max(by_client.values(), default=1.0)

    bars = ""
    for cid, value in sorted(by_client.items(), key=lambda kv: -kv[1]):
        pct = max(2.0, 100.0 * value / max_value)
        bars += (
            f'<div class="bar-row" title="{clients[cid]["name"]}: ${value:,.2f} unbilled">'
            f'<span class="bar-label">{clients[cid]["name"]}</span>'
            f'<span class="bar-track"><span class="bar" style="width:{pct:.1f}%"></span></span>'
            f'<span class="bar-value">${value:,.0f}</span></div>\n'
        )
    if not by_client:
        bars = '<p class="empty">No unbilled time — everything is invoiced.</p>'

    recent = sorted(time_entries, key=lambda te: (te["date"], te["id"]), reverse=True)[:8]
    rows = ""
    for te in recent:
        pr = projects[te["project_id"]]
        state = te["invoice_id"] if te["billed"] else "unbilled"
        rows += (
            f'<tr><td>{te["date"]}</td><td>{pr["name"]}</td>'
            f'<td class="num">{te["hours"]:.2f}</td>'
            f'<td>{te["description"]}</td><td class="state">{state}</td></tr>\n'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Practice Dashboard</title>
<style>
  :root {{
    --surface: #fcfcfb; --card: #ffffff; --border: #e4e3de;
    --ink: #1c1c1a; --ink-2: #5f5e57; --bar: #2a78d6; --track: #f0efec;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --surface: #1a1a19; --card: #232322; --border: #383835;
      --ink: #ffffff; --ink-2: #c3c2b7; --bar: #3987e5; --track: #2c2c2a;
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font: 15px/1.5 system-ui, sans-serif; background: var(--surface);
         color: var(--ink); padding: 32px 24px; }}
  .wrap {{ max-width: 860px; margin: 0 auto; }}
  h1 {{ font-size: 1.3rem; margin-bottom: 2px; }}
  .sub {{ color: var(--ink-2); font-size: 0.85rem; margin-bottom: 28px; }}
  .tiles {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
            margin-bottom: 28px; }}
  .tile {{ background: var(--card); border: 1px solid var(--border);
           border-radius: 10px; padding: 16px 18px; }}
  .tile .label {{ font-size: 0.78rem; color: var(--ink-2);
                  text-transform: uppercase; letter-spacing: 0.05em; }}
  .tile .value {{ font-size: 1.7rem; font-weight: 650; margin-top: 2px;
                  font-variant-numeric: tabular-nums; }}
  .tile .ctx {{ font-size: 0.8rem; color: var(--ink-2); }}
  .card {{ background: var(--card); border: 1px solid var(--border);
           border-radius: 10px; padding: 18px 20px; margin-bottom: 28px; }}
  .card h2 {{ font-size: 0.95rem; margin-bottom: 14px; }}
  .bar-row {{ display: grid; grid-template-columns: 190px 1fr 84px; gap: 10px;
              align-items: center; margin-bottom: 2px; padding: 4px 0; }}
  .bar-row:hover .bar {{ filter: brightness(1.12); }}
  .bar-label {{ font-size: 0.86rem; color: var(--ink); overflow: hidden;
                text-overflow: ellipsis; white-space: nowrap; }}
  .bar-track {{ display: block; background: var(--track); border-radius: 0 4px 4px 0;
                height: 18px; }}
  .bar {{ display: block; height: 100%; background: var(--bar);
          border-radius: 0 4px 4px 0; }}
  .bar-value {{ font-size: 0.86rem; text-align: right; color: var(--ink);
                font-variant-numeric: tabular-nums; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.86rem; }}
  th {{ text-align: left; color: var(--ink-2); font-weight: 600; padding: 6px 10px;
        border-bottom: 1px solid var(--border); }}
  td {{ padding: 7px 10px; border-bottom: 1px solid var(--border);
        vertical-align: top; }}
  tr:hover td {{ background: var(--track); }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  td.state {{ color: var(--ink-2); white-space: nowrap; }}
  .empty {{ color: var(--ink-2); font-size: 0.9rem; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Practice Dashboard</h1>
  <p class="sub">Generated from <code>data/</code> by <code>views/build_dashboard.py</code> —
    regenerate after any data change.</p>

  <div class="tiles">
    <div class="tile"><div class="label">Unbilled hours</div>
      <div class="value">{unbilled_hours:.2f}</div>
      <div class="ctx">across {len(unbilled)} entries</div></div>
    <div class="tile"><div class="label">Unbilled value</div>
      <div class="value">${unbilled_value:,.0f}</div>
      <div class="ctx">at project rates</div></div>
    <div class="tile"><div class="label">Active projects</div>
      <div class="value">{active_projects}</div>
      <div class="ctx">{len(clients)} clients &middot; {len(invoices)} invoices</div></div>
  </div>

  <div class="card">
    <h2>Unbilled value by client</h2>
    {bars}
  </div>

  <div class="card">
    <h2>Recent time</h2>
    <table>
      <tr><th>Date</th><th>Project</th><th style="text-align:right">Hours</th>
          <th>Description</th><th>Invoice</th></tr>
      {rows}
    </table>
  </div>
</div>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} — "
          f"{unbilled_hours:.2f} unbilled hrs, ${unbilled_value:,.2f} across "
          f"{len(by_client)} client(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
