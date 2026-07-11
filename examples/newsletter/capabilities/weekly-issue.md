---
name: weekly-issue
description: The whole weekly pipeline, end to end — open the draft, retrieve, sweep,
  filter, record verdicts, assemble, gate. Use when the user asks for this week's
  issue (or any new issue).
runs: in-context
---

# The weekly issue — the algorithm

**open → retrieve → sweep → filter → record → assemble → gate.** Stages run in order,
every stage deposits to the record through a tool before the next begins, and the
issues view tracks the whole run live. Re-running any stage is safe: retrieval dedups
by URL, membership is derived at assembly, and a `final` issue is frozen — re-runs
cannot touch it.

## 0. Open the draft

    python tools/create_issue.py

Windows **tile**: the new window starts the day after the previous issue's `week_end`
and ends today (first issue: trailing 7 days). The tool refuses a second open draft
and any overlap. The draft exists before retrieval so the view tracks the run from the
first second.

## 1. Retrieve — the deterministic sources

    python tools/fetch_sources.py

Executes every active `retrieval_config` a tool can execute (arxiv, rss, hackernews)
over the draft's window — one run record per config, one record per URL ever.
websweep configs are skipped here; they're stage 2.

## 2. Sweep — the delegated source

Delegate `capabilities/news-sweep.md` with the window and the websweep config's brief.
It **returns stories, writes nothing**. Land what it returns:

    python tools/land_stories.py --config C-XX --window-start ... --window-end ... < stories.json

Same provenance as a fetch: one run record, URL dedup, `run_id` on every story.

## 3. Filter — delegated

Delegate `capabilities/semantic-filter.md` over the window's candidates (one delegate
per story for a big batch; one for the lot when small). It returns analysis only:
`{id, verdict, reason, summary?}`.

## 4. Record

For each returned analysis:

    python tools/record_verdict.py A-0XX --status included --reason "..." --summary "..."
    python tools/record_verdict.py A-0XX --status excluded --reason "..."

The tool refuses a verdict without a reason — that refusal is the rule's enforceable
core. After the batch: `python tools/validate.py`.

## 5. Assemble

Draft the executive summary from the verdicts (in-context — the user should watch
this judgment), then:

    python tools/assemble_issue.py N-0XX --exec-summary "..."

Membership is **derived**, not curated: the issue's stories are the included articles
its window's runs landed. The body lands on the record; REFUSED if an included story
lacks a summary, or if the issue is final.

## 6. Gate — the user's

The user reads the draft on the issues view and approves. Only then:

    python tools/finalize_issue.py N-0XX

Refuses without a body, refuses with unscreened candidates in the window
(`--allow-pending` to override). After this the issue is **frozen** — assembly and
re-runs refuse it. Send a copy: `assemble_issue.py N-0XX --export <path>`.

## Resuming an interrupted run

The record says where you are — read it, don't re-derive:

| The record shows | Resume at |
|---|---|
| no draft issue | stage 0 |
| draft exists, no runs cover its window | stage 1 |
| runs exist, no websweep run in window | stage 2 |
| candidates remain in the window | stage 3 |
| verdicts done, body missing or stale | stage 5 |
| body assembled, status draft | stage 6 (the user's call) |
