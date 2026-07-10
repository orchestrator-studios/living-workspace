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

- **article** (`A-###`) — one candidate paper from a retrieval run: PMID, title,
  journal, publication date, authors, abstract, then the screening verdict — `status`
  (candidate / included / excluded), the `filter_reason`, and a plain-language
  `summary` once included.
- **issue** (`N-###`) — one weekly newsletter: the window it covers, the included
  article ids, an executive summary, and its status (draft / final). The rendered
  newsletter file is a projection of this record, assembled by tool.

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
   renders it from the issue record and the article records; regenerate after any
   change, never edit the output.

## Where the data lives today

- Articles arrive from **PubMed E-utilities** (`tools/fetch_pubmed.py` carries the
  stream query — talc/asbestos × disease/exposure terms — and the date window).
- Reference material (bound, read-only): the KH app at `C:\code\kh` — the full-strength
  version of this pipeline (LLM semantic filter, stance analysis, salience scoring),
  used for behavioral fidelity, not as a data source.

## What you'll ask of it

- **The weekly run:** "Do this week's issue" → fetch the window → screen candidates
  (`capabilities/screening.md` — delegated, one agent per candidate, when the batch is
  large) → summarize the keepers → assemble the newsletter.
- **Status:** "Where's this week's issue?" → the live pipeline board.
- **Judgment calls:** "Why was this paper dropped?" → the recorded filter_reason.
- **Later (KH parity, grow on demand):** stance analysis (pro-plaintiff / pro-defense /
  neutral), salience scoring, category grouping, email delivery.
