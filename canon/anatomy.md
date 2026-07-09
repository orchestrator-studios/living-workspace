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
| `tools/` | Deterministic operations: create, update, validate, query, transform, assemble. Two roles: **muscle** (pure operations) and **enforcer** (operations that carry rules — the dedup check, the citation gate). Once several surfaces read the same data, a third resident appears: the **data-access layer** (see [one definition of every number](#one-definition-of-every-number)). | access · enforcement |
| `skills/` | Workflow rules and know-how in language — how to use the tools correctly, what to watch for. The soft form of the same rules the enforcer tools carry in code. | understanding |
| `views/` | Ways of seeing the data: boards, tables, reports. Projections — never hand-edited, never a second source of truth. Starts holding rendered files; as views mature it holds their **logic** (templates), with instances rendered next to the data they project or served live (see [the anatomy of a view](#the-anatomy-of-a-view--and-how-views-mature)). | presentation |

## Two forms of every rule

A rule that matters exists **twice**: once in language (a skill — for the agent to reason
with) and once in enforcement (a schema constraint or an enforcer tool — for when nobody,
human or model, is paying attention). The example's citation-closure rule is the pattern:
stated in `skills/findings-and-citations.md`, enforced by `tools/add_finding.py`, checked
globally by `tools/validate.py`.

## One definition of every number

The moment two surfaces need the same read of the data — the same count, the same list,
the same derived status — that read is defined **once**, in a data-access layer inside
`tools/` (by convention `repo.py`): the single source of truth for *where* data lives,
*how* it is read and written, and *what the canonical projections are*. Every tool and
every view routes through it; nothing else opens the data files or re-derives a number.

The reason is the same as [two forms of every rule](#two-forms-of-every-rule): what
matters is written down once, where everything that needs it can reach it. Two
independent derivations of one number will eventually disagree — and a projection that
disagrees with the substrate is a confident lie.

## The anatomy of a view — and how views mature

A view starts as the simplest thing that works: one script that reads `data/` and renders
one file. That form is correct — a first view should cost minutes, not structure. Views
earn structure the way everything else here does: at the moment a want blocks without it.

The mature form separates four parts:

| Part | What it is | Lives in |
|---|---|---|
| **Data access** | reads the substrate, defines the canonical projections | `tools/` — the data-access layer |
| **Code** | binds a projection into a rendering | `tools/` (build scripts, the server) |
| **Template** | the presentation markup | `views/` |
| **Instance** | the rendered result | static: next to the data it projects, or at the root if it *is* the deliverable · live: nowhere — served on demand |

Two kinds of view fall out of the instance row:

- **Static views** are rendered to files — the report, the export, the committed board —
  and regenerated after every data change, never hand-edited.
- **Live views** are served: a small read-only server (stdlib is enough — no framework,
  no build step) renders the same templates from the same data-access layer, fresh on
  every request, plus a small JSON API the page can poll. A live view **cannot go
  stale** — it is the logical endpoint of "regenerate views after data changes", not an
  exception to it. And it is still a projection: the server holds no state of its own,
  writes nothing, and adds no second source of truth — the files remain the ground truth
  under it.

The maturation signals are the move rule's, applied to presentation: the same number
derived in two places → extract the data-access layer; markup tangled in build code →
split the template out; regenerate-and-reopen beating watching → grow the live server.
None of this is scaffolding to start with — the template ships none of it, and the
[worked example](../example/JOURNEY.md) grew each piece only when a want blocked.

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
