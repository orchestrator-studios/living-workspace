# System Overview

*Repurposed 2026-07-10 by agreement with the user: the workspace's first domain (a
talc/asbestos litigation-science stream modeled on Knowledge Horizon) was retired and
wiped; KH (`C:\code\kh`) remains the architectural reference. The pipeline shape —
retrieve → filter → assemble, with recorded runs — carries over unchanged.*

## Purpose

Produce a **weekly AI-news newsletter** for a technically literate reader tracking
frontier AI. Three beats, and only these: **model capabilities** (releases, benchmarks,
capability jumps), **orchestration** (agents, multi-agent systems, tool use, workflow
frameworks), and **major-player news** (OpenAI, Google/Gemini/DeepMind, Anthropic —
plus other labs when the news is genuinely big). Each week: open the issue, pull the
window from every active source, screen for stream relevance (recording *why* for
every keep and every drop), summarize the keepers, and assemble the newsletter — a
file a subscriber could be sent as-is.

## The things

- **retrieval_config** (`C-##`) — one source the stream watches, as data: arXiv query,
  RSS feed, Hacker News query, or the web-sweep brief. Any number active; refining the
  stream is a data edit, never a code edit.
- **run** (`R-###`) — one retrieval execution: when, which config, over what window,
  what it matched, landed, and skipped as already known. The provenance of coverage;
  every article points back to its run.
- **article** (`A-###`) — one candidate story from a retrieval run: URL (the identity),
  title, source, published date, excerpt, its `run_id`, then the screening verdict —
  `status` (candidate / included / excluded), the `filter_reason`, and a plain-language
  `summary` once included.
- **issue** (`N-###`) — one weekly newsletter, complete: the window it covers, the
  included story ids (derived at assembly, never hand-curated), an executive summary,
  the assembled `body`, and its status (draft / final). The newsletter *is* this
  record; a file copy is an on-demand export, never stored state.

## The rules

1. **One record per URL, ever.** Retrieval refuses duplicates — the same story seen by
   two sources stays one article.
2. **Every screening verdict carries its reason.** No article moves out of `candidate`
   without a recorded `filter_reason` (`tools/record_verdict.py` refuses otherwise).
3. **An issue carries only included, summarized stories.** Membership is derived at
   assembly from the window's runs; `tools/assemble_issue.py` refuses an included
   story with no summary.
4. **The newsletter is assembled, never hand-written.** `tools/assemble_issue.py`
   renders the body from the records and stores it *on the issue record*; regenerate
   after any change. File copies (`--export`) are for sending — ephemeral, never the
   truth.
5. **Issue windows tile.** Each issue starts the day after the previous one ended —
   gap-free, overlap-free coverage (`tools/create_issue.py` enforces; `validate.py`
   checks).
6. **Final is frozen.** Only the user finalizes (`tools/finalize_issue.py`); after
   that, re-assembly and re-runs refuse to touch it.

## Where the data lives today

- Stories arrive from the active **retrieval_configs** in `data/retrieval_config/`:
  arXiv (API), company blogs (RSS), Hacker News (Algolia API) — executed
  deterministically by `tools/fetch_sources.py` — plus a **web sweep**
  (`capabilities/news-sweep.md`, delegated; landed by `tools/land_stories.py`) for
  what has no feed, Anthropic news above all.
- Reference architecture (bound, read-only): the KH app at `C:\code\kh` — the
  full-strength version of this pipeline shape.

## What you'll ask of it

- **The weekly run:** "Do this week's issue" → `capabilities/weekly-issue.md`, the
  algorithm: open the draft → fetch the sources → sweep the web → filter
  (`capabilities/semantic-filter.md`, delegated — returns analysis, writes nothing) →
  record verdicts → assemble → the user's gate.
- **Status:** "Where's this week's issue?" → the issues view; a draft mid-pipeline
  shows how many candidates still await a verdict.
- **Reading:** "Show me the newsletters" → the issues view: the shelf on the left, the
  open issue on the right — its summary, its stories, and how it was retrieved (the
  runs and the configs they executed).
- **Judgment calls:** "Why was this story dropped?" → the recorded filter_reason.
- **Later (grow on demand):** categorization into sections, stance/salience scoring,
  email delivery, per-source weighting.
