---
name: weekly-issue
description: The whole weekly pipeline, end to end — retrieve, filter, record verdicts,
  assemble the newsletter. Use when the user asks for this week's issue (or any new
  issue).
runs: in-context
---

# The weekly issue — the pipeline

The stream's pipeline as procedure (KH analog: `pipeline_service`'s stage list, in its
basic form): **retrieve → filter → record → assemble → gate.** Stages run in order,
and every stage deposits to the record through a tool before the next begins — so the
issues view tracks the run live, and an interrupted run resumes wherever the record
says it stopped.

## 1. Retrieve

    python tools/fetch_pubmed.py

Executes the active retrieval_config over its trailing window (`--mindate`/`--maxdate`
to override), lands each new paper as a `candidate` article, and records the run — the
provenance of coverage. Dedup is structural: one record per PMID, ever, so re-fetching
a window is harmless.

## 2. Filter — delegated

Delegate `capabilities/semantic-filter.md` over the candidates: one delegate per
article for a big batch, one delegate for the lot when it's small. The filter returns
**analysis only** — `{id, verdict, reason, summary?}` per article — and writes
nothing. The abstracts stay in the delegates' transcripts; the conversation sees only
the verdicts.

## 3. Record

For each returned analysis:

    python tools/record_verdict.py A-0XX --status included --reason "..." --summary "..."
    python tools/record_verdict.py A-0XX --status excluded --reason "..."

The tool refuses a verdict without a reason (OVERVIEW rule 2) — that refusal, not this
file, is the rule's enforceable core. After the batch: `python tools/validate.py`.

## 4. Assemble

Create the issue record — the window, the included article ids, an executive summary
drafted from the verdicts — then:

    python tools/assemble_issue.py N-0XX

The body lands on the issue record; REFUSED if any cited article is unincluded or
unsummarized (rule 3). The draft is now readable on the issues view.

## 5. Gate — the user's

The user reads the draft on the issues view and approves. Only then does `status` flip
to `final` (re-assemble after). Finality is never the pipeline's call. To produce a
sendable copy: `python tools/assemble_issue.py N-0XX --export <path>` — an ephemeral
export; the record stays the truth.
