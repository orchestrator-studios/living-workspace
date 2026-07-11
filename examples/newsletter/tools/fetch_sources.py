#!/usr/bin/env python3
"""fetch_sources.py — the deterministic retrieval step (grown). Executes every active
retrieval_config that a tool can execute (arxiv, rss, hackernews) over a date window,
lands each new story as a candidate article, and writes one run record per config —
the provenance of coverage. websweep configs are skipped here: they run as the
delegated capabilities/news-sweep.md, landed via tools/land_stories.py.

The sources are NOT here: they live in data/retrieval_config/ (refining the stream is
a data edit, visible on the issues view). Carries OVERVIEW rule 1: one record per URL,
ever — a URL already in the record is skipped, not re-ingested, and the run records
what was skipped. A config that fails to fetch is reported and skipped; the others
still run.

Usage:  python tools/fetch_sources.py [--config C-01]
                                      [--window-start 2026-07-03 --window-end 2026-07-10]
        The window defaults to the current draft issue's, else the trailing
        window_days of each config, ending today.
"""
import argparse
import datetime
import email.utils
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import repo

ATOM = "{http://www.w3.org/2005/Atom}"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "living-workspace-newsletter/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def plain(text, cap=600):
    """Feed descriptions arrive as HTML; the record keeps plain text."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:cap]


def iso_date(raw):
    """Best-effort YYYY-MM-DD from the date forms feeds actually use; '' if hopeless."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    try:  # RFC 2822 — RSS pubDate
        return email.utils.parsedate_to_datetime(raw).date().isoformat()
    except (TypeError, ValueError):
        pass
    match = re.match(r"(\d{4}-\d{2}-\d{2})", raw)  # ISO-ish — Atom, arXiv, Algolia
    return match.group(1) if match else ""


# --- one fetcher per executable source; each yields story dicts -----------------
def fetch_arxiv(config, start, end):
    params = urllib.parse.urlencode({
        "search_query": config["query"], "sortBy": "submittedDate",
        "sortOrder": "descending", "max_results": int(config["retmax"]) * 3})
    root = ET.fromstring(get(f"http://export.arxiv.org/api/query?{params}"))
    for entry in root.findall(f"{ATOM}entry"):
        published = iso_date(entry.findtext(f"{ATOM}published", ""))
        if published and not (start <= published <= end):
            continue
        authors = [a.findtext(f"{ATOM}name", "") for a in entry.findall(f"{ATOM}author")]
        yield {"url": entry.findtext(f"{ATOM}id", "").strip(),
               "title": plain(entry.findtext(f"{ATOM}title", ""), 300),
               "published": published,
               "authors": (authors[0] + (" et al." if len(authors) > 1 else "")) if authors else "",
               "excerpt": plain(entry.findtext(f"{ATOM}summary", ""))}


def fetch_rss(config, start, end):
    root = ET.fromstring(get(config["query"]))
    if root.tag == f"{ATOM}feed":  # Atom
        for entry in root.findall(f"{ATOM}entry"):
            link = entry.find(f"{ATOM}link")
            published = iso_date(entry.findtext(f"{ATOM}published", "")
                                 or entry.findtext(f"{ATOM}updated", ""))
            if published and not (start <= published <= end):
                continue
            yield {"url": (link.get("href") if link is not None else "").strip(),
                   "title": plain(entry.findtext(f"{ATOM}title", ""), 300),
                   "published": published, "authors": "",
                   "excerpt": plain(entry.findtext(f"{ATOM}summary", ""))}
    else:  # RSS 2.0
        for item in root.findall("./channel/item"):
            published = iso_date(item.findtext("pubDate", ""))
            if published and not (start <= published <= end):
                continue
            yield {"url": (item.findtext("link") or "").strip(),
                   "title": plain(item.findtext("title", ""), 300),
                   "published": published, "authors": "",
                   "excerpt": plain(item.findtext("description", ""))}


def fetch_hackernews(config, start, end):
    lo = int(datetime.datetime.fromisoformat(start).timestamp())
    hi = int((datetime.datetime.fromisoformat(end)
              + datetime.timedelta(days=1)).timestamp())
    params = urllib.parse.urlencode({
        "query": config["query"], "tags": "story",
        "numericFilters": f"created_at_i>{lo},created_at_i<{hi}",
        "hitsPerPage": int(config["retmax"]) * 3})
    payload = json.loads(get(f"https://hn.algolia.com/api/v1/search_by_date?{params}"))
    for hit in payload.get("hits", []):
        yield {"url": (hit.get("url")
                       or f"https://news.ycombinator.com/item?id={hit.get('objectID')}").strip(),
               "title": plain(hit.get("title", ""), 300),
               "published": iso_date(hit.get("created_at", "")),
               "authors": hit.get("author", ""),
               "excerpt": f"{hit.get('points', 0)} points on Hacker News"}


FETCHERS = {"arxiv": fetch_arxiv, "rss": fetch_rss, "hackernews": fetch_hackernews}


def default_window(days):
    draft = next((i for i in sorted(repo.load_all("issue"),
                                    key=lambda i: i["id"], reverse=True)
                  if i["status"] == "draft"), None)
    if draft:
        return draft["week_start"], draft["week_end"]
    today = datetime.date.today()
    return (today - datetime.timedelta(days=int(days))).isoformat(), today.isoformat()


def main():
    ap = argparse.ArgumentParser(description="Fetch every executable active source.")
    ap.add_argument("--config", help="retrieval_config id; default: all active executable ones")
    ap.add_argument("--window-start", help="YYYY-MM-DD; default: the draft issue's window")
    ap.add_argument("--window-end", help="YYYY-MM-DD")
    args = ap.parse_args()

    configs = [repo.load("retrieval_config", args.config)] if args.config else \
        [c for c in repo.load_all("retrieval_config") if c["active"]]
    known = {a["url"].lower() for a in repo.load_all("article")}
    today = datetime.date.today().isoformat()

    for config in configs:
        if config["source"] not in FETCHERS:
            print(f"SKIP {config['id']} ({config['name']}): source '{config['source']}' "
                  f"runs as capabilities/news-sweep.md, landed via tools/land_stories.py")
            continue
        start, end = ((args.window_start, args.window_end)
                      if args.window_start and args.window_end
                      else default_window(config["window_days"]))
        try:
            stories = [s for s in FETCHERS[config["source"]](config, start, end) if s["url"]]
        except Exception as err:
            print(f"WARN {config['id']} ({config['name']}): fetch failed — "
                  f"{type(err).__name__}: {err}")
            continue
        stories = stories[:int(config["retmax"])]
        run_id, added, skipped = repo.next_id("run"), [], []
        for story in stories:
            if story["url"].lower() in known:
                skipped.append(story["url"])
                continue
            known.add(story["url"].lower())
            rid = repo.next_id("article")
            repo.save("article", {"id": rid, "source_name": config["name"],
                                  "status": "candidate", "filter_reason": None,
                                  "summary": None, "retrieved": today,
                                  "run_id": run_id, **story})
            added.append(rid)
            print(f"OK {rid} — {story['title'][:70]}")
        repo.save("run", {"id": run_id, "date": today, "config": config["id"],
                          "window_start": start, "window_end": end,
                          "matched": len(stories), "added": added,
                          "skipped_urls": skipped})
        print(f"RUN {run_id} ({config['name']}): {len(stories)} in window, "
              f"{len(added)} added, {len(skipped)} already known")


if __name__ == "__main__":
    main()
