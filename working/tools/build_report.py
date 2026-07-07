#!/usr/bin/env python
"""Render a review's interactive HTML report by binding its data into the shared template.

Separation of concerns:
- the presentation *logic* (the template) lives in `views/report.template.html`;
- the *code* that binds a review's data into it lives here in `tools/`;
- the rendered *instance* is written into the study folder: `data/reviews/<slug>/views/`.

Usage:
    python tools/build_report.py <slug> [--date YYYY-MM-DD]

Re-run after any data change. The output is a projection — never hand-edit it.
"""
import argparse
import json

import repo

TEMPLATE_PATH = repo.ROOT / "views" / "report.template.html"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--date", default="")
    args = ap.parse_args()

    review = repo.load_review(args.slug)
    protocol, records = review["protocol"], review["records"]
    date = args.date or (protocol.get("searches", [{}])[-1].get("date", ""))

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    blob = json.dumps(review, ensure_ascii=False).replace("</", "<\\/")
    html = (template
            .replace("__DATA__", blob)
            .replace("__SLUG__", args.slug)
            .replace("__DATE__", date))

    outdir = repo.views_dir(args.slug)
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{args.slug}-report.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(repo.ROOT)} ({len(html) // 1024} KB, {len(records)} records)")


if __name__ == "__main__":
    main()
