---
name: visualize-workspace
description: See a living workspace's anatomy — schemas, tools, capabilities, views, data,
  health — in the dev-friendly Workspaces module. Reach for it when the next move is to
  GROW capability, not take a step.
runs: in-context
---

# Visualizing a living workspace

The manager's **Workspaces** module (`/view/workspaces`, and a per-workspace anatomy at
`/view/workspace?workspace_id=<name>`) is a live X-ray of a living workspace: its schemas
(with substrate and projection), tools (kit vs grown), capabilities (with how each runs),
views (and the query each binds), data record counts, and a static health read. It updates
as you edit the workspace's files — it's a dev instrument, not a report.

## When to reach for it

Work in a living workspace alternates between two kinds of move (the
[move rule](../../../canon/the-move-rule.md)): **do it** — take a step with what exists —
and **grow it** — the step is blocked, so acquire the missing access / understanding /
presentation first. The visualization is for the second kind.

**The trigger: when the next move, hop, or step is to *improve capability* rather than
carry the work forward, bring up the anatomy first.** Concretely, before you:

- add or change a **schema** (a new kind, bound vs contained, a projection) — see what
  kinds exist and how they're wired;
- grow a **tool**, **capability**, or **view** — see what's already there so you extend
  rather than duplicate, and so a new view binds to a real query;
- wonder whether the pieces line up — read the **health** panel: a bound schema whose
  `x-projection` isn't a published query, a grown view that binds to no query, a `data/`
  folder no schema declares.

Growing capability is exactly the moment the map is worth more than the territory: you're
about to change the workspace's *structure*, and the anatomy shows the structure you're
changing. Taking a step forward (running a query, adding a record) rarely needs it.

## How

- The catalog: `/view/workspaces` — every workspace under the repo, counts + health.
- One workspace: click through, or `/view/workspace?workspace_id=tablethat`.
- It reads the files directly and polls, so edit a schema or add a capability and watch the
  panel change — a tight loop while building the space out.

It is read-only: a lens for developing, not a way to mutate the workspace. Changes still
go through that workspace's own tools and conversation.
