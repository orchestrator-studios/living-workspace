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
| `schemas/` | The structure and validity of everything in `data/`. | understanding |
| `tools/` | Deterministic operations: create, update, validate, query, transform, assemble. Three residents: the **data-access layer** (`repo.py`, shipped — see [one definition of every number](#one-definition-of-every-number)), **muscle** (pure operations, grown) and **enforcers** (operations that carry rules — the dedup check, the citation gate; grown). The kit's `server.py` and `validate.py` live here too. | access · enforcement |
| `skills/` | Workflow rules and know-how in language — how to use the tools correctly, what to watch for. The soft form of the same rules the enforcer tools carry in code. The kit ships one: `dashboard.md`. | understanding |
| `views/` | View **logic** — templates, never rendered output, never a second source of truth. The kit ships `index.template.html`; domain views are grown (see [the anatomy of a view](#the-anatomy-of-a-view)). | presentation |

## The standard kit

Not everything is grown. A small set of machinery is **domain-agnostic, identical in every
workspace, and encodes zero domain knowledge** — making each workspace re-derive it teaches
nothing and costs the user real time. That set ships with the template:

| Ships | What it is |
|---|---|
| `tools/repo.py` | The data-access layer, as a skeleton: paths, load/save/next-id conventions, and an empty projection registry. |
| `tools/server.py` | The dashboard server: the index at `/`, any template at `/view/<name>`, any projection at `/api/<name>`, `/health`. Stdlib only, read-only, holds no state. |
| `tools/validate.py` | The generic schema checker; the workspace grows its cross-record integrity rules into it, in place. |
| `skills/dashboard.md` | The keep-the-server-up recipe: probe, background-launch, hand over the link once. |
| `views/index.template.html` | The dashboard's index page — views and projections appear on it as they come into existence. |

The test for shipping is strict, and it is the same line the move rule draws: **the kit is
the system's machinery; everything the *domain* shapes is grown.** Schemas, records, domain
tools, projections, and view templates never ship — they are the workspace coming to life.
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

Every read of the data — every count, every list, every derived status — is defined
**once**, in the data-access layer the kit ships (`tools/repo.py`): the single source of
truth for *where* data lives, *how* it is read and written, and *what the canonical
projections are*. Every tool and every view routes through it; nothing else opens the
data files or re-derives a number. The kit supplies the layer; the workspace's discipline
is routing everything through it, and its projections — the canonical derived shapes the
views render — are grown into it one by one.

The reason is the same as [two forms of every rule](#two-forms-of-every-rule): what
matters is written down once, where everything that needs it can reach it. Two
independent derivations of one number will eventually disagree — and a projection that
disagrees with the substrate is a confident lie.

## The anatomy of a view

Every view separates four parts:

| Part | What it is | Lives in | Ships or grown |
|---|---|---|---|
| **Data access** | reads the substrate, defines the canonical projections | `tools/repo.py` | layer ships · projections grown |
| **Code** | binds a projection into a rendering | `tools/` (the server; build tools) | server ships · build tools grown |
| **Template** | the presentation markup | `views/` | index ships · domain templates grown |
| **Instance** | the rendered result | live: nowhere — served on demand · static: at the root if it *is* the deliverable, else next to the data it projects | — |

Two kinds of view fall out of the instance row:

- **Live views** are the default: grow a projection in `repo.py` and a template in
  `views/` with the same name, and the shipped server binds them with no wiring — the
  page at `/view/<name>`, the data it polls at `/api/<name>`, and a card on the index
  the moment the template exists. A live view **cannot go stale** — it is the logical
  endpoint of "regenerate views after data changes", not an exception to it. And it is
  still a projection: the server holds no state of its own, writes nothing, and adds no
  second source of truth — the files remain the ground truth under it.
- **Static views** are for outputs that must exist as files — the report, the export,
  the deliverable. A grown build tool renders them from the same projections, and they
  are regenerated after every data change, never hand-edited.

So the cost of a new way of seeing is exactly two grown pieces — a projection and a
template — and the [worked example](../example/JOURNEY.md) shows both kinds: a live
screening board, and a report assembled to a file.

## Contained and bound substrates

`data/` is the *contained* case — the workspace is the system of record. The concept
equally covers *bound* substrates: the records live in a CRM, a drive, a database, and the
workspace holds the reach (a tool), the meaning (schemas and skills describing what the
external data means here), and the projections. Most real workspaces mix both — the worked
example seeds its contained data *from* a bound source (the client's file in `seed/`).

## Deliverables are projections

The workspace's outputs — the report, the export, the dashboard — are **assembled from the
substrate by tools, never hand-written**. That's what makes guarantees structural: the
example's report *cannot* cite an excluded paper, because findings can't exist against one.
A dashboard served live is still a projection — the server just re-assembles it on every
request instead of freezing it to disk.
