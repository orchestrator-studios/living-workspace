# The Canon — how a living workspace works

This folder is the system's doctrine: what a living workspace *is*, how work moves through
it — from whole journeys down to single moves — and what it's made of. Everything here is general — nothing about any particular
project. For the concept in action, see [the worked example](../examples/lit-review/JOURNEY.md); to
start your own, copy [the template](../template/).

| Doc | Question it answers |
|---|---|
| this file | What is a living workspace? |
| [the-journey.md](the-journey.md) | How does a whole piece of work get from here to done? |
| [the-move-rule.md](the-move-rule.md) | How does a single move get made? |
| [anatomy.md](anatomy.md) | What is it made of? |
| [operating-manual.md](operating-manual.md) | What does the agent follow, and why? |

## The definition

> A living workspace is a work environment on a shared file substrate, operated by an
> agent in conversation with its user, that grows its own capabilities as a side effect
> of the work — never deployed, never finished, always in use.

Three properties make something a living workspace. Each is necessary; together they are
sufficient:

1. **A shared, meaning-bearing file substrate.** The durable state lives in files that both
   the person and the agent read and write — and the files carry all four kinds of content:
   data, understanding (schemas, rules), capability (tools, capabilities), and presentation
   (views). A file is simultaneously something to read, an instruction to follow, and a
   program to run. In application terms, the substrate is the **backend** — the data layer
   (the system of record) and the application layer (the meaning, operations, and rules
   that govern it), together — persisted as files rather than hidden behind a frozen
   interface; *durable* because those files persist and accumulate across sessions, so the
   workspace's memory is the substrate, never the conversation. The substrate may be
   *contained* in the workspace, *bound* from systems that live elsewhere (a CRM, a drive,
   a database), or both — that's a spectrum within the concept, not a boundary of it.

2. **Agent operation.** An agent with tool reach is the primary operator, standing where
   an application's frontend used to stand — and the user↔agent interaction runs both
   ways. Conversation is the native interface; every other interface — a board, a report,
   an export, an approval request — is an answer computed from the substrate that the
   agent can generate and regenerate on demand. In return, the user's decisions and
   intentions reach the substrate only through the agent and its tools. Neither direction
   requires co-presence: a projected surface can outlive the session that produced it, and
   a decision can wait, queued, until the agent next runs. A surface owns only the glass;
   the workspace owns the meaning and the work.

3. **Capability accretion — the "living" part.** There is no boundary between using the
   system and extending it. Every obstacle asks *"what capability is missing?"*, and every
   answer is deposited permanently as files the agent reads from then on.

## The category

A living workspace is not an unfinished application. It's a **capability system** — a thing
in the same category as a practice or a craft, for which "finished" is not a defined state.
Every obstacle asks what capability is missing; every solution permanently expands the
workspace's inventory; progress comes not just from accomplishing tasks but from continually
enriching the workspace so it can accomplish more ambitious tasks next.

## The test

Apply the three properties and boundary cases sort themselves:

- A repo you build and **ship** — fails 2 and 3: the capability leaves; a deploy boundary
  separates using from extending.
- **Chat with your data** (a copilot bolted onto a backend) — fails 1 and 3: agent-operated,
  but nothing accumulates in a substrate you own.
- A **Notion workspace** — fails 2 and 3: shared substrate, but the files aren't executors
  and no agent operates it.
- The [worked example](../examples/lit-review/JOURNEY.md) in this repo — passes all three.
