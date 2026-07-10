# The Operating Manual — canonical CLAUDE.md, annotated

Every living workspace ships with a `CLAUDE.md` — the manual the agent loads on entry.
The canonical text is below; [`template/CLAUDE.md`](../template/CLAUDE.md) is a verbatim
copy to start from, and each workspace **owns its copy** — a workspace's manual may grow
project-specific rules as it lives. That divergence is a feature: the manual is part of the
workspace, not part of the framework.

The manual assumes the [standard kit](anatomy.md#the-standard-kit) — the domain-agnostic
machinery (`repo.py`, `server.py`, `validate.py`, the dashboard capability, the index
template) that ships in every workspace rather than being grown per project.

## Why each rule exists

1. **The overview comes first** — because every later artifact must trace to an agreed
   statement of what the system is. Schemas invented before the overview is settled encode
   guesses.
2. **Schemas are law** — because a substrate the agent (or the user) can silently bend is
   not a substrate; it's a suggestion. Validation after every write keeps the data
   trustworthy across long sessions and many turns. Making the schema the kind's single
   declaration is the same principle applied to the system's own registries: the kit
   derives the folder mapping and id convention from it, so a kind cannot be
   half-registered, and `validate.py` flags any data folder no schema governs.
3. **Prefer tools over hand-edits** — because tools carry the rules. A hand-edit is a write
   that skips every guarantee the workspace has accumulated.
4. **Reach for the relevant capability before acting** — because capabilities are where
   hard-won procedure lives; ignoring them re-learns old lessons at the user's expense.
   A capability declares how it runs, and that choice is about *context economics*, not
   importance: work whose byproducts are bulky and whose conclusion is small should be
   [delegated](anatomy.md#in-context-and-delegated) to a fresh context. This is safe
   because the workspace's memory is the substrate, not the conversation — the delegate
   writes through the tools, and the tools carry the rules whether or not it read them.
5. **Regenerate views after data changes** — because a stale view is worse than no view:
   it's a confident lie about the substrate. A *live* view — served fresh from the data on
   every request — is this rule fulfilled structurally: it cannot go stale. Growing one is
   the rule's endpoint, not an exception to it.
6. **Do it, or grow it** — the [move rule](the-move-rule.md). This is the rule that makes
   the workspace *living*: capability is added at the moment its absence blocks a want,
   permanently, in place.
7. **Navigate big work from the end** — [the journey](the-journey.md). A move can only be
   judged against a described destination, and a route sketched finer than your knowledge
   is a guess wearing a schedule. The final state and the chunks hold steady; the hops
   absorb all the uncertainty.
8. **One definition of every number** — because two independent derivations of the same
   count will eventually disagree, and every surface that renders it becomes a suspect.
   The kit ships the data-access layer
   (see [anatomy](anatomy.md#one-definition-of-every-number)); the rule is the discipline
   of routing everything through it, so every surface renders the same truth. A query may
   take parameters, because some questions are only well-posed about one thing — but a
   parameter narrows a question, never switches which one is asked.
9. **Keep the dashboard up for the user** — because the dashboard is the user's window
   into the workspace, and a user driving everything through one conversation won't
   launch a second process themselves. A running dashboard is a precondition for data
   work the way validation is a postcondition — and it's how the "living" property
   becomes visible: the user watches capability and content land as they talk.

## Canonical text

```markdown
# This repo is a living workspace

The structures below are not project scaffolding. Together with the agent reading this
file, they are an application — one that starts domain-empty and comes to life through
conversation. A small **standard kit** ships with the workspace: the domain-agnostic
machinery every workspace needs, noted per folder below. Everything domain-shaped —
schemas, records, domain tools, named queries, view templates — is grown, in place, as the
work demands it.

| Structure | What lives here |
|---|---|
| `OVERVIEW.md` | What this system is: purpose, entities, rules, existing data sources, recurring asks. Filled in first, by interview. |
| `data/` | The application's persistent objects — the system of record. Starts empty. |
| `schemas/` | The structure and validity rules for everything in `data/`. Each schema is its kind's single declaration: `x-kind` names the `data/` folder, the id pattern fixes the id format. Starts empty. |
| `tools/` | Deterministic operations: create, update, validate, query, transform. Kit: `repo.py` — the data-access layer every read, write, and named query goes through; `server.py` — the dashboard server; `validate.py` — the schema checker. Domain tools are grown. |
| `capabilities/` | Procedure in language: workflow rules, state transitions, how to use the tools correctly, how to judge. Each declares in frontmatter how it runs — `in-context`, `delegated`, or `either` (ambidextrous). Kit: `dashboard.md`. |
| `views/` | View logic — templates, never rendered output, never a second source of truth. Kit: `index.template.html`. A domain view is grown as a named query in `repo.py` plus a template here; the server serves it live. |

## Operating rules

1. **The overview comes first.** If `OVERVIEW.md` is still the unfilled skeleton, your
   first job is an interview: ask about purpose, the things the work is made of, the rules
   that must hold, where the data lives today, and what will be asked of the system — and
   write the answers into `OVERVIEW.md`. Do not create schemas until the overview is agreed.
2. **Schemas are law.** Never write to `data/` except in conformance with `schemas/`. After
   any write, validate: `python tools/validate.py`. A schema is also its kind's single
   declaration — `x-kind` names its `data/` folder, the id pattern fixes the id format,
   and the kit derives the rest — so growing a kind is one act: writing the schema.
3. **Prefer tools over hand-edits.** When a tool exists for an operation, use it — tools
   carry the rules that free-form edits would skip.
4. **Reach for the relevant capability before acting.** Procedure lives in
   `capabilities/`; consult the one that covers the operation at hand. Each declares how
   it runs: `in-context` (read it and act, here), `delegated` (hand it to a fresh agent
   and keep only what it returns), or `either` — ambidextrous, and you choose. Delegate
   when the work's byproducts are bulky and disposable and only its conclusion or its
   write matters: a fan-out over many items, a deep read of one source. Prefer in-context
   when the reasoning is the product or the user is steering it. A delegate deposits to
   the substrate through the tools, never to the conversation; it can never supply a gate
   that belongs to the user; and it does not soften a rule — the tool still refuses.
5. **Regenerate views after data changes.** A view renders a query's answer; never
   hand-edit one out of sync with the data. Live views — re-asking their query on every
   request — cannot go stale; static ones (the report, the export) are regenerated by the
   tool that assembles them.
6. **Do it, or grow it.** When the user states a want: if it's reachable with the access,
   understanding, and views that already exist — just do it. If it isn't, the next move is
   acquiring what's missing, checked in order: **access** (add the tool or connection),
   **understanding** (write the schema or capability), **presentation** (generate the
   view). Then retry the want. Every gap-fill is deposited permanently, in place — there
   is no deploy step. Signals worth acting on: an operation repeating (→ tool), a rule or
   a judgment being stated (→ capability), the same work flooding the conversation
   (→ mark that capability `delegated`), scanning beating asking (→ view: a named query in
   `repo.py` plus a template in `views/` — the shipped server puts it live with no wiring).
7. **Navigate big work from the end.** When the want is a whole deliverable, not a single
   step: first write down the final state — what will exist when the work is done, and
   what must be true of it — as a file. Then chunk the route coarse: typically about three
   phases, each naming where it ends, not how it goes. Then hop the insides — one visible
   move at a time, applying rule 6 at every hop.
8. **One definition of every number.** `tools/repo.py` is the only door to the record:
   writes go through it in conformance with `schemas/`; reads come as primitives (load a
   record, load them all) or **named queries** — a question about the record, written
   down once, recomputed from the files on every ask. New queries are defined there and
   published in `QUERIES`; nothing else opens `data/` or re-derives a number. A query
   belongs to a question, never to a consumer — the dashboard and the report render the
   same one. Two derivations of one number will eventually disagree. A query may take
   **parameters**, filled from the URL's query string on `/api/<name>` and `/view/<name>`
   alike, for questions only well-posed about one thing (`?table_id=T-001`); give each a
   default, answer a bare ask helpfully, and have the live page poll with its own
   `location.search`. A parameter narrows a question — if it switches the answer's shape,
   that's two questions wearing one name.
9. **Keep the dashboard up for the user.** The live dashboard is how the user watches the
   workspace move; they won't start the server themselves. At the first data-touching
   action of a session, make sure `tools/server.py` is running — probe `/health` first,
   never double-launch — and give the user the link once. Recipe:
   `capabilities/dashboard.md`.

## On entry

Read `OVERVIEW.md`, then `schemas/`, then skim `capabilities/` (names, descriptions, and
how each runs), then take the user's request. If everything is empty, start the interview
(rule 1). When the request touches the data, bring the dashboard up first (rule 9) so the
user can watch the workspace work.
```
