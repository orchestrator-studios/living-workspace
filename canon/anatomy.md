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
| `schemas/` | The structure and validity of everything in `data/`. Each schema is its kind's **single declaration**: `x-kind` names the `data/` folder, the id pattern fixes the id format, and the kit derives everything else from it. | understanding |
| `tools/` | Deterministic operations: create, update, validate, query, transform, assemble. Three residents: the **data-access layer** (`repo.py`, shipped — see [one definition of every number](#one-definition-of-every-number)), **muscle** (pure operations, grown) and **enforcers** (operations that carry rules — the dedup check, the citation gate; grown). The kit's `server.py` and `validate.py` live here too. | access · enforcement |
| `skills/` | Workflow rules and know-how in language — how to use the tools correctly, what to watch for. The soft form of the same rules the enforcer tools carry in code. The kit ships one: `dashboard.md`. | understanding |
| `views/` | View **logic** — templates, never rendered output, never a second source of truth. The kit ships `index.template.html`; domain views are grown (see [the anatomy of a view](#the-anatomy-of-a-view)). | presentation |

## The standard kit

Not everything is grown. A small set of machinery is **domain-agnostic, identical in every
workspace, and encodes zero domain knowledge** — making each workspace re-derive it teaches
nothing and costs the user real time. That set ships with the template:

| Ships | What it is |
|---|---|
| `tools/repo.py` | The data-access layer, as a skeleton: paths, the CRUD primitives (load/save/next-id conventions), the kind table derived from `schemas/` at import, and an empty query registry. |
| `tools/server.py` | The dashboard server: the index at `/`, any template at `/view/<name>`, any published query at `/api/<name>`, `/health`. Stdlib only, read-only, holds no state. |
| `tools/validate.py` | The generic schema checker plus the alignment backstop (every schema declares its kind; every `data/` folder is governed by a schema); the workspace grows its cross-record integrity rules into it, in place. |
| `skills/dashboard.md` | The keep-the-server-up recipe: probe, background-launch, hand over the link once. |
| `views/index.template.html` | The dashboard's index page — views and queries appear on it as they come into existence. |

The test for shipping is strict, and it is the same line the move rule draws: **the kit is
the system's machinery; everything the *domain* shapes is grown.** Schemas, records, domain
tools, named queries, and view templates never ship — they are the workspace coming to life.
The payoff of the kit is that the workspace is *visible from minute one*: copy the
template, start the server, and watch the workspace assemble itself on screen as the
conversation runs.

## Two forms of every rule

A rule that matters exists **twice**: once in language (a skill — for the agent to reason
with) and once in enforcement (a schema constraint or an enforcer tool — for when nobody,
human or model, is paying attention). The example's citation-closure rule is the pattern:
stated in `skills/findings-and-citations.md`, enforced by `tools/add_finding.py`, checked
globally by `tools/validate.py`.

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
is the same as [two forms of every rule](#two-forms-of-every-rule): what matters is
written down once, where everything that needs it can reach it. Two independent
derivations of one number will eventually disagree — and an answer that disagrees with
the substrate is a confident lie.

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
| **Instance** | the rendered result | live: nowhere — served on demand · static: at the root if it *is* the deliverable, else next to the data it renders | — |

Two kinds of view fall out of the instance row:

- **Live views** are the default: grow a named query in `repo.py` and a template in
  `views/` with the same name, and the shipped server binds them with no wiring — the
  page at `/view/<name>`, the answer it polls at `/api/<name>`, and a card on the index
  the moment the template exists. A live view **cannot go stale** — every ask recomputes
  the answer from the files; it is the logical endpoint of "regenerate views after data
  changes", not an exception to it. And the page adds nothing to the truth: the server
  holds no state of its own, writes nothing, and creates no second source — the files
  remain the ground truth under it.
- **Static views** are for outputs that must exist as files — the report, the export,
  the deliverable. A grown build tool renders them from the same queries, and they are
  regenerated after every data change, never hand-edited.

So the cost of a new way of seeing is exactly two grown pieces — a query and a
template — and the [worked example](../example/JOURNEY.md) shows both kinds: a live
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
websockets: their distinguishing feature is a channel *back* from the page, and this
surface is read-only by design.

## Contained and bound substrates

`data/` is the *contained* case — the workspace is the system of record. The concept
equally covers *bound* substrates: the records live in a CRM, a drive, a database, and the
workspace holds the reach (a tool), the meaning (schemas and skills describing what the
external data means here), and the named queries. Most real workspaces mix both — the worked
example seeds its contained data *from* a bound source (the client's file in `seed/`).

## Deliverables are assembled, never authored

The workspace's outputs — the report, the export, the dashboard — are **assembled from the
substrate by tools, never hand-written**. That's what makes guarantees structural: the
example's report *cannot* cite an excluded paper, because findings can't exist against one.
A dashboard served live is the same discipline — the server just re-asks the queries on
every request instead of freezing their answers to disk.
