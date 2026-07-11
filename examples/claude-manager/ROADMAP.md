# Claude Manager — Roadmap

A global Claude Code manager: a bound lens over `~/.claude` (and, increasingly, project
`.claude/` dirs), one module per concern. Built and planned work, in priority order.

## Built

- **Overview** — the cockpit: at-a-glance numbers, what's live, what needs attention.
- **Sessions** — every session; filter by age / last-active / archived; two grades of
  alive; per-session summaries (delegated) + archive (a write **action**).
- **Usage** — activity over time, volume only: prompts/day from `history.jsonl`, enriched
  with `stats-cache.json` message/tool counts where it reaches.
- **Extensions** — plugins / skills / agents / commands / MCP in one bound `extension`
  type. **Needs a second pass — see below.**

## Next up

### 1. Extensions, reorganized by *scope* and *state*
The first cut conflates three very different things and misses the user's real
extensions. What we learned (2026-07-10) working out "where are all these agents?":

- The 24 agents shown are **all from the marketplace catalog** (`plugins/marketplaces/…`),
  and **none are installed** — they're plugins available *to* install (code-modernization,
  pr-review-toolkit, feature-dev, …), not active.
- The two actually-installed plugins (pyright-lsp, orchestra) ship **zero agents**, and
  both are **disabled** in settings anyway.
- The user's **real, working agents are project-scoped** — `table-that/.claude/agents`
  (2), `kh/.claude/agents` (2), `openreview/.claude/agents` (1) — which the manager
  **isn't reading at all** (it only looks in `~/.claude`). Same for project skills
  (table-that: 8, kh: 4).

So Extensions must model two axes, not one `installed` bool:
- **scope**: `user` (`~/.claude`) · `project` (`<proj>/.claude`) · `plugin` (shipped by an
  installed plugin) · `marketplace` (catalog, not installed).
- **state**: `active` (affecting Claude now) · `disabled` (installed/enabled-off) ·
  `available` (installable). Lead the UI with **active**; tuck **available** behind a
  filter. Show plugin enabled/disabled prominently.
- **Read project `.claude/` dirs** — enumerate projects from session cwds, scan each for
  `agents`/`commands`/`skills`. This is where the user's real extensions live.

### 2. Workspace inspector (living-workspace-aware)
Point it at a living workspace and report its anatomy — capabilities, tools, schemas,
views, data (counts, health). The manager inspecting living workspaces (meta). Ties into:

### 3. Dev-visualization capability for living workspaces
A reusable **skill** that visualizes a living workspace in a dev-friendly way, for use
while building out a space's capabilities. **Trigger (the load-bearing idea):** surface it
exactly when the next move / hop / step is to **grow capability** rather than **take a step
forward** — the [move rule](../../canon/the-move-rule.md)'s "grow it" branch. Likely
belongs at the **kit/canon level**, not just this workspace.

### 4. Extension usage — "what earns its keep"
Invocation counts per skill/agent/command, from a cached transcript scan (deferred until
the invocation format is pinned — 0 `Skill` tool-uses found in sampled transcripts).

### 5. Deeper
Token/cost (parse transcript usage records), plugin enable/disable **actions**, a
settings/health read.

## Kit-level dashboard technology (bigger than this workspace — touches canon + kit)

- **Multi-tabbed surface, first-class.** The shared top-nav hand-rolled across these views
  is a preview; the kit should support multi-view/tabbed dashboards natively.
- **Collaboration surfaces** projected from the substrate (multi-user / shared).
