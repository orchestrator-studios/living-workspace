---
name: semantic-filter
description: The stream's relevance analysis — decide whether retrieved stories belong
  in an AI newsletter focused on model capabilities, orchestration, and major-player
  news, and say why. Pure analysis; returns verdicts, writes nothing. Use on any batch
  of candidate articles.
runs: delegated
returns: |
  For each story analyzed: {id, verdict: included|excluded, reason, summary?}.
  Analysis only — nothing is written. The caller (capabilities/weekly-issue.md, or
  the conversation for a one-off) records verdicts via tools/record_verdict.py.
---

# The semantic filter — does this story belong in the AI newsletter?

The judgment half of the filter rule: what belongs in this stream. This capability
**analyzes and returns; it never writes.** That purity is why the same filter serves
the weekly pipeline, a one-off "re-check this story", and a "test the criteria against
last week's batch" — none of which should touch the record until the caller decides.
Persistence is the caller's step, through `tools/record_verdict.py`, whose refusal
(no reason, no move) is the rule's enforceable core — nothing here restates it.

Changing the criteria below is a conversation with the user — never a delegate's call.

## The question

Would a technically literate reader tracking **frontier AI** want this story in their
weekly briefing? The stream cares about three things, and only these:

## Include when the story bears on

- **Model capabilities** — new model releases or substantive updates; benchmark and
  eval results that move the picture; capability jumps (reasoning, context, coding,
  multimodal, speed/cost); notable capability research.
- **Orchestration** — agent architectures, multi-agent systems, tool use and
  interoperability protocols, workflow/planning frameworks, agent evaluation
  harnesses, production lessons about running agents.
- **Major-player news** — substantive announcements from OpenAI, Google/DeepMind, or
  Anthropic: releases, research, API/pricing changes with real consequence, strategic
  or safety moves that matter. Other labs (Meta, xAI, Mistral, DeepSeek, Qwen…) when
  the news is genuinely big.

## Exclude when it is

- Marketing fluff, or a **minor integration** ("app X adds AI feature").
- Opinion or hot takes with no new information; speculation and unconfirmed rumors.
- Tutorials, how-tos, and listicles.
- A **repost or aggregation** of a primary source — prefer the primary; if the
  primary is already a candidate in this window, exclude the echo and say so.
- Research with no capability or orchestration relevance (applications of AI to other
  fields, pure theory without a capability claim).
- Borderline major-player news: when in doubt, **include and say why** — a subscriber
  would rather skim one extra story than miss a real one.

## The analysis you return

For every story: the **verdict** (included / excluded) and a **reason** in one or two
sentences — specific enough that "why was this dropped?" is answered by reading it
back. For included stories, also a **summary**: 2–4 plain-language sentences a
subscriber can read without clicking through — what happened, what's new about it,
why it matters to this stream. Return the whole batch as structured lines; write
nothing.
