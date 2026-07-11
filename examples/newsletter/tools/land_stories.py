#!/usr/bin/env python3
"""land_stories.py — land externally-found stories as one recorded run (grown). The
deposit half of the web sweep: capabilities/news-sweep.md is a delegated pure analysis
that *returns* stories; its caller lands them here, so the sweep gets the same
provenance (a run record, run_id on every article) as a deterministic fetch.

Carries OVERVIEW rule 1: one record per URL, ever — already-known URLs are skipped
and recorded as such.

Usage:  python tools/land_stories.py --config C-06 \
            --window-start 2026-07-03 --window-end 2026-07-10 [--file stories.json]
        --file (or stdin): JSON array of
        {url, title, source_name?, published?, excerpt?, authors?}
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

import repo


def main() -> int:
    ap = argparse.ArgumentParser(description="Land swept stories as one recorded run.")
    ap.add_argument("--config", required=True, help="the websweep retrieval_config id")
    ap.add_argument("--window-start", required=True)
    ap.add_argument("--window-end", required=True)
    ap.add_argument("--file", help="read the JSON array from a file instead of stdin")
    args = ap.parse_args()

    if not repo.exists("retrieval_config", args.config):
        print(f"REFUSED: no retrieval_config '{args.config}'")
        return 1
    config = repo.load("retrieval_config", args.config)
    stories = json.loads(Path(args.file).read_text(encoding="utf-8-sig")) \
        if args.file else json.load(sys.stdin)
    if not isinstance(stories, list):
        print("REFUSED: stdin must be a JSON array of stories")
        return 1

    known = {a["url"].lower() for a in repo.load_all("article")}
    today = datetime.date.today().isoformat()
    run_id, added, skipped = repo.next_id("run"), [], []
    for story in stories[:int(config["retmax"])]:
        url = (story.get("url") or "").strip()
        if not url or not (story.get("title") or "").strip():
            print(f"SKIP: story without url/title: {json.dumps(story)[:80]}")
            continue
        if url.lower() in known:
            skipped.append(url)
            continue
        known.add(url.lower())
        rid = repo.next_id("article")
        repo.save("article", {"id": rid, "url": url, "title": story["title"].strip(),
                              "source_name": story.get("source_name") or config["name"],
                              "published": story.get("published", ""),
                              "authors": story.get("authors", ""),
                              "excerpt": story.get("excerpt", ""),
                              "status": "candidate", "filter_reason": None,
                              "summary": None, "retrieved": today, "run_id": run_id})
        added.append(rid)
        print(f"OK {rid} — {story['title'][:70]}")
    repo.save("run", {"id": run_id, "date": today, "config": config["id"],
                      "window_start": args.window_start, "window_end": args.window_end,
                      "matched": len(stories), "added": added,
                      "skipped_urls": skipped})
    print(f"RUN {run_id} ({config['name']}): {len(stories)} swept, "
          f"{len(added)} added, {len(skipped)} already known")
    return 0


if __name__ == "__main__":
    sys.exit(main())
