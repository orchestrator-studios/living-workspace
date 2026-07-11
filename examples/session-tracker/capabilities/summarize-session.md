---
name: summarize-session
description: Read one session's transcript and write a short synthesis of it. Use on a
  session the trigger algo (repo.summaries_due) reports as due.
runs: delegated
returns: |
  {session_id, project, wrote: true, note?: one line}. The summary is already written
  via tools/write_summary.py (which stamps the watermark) — the return value is the
  report, not the deposit. On refusal, return {refused: the tool's message}.
---

# Summarizing a session

Two moving parts, split the way the doctrine splits them:

- **The trigger algo** — `repo.summaries_due()` — decides *when*. Deterministic, cheap,
  stat-only: a session is due when it has settled (idle ≥ `SUMMARY_SETTLE_S`) and either
  has no summary or has grown past its watermark by ≥ `SUMMARY_GROWTH_BYTES`. It is not
  this capability; it is a query anyone can ask.
- **This capability** — decides *what*. The judgment: read the transcript and say what the
  session was about. No tool can write it, so it stays in language.

## Why this is delegated

Summarizing means reading a whole transcript — often megabytes of prompts, replies, tool
calls, and tool output — to produce four sentences. That is the delegation signature
exactly: **bulky and disposable in, small and durable out.** One fresh agent per due
session reads its transcript in its own context, writes the summary through the tool, and
returns one line; the transcript text never enters the caller's conversation. This is why
a tracker over hundreds of sessions can keep its summaries current without ever flooding
the session you are working in. It is safe for the reason all delegation here is safe: the
watermark that keeps summaries honest is stamped by `write_summary.py`, not by the agent —
a delegate that never read this page still cannot write a summary without one.

## The procedure

You are given a `session_id` (from `summaries_due()`).

1. **Read enough of the transcript to summarize it.** Use `repo.session(session_id)` for
   the structured basics (project, first/last prompt, turn counts, model), and read the
   transcript file itself — `~/.claude/projects/<project>/<session_id>.jsonl`, one JSON
   object per line — for the arc of the work. You need not read every byte of a giant
   transcript: the opening prompts, a sampling through the middle, and the tail are
   enough to say what happened. (This is your own context to spend; spend it here so the
   caller's stays clean.)
2. **Write 3–5 plain sentences** answering *what was this session about, and where did it
   get to?* — the goal, the substantive moves, the current state or outcome. Name things
   concretely (files, features, decisions). No preamble, no "this session…", no restating
   metadata the tracker already shows.
3. **Persist it through the tool** — never write `data/summary/` by hand:

       python tools/write_summary.py <session_id> --text "…" --model claude-fable-5

   The tool stamps the watermark from the live transcript, so the algo can later tell the
   summary has gone stale.
4. **Report back** in the contract's shape. If the tool refuses, return the refusal; do
   not work around it.

## The loop this lives in

"Summarize what's due" is: ask `repo.summaries_due()`, then delegate this capability once
per due session (a fan-out — each session's read is self-contained). The algo re-runs
cheaply afterward and the freshly-summarized sessions drop off the due list, because their
watermarks now match. Nothing here writes to `~/.claude`; the only deposit is the
contained summary record.
