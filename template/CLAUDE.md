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
| `views/` | Ways of seeing the data — projections, never a second source of truth. Starts holding rendered files; as views mature it holds their logic (templates), with instances rendered next to the data they project or served live. |

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
   must never be hand-edited out of sync with the data. A *live* view — served by a local
   server, fresh from the data on every request — cannot go stale: growing one is this rule's
   endpoint, not an exception to it.
6. **Do it, or grow it.** When the user states a want: if it's reachable with the access,
   understanding, and views that already exist — just do it. If it isn't, the next move is
   acquiring what's missing, checked in order: **access** (add the tool or connection),
   **understanding** (write the schema or skill), **presentation** (generate the view). Then
   retry the want. Every gap-fill is deposited permanently, in place — there is no deploy step.
   Signals worth acting on: an operation repeating (→ tool), a rule being stated (→ skill),
   scanning beating asking (→ view), the same number derived in two places (→ data-access
   layer), regenerate-and-reopen beating watching (→ live view).
7. **Navigate big work from the end.** When the want is a whole deliverable, not a single
   step: first write down the final state — what will exist when the work is done, and
   what must be true of it — as a file. Then chunk the route coarse: typically about three
   phases, each naming where it ends, not how it goes. Then hop the insides — one visible
   move at a time, applying rule 6 at every hop.
8. **One definition of every number.** The moment two tools or views need the same read of the
   data — the same count, list, or derived status — define it once in a data-access layer in
   `tools/` (by convention `repo.py`: where data lives, how it is read and written, what the
   canonical projections are) and route every surface through it. Two derivations of one number
   will eventually disagree.

## On entry

Read `OVERVIEW.md`, then `schemas/`, then skim `skills/`, then take the user's request.
If everything is empty, start the interview (rule 1).
