---
name: screening
description: Decide whether a retrieved paper is talc/asbestos litigation-science
  relevant, and record why. Use on any article in `candidate` status.
runs: either
returns: |
  For each article screened: {id, status: included|excluded, reason, summary?}.
  The verdict is already written to the record via tools/screen_article.py — the
  return value is the report, not the deposit.
---

# Screening — is this paper litigation-science relevant?

The soft form of the filter rule; the hard form is `tools/screen_article.py` (which
refuses any verdict without a reason) and `tools/validate.py` (which flags any
non-candidate without one). KH analog: the LLM semantic filter and its
`filter_score_reason`.

## How to run this

**Ambidextrous** — the same judgment, either way:

- **In-context**, when the user is screening one paper, arguing a borderline call, or
  tuning the criteria below. The reasoning is the product; it belongs in the
  conversation.
- **Delegated**, when a retrieval run lands a batch — one fresh agent per article, in
  parallel. A week's candidates carry thousands of tokens of abstract each, and the
  conversation needs none of it: the verdict and its reason land in `data/` through the
  tool, and only the one-line report comes back. This is the whole reason a weekly run
  doesn't drown the session.

Delegation is safe here because the enforcer is in the tool, not in this file: a fresh
agent that never read this page still cannot record a verdict with no reason. What
delegation *cannot* do is decide the criteria — changing what counts as relevant is a
conversation with the user, not a thing a delegate rules on.

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

## The verdict

Every verdict goes through the tool, with the reason stated in one or two sentences —
specific enough that "why was this dropped?" is answered by reading it back:

    python tools/screen_article.py A-007 --status excluded --reason "Talc pleurodesis
    technique study; treatment efficacy only, no causation or exposure content."

Included papers also get a `--summary`: 2–4 plain-language sentences a subscriber can
read without the abstract — what was studied, what was found, why it matters to the
stream.
