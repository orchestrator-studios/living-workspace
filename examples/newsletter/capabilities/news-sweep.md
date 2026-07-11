---
name: news-sweep
description: The stream's non-deterministic source — search the web for the window's
  major AI news that the feeds miss (Anthropic announcements above all — they have no
  reliable RSS — plus anything big). Pure analysis; returns stories, writes nothing.
runs: delegated
returns: |
  A JSON array of stories, each {url, title, source_name, published?, excerpt?} —
  primary-source URLs, at most the config's retmax. Nothing is written. The caller
  lands the batch via tools/land_stories.py --config <websweep id>, which dedups by
  URL and records the run.
---

# The news sweep — what did the feeds miss this window?

The deterministic sources (arXiv, RSS, Hacker News) run as `tools/fetch_sources.py`;
this capability covers what has no feed. It **searches and returns; it never writes**
— provenance comes from the landing step, which gives the sweep the same run record
and URL dedup as any fetch.

## What to sweep for, in priority order

1. **Anthropic** — releases, research posts, capability or policy announcements in
   the window. They are the sweep's reason to exist: no reliable official feed.
2. **Major releases and capability news** from any frontier lab that the window's
   feeds plausibly missed — model launches, notable evals, big API changes.
3. **Orchestration news** — agent frameworks, interop protocols, notable production
   write-ups.

## Rules

- **Primary sources only**: the lab's own post, the paper, the official docs — not
  coverage of them. If only coverage exists, use the best single piece and say so in
  the excerpt.
- The window is given by the caller — stories must fall in it (a `published` date
  you can attest beats a guess; omit it if unsure).
- Cap at the config's retmax; fewer good stories beat many thin ones. Duplicates are
  harmless — landing dedups by URL — but don't spend the budget on what an RSS feed
  obviously already carried.
- Return the array and stop. Judging *relevance* is not this capability's job — the
  semantic filter screens everything you land, so when torn, return it.
