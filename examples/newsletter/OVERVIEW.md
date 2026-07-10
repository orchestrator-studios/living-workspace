# System Overview

*Drafted at intake from the Knowledge Horizon repo (`C:\code\kh` — stream 10, "Asbestos
and Talc Litigation") and conversation with the user. This is a deliberately basic
version of that stream's pipeline: query → filter → summarize → assemble.*

## Purpose

Produce a **weekly literature-monitoring newsletter** on the science relevant to talc
and asbestos litigation — modeled on Knowledge Horizon's talc/asbestos stream. Each
week: run the PubMed query for the trailing window, screen the candidates for
litigation-science relevance (recording *why* for every keep and every drop),
summarize what's included, and assemble the newsletter — a file a subscriber could be
sent as-is.

## The things

- **retrieval_config** (`C-##`) — one stream definition, as data: the PubMed query,
  the default window, the cap, and whether it's active. Refining the stream is a data
  edit, never a code edit. (KH: the stream definition.)
- **run** (`R-###`) — one retrieval execution: when it ran, which config, over what
  window, what it matched, what it landed, what it skipped as already known. The
  provenance of coverage; every article points back to its run.
- **article** (`A-###`) — one candidate paper from a retrieval run: PMID, title,
  journal, publication date, authors, abstract, its `run_id`, then the screening
  verdict — `status` (candidate / included / excluded), the `filter_reason`, and a
  plain-language `summary` once included.
- **issue** (`N-###`) — one weekly newsletter, complete: the window it covers, the
  included article ids, an executive summary, the assembled `body`, and its status
  (draft / final). The newsletter *is* this record; a file copy is an on-demand
  export, never stored state.

## The rules

1. **One record per PMID, ever.** Retrieval refuses duplicates — the same paper seen by
   two runs stays one article. (KH: `wip_articles` dedup by PMID.)
2. **Every screening verdict carries its reason.** No article moves out of `candidate`
   without a recorded `filter_reason` — the "why was it dropped" text. (KH:
   `filter_score_reason`.)
3. **An issue cites only included articles.** The assemble tool refuses an issue that
   references an excluded or still-candidate article — the newsletter *cannot* carry an
   unscreened paper. (The lit-review example's citation-closure rule, in newsletter
   form.)
4. **The newsletter is assembled, never hand-written.** `tools/assemble_issue.py`
   renders the body from the issue record and the article records and stores it *on
   the issue record*; regenerate after any change. A final issue must carry its body.
   File copies (`--export`) are for sending — ephemeral, never the truth.

## Where the data lives today

- Articles arrive from **PubMed E-utilities** — `tools/fetch_pubmed.py` executes the
  active **retrieval_config** (the stream query — talc/asbestos × disease/exposure
  terms — lives in `data/retrieval_config/`, not in code) and records every run.
- Reference material (bound, read-only): the KH app at `C:\code\kh` — the full-strength
  version of this pipeline (LLM semantic filter, stance analysis, salience scoring),
  used for behavioral fidelity, not as a data source.

## What you'll ask of it

- **The weekly run:** "Do this week's issue" → `capabilities/weekly-issue.md`, the
  pipeline as procedure: retrieve → filter (`capabilities/semantic-filter.md`,
  delegated — returns analysis, writes nothing) → record verdicts
  (`tools/record_verdict.py`) → assemble → the user's gate.
- **Status:** "Where's this week's issue?" → the issues view; a draft mid-pipeline
  shows how many candidates still await a verdict.
- **Reading:** "Show me the newsletters" → the issues view: the shelf on the left, the
  open issue on the right — its summary, its papers, and how it was retrieved (the
  runs and the config they executed).
- **Judgment calls:** "Why was this paper dropped?" → the recorded filter_reason.
- **Later (KH parity, grow on demand):** stance analysis (pro-plaintiff / pro-defense /
  neutral), salience scoring, category grouping, email delivery.
