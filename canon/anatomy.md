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
| `tools/` | Deterministic operations: create, update, validate, query, transform, assemble. Two roles: **muscle** (pure operations) and **enforcer** (operations that carry rules — the dedup check, the citation gate). | access · enforcement |
| `skills/` | Workflow rules and know-how in language — how to use the tools correctly, what to watch for. The soft form of the same rules the enforcer tools carry in code. | understanding |
| `views/` | Generated ways of seeing the data: boards, tables, reports. Projections — regenerated after every change, never hand-edited, never a second source of truth. | presentation |

## Two forms of every rule

A rule that matters exists **twice**: once in language (a skill — for the agent to reason
with) and once in enforcement (a schema constraint or an enforcer tool — for when nobody,
human or model, is paying attention). The example's citation-closure rule is the pattern:
stated in `skills/findings-and-citations.md`, enforced by `tools/add_finding.py`, checked
globally by `tools/validate.py`.

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
