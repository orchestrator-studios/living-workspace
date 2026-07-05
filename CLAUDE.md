# This repo is a living workspace

The structures below are not project scaffolding. Together with the agent reading this file,
they are an application — one that starts empty and comes to life through conversation.

| Structure | What lives here |
|---|---|
| `OVERVIEW.md` | What this system is: purpose, entities, rules, existing data sources, recurring asks. Filled in first, by interview. |
| `data/` | The application's persistent objects — the system of record. |
| `schemas/` | The structure and validity rules for everything in `data/`. |
| `tools/` | Deterministic operations: create, update, validate, query, transform. |
| `skills/` | Operational knowledge: workflow rules, state transitions, how to use the tools correctly. |
| `views/` | Visualizations of the data, generated and regenerated as the data changes. |

## Operating rules

1. **The overview comes first.** If `OVERVIEW.md` is still the unfilled skeleton, your first job
   is an interview: ask about purpose, the things the work is made of, the rules that must hold,
   where the data lives today, and what will be asked of the system — and write the answers into
   `OVERVIEW.md`. Do not create schemas until the overview is agreed.
2. **Schemas are law.** Never write to `data/` except in conformance with `schemas/`. After any
   write, validate: `python tools/validate.py` (once it exists).
3. **Prefer tools over hand-edits.** When a tool exists for an operation, use it — tools carry
   the rules that free-form edits would skip.
4. **Read the relevant skill before acting.** Workflow rules live in `skills/`; consult the one
   that covers the operation at hand.
5. **Regenerate views after data changes.** Views are projections; they are cheap to rebuild and
   must never be hand-edited out of sync with the data.
6. **Grow the workspace as a side effect of the work.** When an operation repeats, propose a tool.
   When a rule is stated, capture it as a skill. When scanning beats asking, propose a view.
   New capability is added in place — there is no deploy step.

## On entry

Read `OVERVIEW.md`, then `schemas/`, then skim `skills/`, then take the user's request.
If everything is empty, start the interview (rule 1).
