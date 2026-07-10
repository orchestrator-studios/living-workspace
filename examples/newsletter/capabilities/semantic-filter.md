---
name: semantic-filter
description: The stream's relevance analysis — decide whether retrieved papers are
  talc/asbestos litigation-science relevant, and say why. Pure analysis; returns
  verdicts, writes nothing. Use on any batch of candidate articles.
runs: delegated
returns: |
  For each article analyzed: {id, verdict: included|excluded, reason, summary?}.
  Analysis only — nothing is written. The caller (capabilities/weekly-issue.md, or
  the conversation for a one-off) records verdicts via tools/record_verdict.py.
---

# The semantic filter — is this paper litigation-science relevant?

The judgment half of the filter rule: what "litigation-science relevant" means. This
capability **analyzes and returns; it never writes.** That purity is why the same
filter serves the weekly pipeline, a one-off "re-check this paper", and a "test the
criteria against last week's batch" — none of which should touch the record until the
caller decides. Persistence is the caller's step, through `tools/record_verdict.py`,
whose refusal (no reason, no move) is the rule's enforceable core — nothing here
restates it. KH analog: `semantic_filter_service` — criteria in, normalized
per-article verdicts out, persistence elsewhere.

Changing the criteria below is a conversation with the user — never a delegate's call.

## The question

Would this paper's findings plausibly matter to product-liability or toxic-tort
litigation involving **talc or asbestos**? That is the stream's only question — not
whether the science is good, novel, or interesting.

## Include when the paper bears on

- **Causation** — exposure→disease evidence in humans (mesothelioma, ovarian cancer,
  lung disease): epidemiology, case series, mechanistic studies used in causation
  arguments.
- **Exposure & contamination** — measuring asbestos in talc products, fiber burden
  analysis, exposure reconstruction, analytical methods for detecting contamination.
- **Attribution science** — distinguishing asbestos-caused disease from other causes;
  latency; dose-response.
- **The litigation itself** — commentary, reviews, or medico-legal analyses of the
  talc/asbestos litigation landscape.

## Exclude when it is

- Materials science or industrial use of talc/asbestos with **no health dimension**
  (ceramics, composites, geology-only).
- Clinical use of **talc pleurodesis** as a treatment technique with no
  safety/causation angle.
- About a different exposure entirely (the query's `exposure` term casts wide — expect
  bycatch).
- Animal/in-vitro work so preliminary it could not be cited in a causation argument —
  judgment call: when in doubt, include and say why.

## The analysis you return

For every article: the **verdict** (included / excluded) and a **reason** in one or
two sentences — specific enough that "why was this dropped?" is answered by reading it
back. For included papers, also a **summary**: 2–4 plain-language sentences a
subscriber can read without the abstract — what was studied, what was found, why it
matters to the stream. Return the whole batch as structured lines; write nothing.
