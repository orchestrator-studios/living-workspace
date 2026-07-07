# System Overview

*Drafted from the client's file (`seed/`) on 2 July 2026, gaps closed by interview.
Everything else in this workspace traces back to this file.*

## Purpose

Produce a structured literature review for Lakeshore Health System: **does remote patient
monitoring of heart-failure patients after discharge reduce hospital readmissions?**
(Secondary outcomes: mortality, adherence, cost.) Deliverable: a report the client's board
can act on, in which every claim traces to an explicitly included source, and every
exclusion is recorded with its reason — due ahead of the September board cycle.

## The things

- **Source** — a paper under consideration: citation, how it was found, and its screening
  status (unscreened → included / excluded, with the criterion it was decided on).
- **Finding** — one extracted claim from one included source: outcome, direction, evidence.
- **Theme** — a synthesis bucket the findings are organized under in the report.
- **Search** — a logged sweep: query, database, date, hits, which sources it added.

## The rules

- Screening criteria are the brief's (`seed/brief.md`), verbatim — not improvised per paper.
- Every screening decision records **which criterion** it was decided on.
- A source enters the review **once** — the same DOI can never be added twice.
- A finding may only cite an **included** source. Nothing in the report may reference
  anything that wasn't screened in. Excluded sources appear only in the exclusions appendix.
- Once the report is delivered, the underlying decisions are frozen — revisions happen as
  a new versioned pass, not silent edits.

## Where the data lives today

The client's file, mirrored in `seed/`: the email thread (the ask), the brief (question,
criteria, ground rules), and `flagged-papers.csv` — five papers the client's medical
director considers the starting point. Everything else will come from logged searches.

## What you'll ask of it

- "Pull in the papers the client already flagged."
- "Run a sweep with the brief's criteria; add what's new."
- "Screen S-007 — include or exclude, against the criteria, with the reason."
- "What's still unscreened?" / a glanceable screening board.
- "Extract the findings from the included sources and organize them into themes."
- "Assemble the report."
