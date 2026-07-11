# Anatomy — what a living workspace is made of

Two documents and five folders. That's the whole skeleton, and each piece serves one of the
[three defining properties](README.md#the-definition).

## The two documents

| Document | Role |
|---|---|
| `OVERVIEW.md` | **What this system is.** Purpose, the things the work is made of, the rules that must hold, where the data lives today, the recurring asks. Filled in *first* — from whatever source material exists plus an interview — before any schema, record, tool, or view. Everything else traces back to it. |
| `CLAUDE.md` | **The operating manual the agent follows.** Loaded when the agent enters the workspace. Canonical text and rationale: [operating-manual.md](operating-manual.md). |

## The five folders

| Folder | Holds | Serves |
|---|---|---|
| `data/` | The persistent objects — the system of record. One file per record. | substrate |
| `schemas/` | The structure and validity of **every type the workspace reasons about** — whether its records are *contained* in `data/` or *bound* in an external system. Each schema is its kind's **single declaration**: `x-kind` names the kind, and for a contained kind the id pattern fixes the id format and names its `data/` folder. A bound kind adds `x-source` (where its records really live) and has no `data/` folder — the schema is still its meaning (see [contained and bound](#contained-and-bound-substrates)). | understanding |
| `tools/` | Deterministic operations: create, update, validate, query, transform, assemble. Three residents: the **data-access layer** (`repo.py`, shipped — see [one definition of every number](#one-definition-of-every-number)), **muscle** (pure operations, grown) and **enforcers** (operations that carry rules — the dedup check, the citation gate; grown). The kit's `server.py` and `validate.py` live here too. | access · enforcement |
| `capabilities/` | Procedure in language — how to use the tools correctly, what to watch for, how to judge. The judgment part of the workspace's rules: what no enforcer tool can check (see [where a rule lives](#where-a-rule-lives)). Each declares **how it runs**: in the conversation's context, or delegated to a fresh one (see [in-context and delegated](#in-context-and-delegated)). The kit ships one: `dashboard.md`. | understanding |
| `views/` | View **logic** — templates, never rendered output, never a second source of truth. The kit ships `index.template.html`; domain views are grown (see [the anatomy of a view](#the-anatomy-of-a-view)). | presentation |

## The standard kit

Not everything is grown. A small set of machinery is **domain-agnostic, identical in every
workspace, and encodes zero domain knowledge** — making each workspace re-derive it teaches
nothing and costs the user real time. That set ships with the template:

| Ships | What it is |
|---|---|
| `tools/repo.py` | The data-access layer, as a skeleton: paths, the CRUD primitives (load/save/next-id conventions), the kind table derived from `schemas/` at import, and an empty query registry. |
| `tools/server.py` | The dashboard server: the index at `/`, any template at `/view/<name>`, any published query at `/api/<name>`, `/health`. URL parameters reach the query as keyword arguments. Reads over GET; a workspace may also publish write **actions** served over `POST /action/<name>` (empty by default — see [actions](#actions-when-the-dashboard-should-do)). Stdlib only, holds no state of its own. |
| `tools/validate.py` | The generic schema checker plus the alignment backstop (every schema declares its kind; every `data/` folder is governed by a schema); the workspace grows its cross-record integrity rules into it, in place. |
| `capabilities/dashboard.md` | The keep-the-server-up recipe: probe, background-launch, hand over the link once. |
| `views/index.template.html` | The dashboard's index page — views and queries appear on it as they come into existence. |

The test for shipping is strict, and it is the same line the move rule draws: **the kit is
the system's machinery; everything the *domain* shapes is grown.** Schemas, records, domain
tools, named queries, and view templates never ship — they are the workspace coming to life.
The payoff of the kit is that the workspace is *visible from minute one*: copy the
template, start the server, and watch the workspace assemble itself on screen as the
conversation runs.

## Where a rule lives

A rule is not written twice — it is **factored once**. Every rule the overview states
splits into two parts, and each part lives where it belongs:

- The **enforceable core** — the predicate a machine can check with no judgment — goes
  to the hard layer: a schema constraint, a tool that refuses, a validator check. "An
  issue cites only included articles" is a core; the assemble tool refuses it, and no
  capability restates it.
- The **judgment remainder** — the part that needs a reader — goes to a capability:
  what counts as relevant, how to weigh the borderline case, what a good reason looks
  like. No deterministic tool can hold it.

The factoring is the design act, and it has a direction: **push everything checkable
into the hard layer**, because enforcement holds when nobody — human or model — is
paying attention; leave in language only what genuinely needs judgment.

The split is rarely even, and either side can be empty. Some rules are all core ("one
record per PMID" — nothing to judge; the tool *is* the rule, and no capability
shadows it). Some are all remainder (tablethat's bottom-line rule — pure judgment,
deliberately unenforced). Most land apart: the lit-review's citation rule puts
"findings cite only included sources" in `tools/add_finding.py` and "what makes a
claim a finding" in `capabilities/findings-and-citations.md` — two *different parts*
of one rule, each written once.

What the two layers must never hold is two statements of the same part. A capability
that restates what a tool already refuses is a second derivation of one rule — the
[one-definition](#one-definition-of-every-number) failure, in prose: the copies drift,
and a reader eventually trusts the wrong one. A capability *cites* the enforcement
("the tool refuses X; here is how to decide Y"); it never repeats it.

## In-context and delegated

A capability is a unit of procedure written in language. Whether it is read into the
current conversation or handed to a fresh agent is a property of **how it runs**, not of
what it is — so both live in `capabilities/`, and each declares its mode in frontmatter:

| `runs:` | Meaning | Use when |
|---|---|---|
| `in-context` | The agent reads it and acts, here, in the conversation. | The reasoning *is* the product, or the user is steering it. Judgment the conversation needs to witness. |
| `delegated` | Handed to a fresh agent with its own context; only its return value comes back. | The byproducts are bulky and disposable — a fan-out over many items, a deep read of one source — and only the conclusion, or the write it makes, matters. |
| `either` | **Ambidextrous.** The same procedure, run either way; the caller decides. | One item in conversation, forty delegated one-per-item. Screening one paper is a conversation; screening a week's retrieval is a fan-out. |

A capability that can be delegated declares a **contract** — a `returns:` line saying what
comes back — because the return value is the *only* thing that does. The transcript is
thrown away.

**Why a workspace can delegate freely.** In an ordinary agent, delegation is a gamble: the
sub-agent has never read the rules, so it may not respect them. Here it doesn't need to.
The workspace's memory is the substrate, not the conversation, and every rule's
[enforceable core](#where-a-rule-lives) is in the tools. A filter's verdicts land through
the verdict tool, which *refuses* one with no reason — whoever holds the pen, delegate or
caller, and whether or not they ever read the filter capability. **Delegation is cheap
because the files remember and the tools refuse.**

Three constraints follow:

1. **A delegate's results land in the substrate; its transcript is disposable.** Two
   honest shapes. The delegate writes through the tools itself — right when each item's
   work is self-contained. Or it is a **pure analysis**: it returns its findings and the
   *caller* writes them through the tools — right when the write needs the caller's
   context (batching, ordering, a gate ahead) or the analysis has more than one consumer
   (the same filter serves the weekly pipeline and a one-off re-check, and a test run
   should touch nothing). What a delegate must never do is leave results only in its
   transcript.
2. **Delegation may not launder a gate.** If a rule requires the user's approval, a fresh
   agent cannot supply it on their behalf. Gates are answered in the conversation, always.
3. **Delegation does not soften a rule.** A delegated capability is still judgment; the
   enforcer is still the tool. A capability that can only be trusted when its reader is
   paying attention is one whose enforceable core hasn't been factored into a tool yet.

The context economics are the whole point: the work that would flood a conversation with
search results, page text, and dead ends is exactly the work whose *conclusions* are small.
Delegate the flood, keep the conclusion, let the files hold the rest.

## One definition of every number

The data-access layer the kit ships (`tools/repo.py`) is the **only door to the record**.
Writes go through it in conformance with the schemas. Reads come at two altitudes:
**primitives** — load a record, load them all; domain-blind plumbing, shipped — and
**named queries** — a question about the record ("how's screening going?"), written down
once and recomputed from the files on every ask; grown one by one. Every tool and every
view routes through this layer; nothing else opens the data files or re-derives a number.
The kit supplies the layer; the workspace's discipline is routing everything through it.

A named query belongs to a *question*, never to a consumer: the live board and the
assembled report render the same query, and the registry (`QUERIES`) is nothing more than
the list of queries published to the dashboard. A query may *format* its answer — titles,
citations, human-shaped cards — but any fact it computes exists nowhere else. The reason
is the same as [where a rule lives](#where-a-rule-lives): what matters is
written down once, where everything that needs it can reach it. Two independent
derivations of one number will eventually disagree — and an answer that disagrees with
the substrate is a confident lie.

**Queries take parameters**, because some questions are only well-posed about one thing:
not "every table" but "table T-001". A query may declare keyword arguments, and the URL's
query string fills them — `/api/table?table_id=T-001` and `/view/table?table_id=T-001`
ask the same question of the same query, one as data and one as a page. Without this, a
workspace can only ask whole-record questions, and every page carries the whole record.

A parameter **narrows a question; it never changes which question is asked.** If a
parameter would switch the shape of the answer — a `mode=`, a `format=` — that is two
questions wearing one name, and it wants two queries. The [worked
example](../examples/tablethat/) draws the line where it belongs: `tables` answers *what
tables exist* and never carries a row; `table(table_id=…)` answers *what this one says*.
Neither is a mode of the other.

Two obligations come with a parameterized query. It gives every parameter a default and
answers a bare ask helpfully, because the dashboard's index links every published query
with no arguments. And its live page must poll with its own query string, or it will
repaint itself with another thing's data.

The same discipline applies to the system's own registries. A record kind is declared
**once, in its schema**: `x-kind` names the `data/` folder, and the id pattern carries
the id prefix and width. `repo.py` derives its kind table from `schemas/` at import —
there is no second list to keep aligned — and `validate.py` backstops the seam, flagging
any schema that declares no kind and any `data/` folder no schema governs (which would
otherwise sit outside validation, silently). Growing a kind is one act: writing the
schema.

## The anatomy of a view

Every view separates four parts:

| Part | What it is | Lives in | Ships or grown |
|---|---|---|---|
| **Data access** | reads the record; defines the named queries views render | `tools/repo.py` | layer ships · queries grown |
| **Code** | binds a query's answer into a rendering | `tools/` (the server; build tools) | server ships · build tools grown |
| **Template** | the presentation markup | `views/` | index ships · domain templates grown |
| **Instance** | the rendered result | live: nowhere — served on demand · static: **on the record it renders** (a body field the schema governs, written by the tool); a file copy is an on-demand export, never stored state | — |

Two kinds of view fall out of the instance row:

- **Live views** are the default: grow a named query in `repo.py` and a template in
  `views/` with the same name, and the shipped server binds them with no wiring — the
  page at `/view/<name>`, the answer it polls at `/api/<name>`, and a card on the index
  the moment the template exists. If the query takes parameters, the page takes them too,
  from its own URL — so **one template serves a whole class of pages** (the example's
  table viewer renders every table the workspace will ever hold; new tables cost no new
  view). The binding contract allows a **null** answer (a server whose registry doesn't
  know the query yet — a process older than the view); a template renders a note for
  that case and lets its poll recover — it never crashes on it. A live view **cannot go
  stale** — every ask recomputes
  the answer from the files; it is the logical endpoint of "regenerate views after data
  changes", not an exception to it. And the page adds nothing to the truth: a live view
  holds no state of its own, writes nothing, and creates no second source — the files
  remain the ground truth under it. (Writing, where a workspace wants it, is a separate
  opt-in surface — see [actions](#actions-when-the-dashboard-should-do) — never something
  a view does.)
- **Static views** are for content that must outlive a page — the report, the
  newsletter, the deliverable. A grown build tool assembles the content from the same
  queries and stores it **on the record itself**, in a schema-governed field,
  regenerated after every data change, never hand-edited. Nothing rendered persists
  outside `data/`: a loose rendered file is a record outside the law — unvalidated, and
  a second copy of the truth that can silently go stale. When a copy must actually
  leave the workspace — an email, a client attachment — the tool *exports* one on
  demand: a snapshot for sending, never the truth.

So the cost of a new way of seeing is exactly two grown pieces — a query and a
template — and the [worked example](../examples/lit-review/JOURNEY.md) shows both kinds: a live
screening board, and a report assembled to a file.

### Why the live page polls

Liveness is polling, and that is a consequence of the design, not a compromise. The
truth lives in files, and the write side is deliberately open — any tool, or a hand with
a text editor, may change the record. For a server to *push*, it would have to know the
moment something changed: either it watches the files on a loop (polling, relocated into
the server, plus connection state it exists to not have), or every writer takes on a duty
to notify (liveness stops being structural and becomes something a writer can forget).
Polling keeps change detection where it is free — at read time, because queries recompute
from the record on every ask. The server stays stateless and stdlib; watching stays
harmless.

If a workspace ever outgrows this, the sanctioned escalations, in order: first a
freshness short-circuit (the server answers "unchanged" from the record's modification
times without recomputing), then server-sent events — one-directional, plain HTTP. Not
websockets: their distinguishing feature is a persistent channel held open *back* from the
page, and liveness needs none — reads are polled, and the write actions a workspace may
grow are ordinary request/response POSTs, not a standing back-channel.

## Actions — when the dashboard should do

The dashboard is a projection: it shows the record, and by default it only shows. But some
work wants a verb on the page — *set this aside*, *mark that done* — rather than a trip back
to the conversation for every change. For that a workspace grows an **action**: the write
counterpart of a query.

An action is an ordinary workspace write operation. It goes through the same `repo` door and
the same schema rules an enforcer tool would — and the rule should live in **one** place a
CLI tool and the button both call, so nothing restates it. Publishing it in `repo.ACTIONS`
also exposes it over `POST /action/<name>`, called with the request's JSON body as keyword
arguments. The registry is empty by default, so most dashboards write nothing and are
read-only in effect; GET never reaches an action, so a stray read can't mutate.

What actions do **not** change: the server still holds no state of its own and adds no second
source of truth. An action mutates the files through `repo`, exactly as the conversation
would — the button is a shortcut to a tool, not a new authority. The
[session-tracker](../examples/session-tracker/) grows `archive` and `unarchive` this way: a
card button POSTs the action, the contained record changes, and the next poll shows it.

## Contained and bound substrates

`data/` is the *contained* case — the workspace is the system of record. The concept
equally covers *bound* substrates: the records live in a CRM, a drive, a database, and the
workspace holds the reach (a tool), the meaning (schemas and capabilities describing what the
external data means here), and the named queries. Most real workspaces mix both — the worked
example seeds its contained data *from* a bound source (the client's file in `seed/`).

**A bound type still gets a schema.** The schema is the declaration of a *type* — the shape
and validity of a thing the workspace reasons about — and that is worth writing down
whether or not a record of it ever lands in `data/`. So a bound kind belongs in `schemas/`
exactly like a contained one; it simply declares where its records really live and has no
`data/` folder:

```json
{ "x-kind": "session",
  "x-source": "~/.claude/projects/<project>/<uuid>.jsonl (read-only)",
  "x-projection": "sessions",
  ...the fields, with types... }
```

Three consequences. **The type is complete:** every kind the capabilities touch has a
declaration, so a reader learns the whole vocabulary from `schemas/`, not half from
`schemas/` and half from a query's return shape. **The id pattern is contained-only:** a
bound kind's ids come from the foreign system (a uuid, a row key), so it carries no
`data/`-style id pattern and the kit never mints ids for it. **The schema can still bite:**
where a contained kind is validated against the files in `data/`, a bound kind is validated
against *what the reach returns* — `x-projection` names the query that materializes it, and
`validate.py` can check each projected record against the schema. The rule "schemas are law"
holds on both sides of the boundary; only the thing being checked differs — files here,
the projection there. The [session-tracker example](../examples/session-tracker/) is the
pure case: no `data/`, no contained kind, and two bound schemas (`session`, `subagent`)
that are the entire meaning layer.

## Deliverables are assembled, never authored

The workspace's outputs — the report, the export, the dashboard — are **assembled from the
substrate by tools, never hand-written**. That's what makes guarantees structural: the
example's report *cannot* cite an excluded paper, because findings can't exist against one.
A dashboard served live is the same discipline — the server just re-asks the queries on
every request instead of freezing their answers to disk. And when a deliverable is
assembled, the assembled content is still data: it lives on the record, under its schema
(see the instance row above) — the deliverable *file* is an export of the record, made on
demand, owned by whoever it's sent to.
