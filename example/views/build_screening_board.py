#!/usr/bin/env python3
"""Generate views/screening_board.html — the review at a glance.

Reads data/, writes a static self-contained HTML file. Regenerate after any change:
    python views/build_screening_board.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "views" / "screening_board.html"


def load_all(subdir):
    folder = ROOT / "data" / subdir
    if not folder.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(folder.glob("*.json"))]


def card(s):
    authors = s["authors"][0] + (" et al." if len(s["authors"]) > 1 else "")
    meta = f"{authors} · {s['year']} · via {s['found_via']}"
    reason = ""
    scr = s["screening"]
    if scr.get("criterion"):
        detail = scr.get("reason") or scr["criterion"]
        reason = f'<div class="why">{detail}</div>'
    return (f'<div class="card"><div class="sid">{s["id"]}</div>'
            f'<div class="ttl">{s["title"]}</div>'
            f'<div class="meta">{meta}</div>{reason}</div>')


def main() -> int:
    sources = load_all("sources")
    findings = load_all("findings")
    cols = {"unscreened": [], "included": [], "excluded": []}
    for s in sources:
        cols[s["screening"]["status"]].append(s)

    col_html = ""
    for status in ("unscreened", "included", "excluded"):
        cards = "\n".join(card(s) for s in cols[status]) or '<p class="empty">none</p>'
        col_html += (f'<section class="col"><h2>{status} '
                     f'<span class="count">{len(cols[status])}</span></h2>{cards}</section>\n')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Screening Board</title>
<style>
  :root {{
    --surface: #fcfcfb; --card: #ffffff; --border: #e4e3de;
    --ink: #1c1c1a; --ink-2: #5f5e57; --track: #f0efec; --accent: #2a78d6;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --surface: #1a1a19; --card: #232322; --border: #383835;
      --ink: #ffffff; --ink-2: #c3c2b7; --track: #2c2c2a; --accent: #3987e5;
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font: 14px/1.5 system-ui, sans-serif; background: var(--surface);
         color: var(--ink); padding: 28px 22px; }}
  .wrap {{ max-width: 1080px; margin: 0 auto; }}
  h1 {{ font-size: 1.25rem; margin-bottom: 2px; }}
  .sub {{ color: var(--ink-2); font-size: 0.84rem; margin-bottom: 22px; }}
  .board {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
  .col {{ background: var(--track); border-radius: 10px; padding: 12px; }}
  .col h2 {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em;
             color: var(--ink-2); margin: 2px 4px 10px; }}
  .count {{ float: right; background: var(--card); border: 1px solid var(--border);
            border-radius: 999px; padding: 0 8px; font-size: 0.75rem; color: var(--ink); }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px;
           padding: 10px 12px; margin-bottom: 8px; }}
  .sid {{ font-family: ui-monospace, Consolas, monospace; font-size: 0.7rem;
          color: var(--accent); font-weight: 700; }}
  .ttl {{ font-size: 0.84rem; font-weight: 600; line-height: 1.35; margin: 2px 0 4px; }}
  .meta {{ font-size: 0.72rem; color: var(--ink-2); }}
  .why {{ font-size: 0.72rem; color: var(--ink-2); border-top: 1px solid var(--border);
          margin-top: 6px; padding-top: 5px; font-style: italic; }}
  .empty {{ color: var(--ink-2); font-size: 0.8rem; padding: 4px; }}
  @media (max-width: 760px) {{ .board {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Screening Board</h1>
  <p class="sub">{len(sources)} sources · {len(findings)} findings extracted ·
    generated from <code>data/</code> by <code>views/build_screening_board.py</code></p>
  <div class="board">
{col_html}
  </div>
</div>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote views/screening_board.html — "
          f"{len(cols['unscreened'])} unscreened · {len(cols['included'])} included · "
          f"{len(cols['excluded'])} excluded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
