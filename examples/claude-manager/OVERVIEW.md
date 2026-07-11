# System Overview

*Drafted at intake from the spec Cliff gave (2026-07-10) plus a look at the real
`~/.claude/` layout on this machine.*

## Purpose

A **global Claude Code manager**: a live dashboard over the whole Claude Code install on
this machine, one module per concern, all lensing the same `~/.claude/` state directory.
It began as (and still leads with) a **session tracker** and grows outward from there.

Modules today:
- **Overview** — the cockpit: at-a-glance numbers across every module, what's live now,
  and what needs attention. The front door (`/view/overview`).
- **Sessions** — every Claude Code session: filter by age / last-active / archived, two
  grades of alive (**recently active** = touched in the last few minutes; **currently
  active** = the transcript changed within the last 2 seconds), per-session summaries, and
  archive.
- **Usage** — activity over time (volume): prompts per day, busiest projects, and Claude
  Code's own message/tool counts where its stats cache reaches.
- **Extensions** — everything installed that extends Claude, unified: plugins, skills,
  agents, commands, and MCP servers. One bound `extension` type (a `kind` tag rather than
  five near-identical schemas), filterable by kind and installed/available.

Planned next:
- **Workspace inspector** — a living-workspace-aware module: point it at a workspace and
  report its anatomy (capabilities, tools, schemas, views, data). It should tie into a
  reusable **dev-visualization capability** for living workspaces — the thing to surface
  precisely when the next move is *grow capability* rather than *take a step* (the move
  rule's "grow it" branch), while developing a space.
- **Extension usage** — how often each skill/agent/command is actually invoked (a cached
  transcript scan, once the invocation format is pinned down) — "what earns its keep."
- Deeper: token/cost (parse transcript usage records), plugin enable/disable **actions**,
  a settings/health read.

Dashboard-technology asks (kit-level, not this workspace alone): make the **multi-tabbed
surface** first-class (the shared nav is a hand-rolled preview of it), and support
**collaboration surfaces** projected from the substrate.

## The substrate is bound, not contained

This workspace **owns no data**. The system of record is Claude Code's own state
directory, `~/.claude/`, and the tracker is a *live lens* over it — it reads, never
writes, and never copies. `data/` stays empty on purpose. But `schemas/` is **not** empty:
the types this workspace reasons about — `session` and `subagent` — are declared there
even though their records live in `~/.claude`, because a schema is the declaration of a
*type*, worth writing whether or not a record ever lands in `data/`
([canon/anatomy.md](../../canon/anatomy.md#contained-and-bound-substrates)). Those schemas
are marked bound (`x-substrate: bound`, `x-source`), carry no `data/`-style id, and are
validated against **what the reach returns** — `session.schema.json` names its projection
(`sessions`) and `tools/validate.py` checks every projected row against it. So the
workspace's knowledge lives in the **meaning** (`schemas/` + `capabilities/`) and the
**reach** (`tools/repo.py`); only contained *records* are absent.

Copying would be the wrong architecture twice over: it would go stale the instant it was
written, and "currently active" is *only* knowable from the live file — a cached mtime is
a contradiction in terms.

## The things

- **session** (`schemas/session.schema.json`, bound) — one Claude Code session: a
  transcript at `~/.claude/projects/<encoded-project>/<uuid>.jsonl`. Its id is the uuid;
  its true project path is the `cwd` recorded *inside* the transcript (the folder name is
  a lossy encoding — never decode it when the content is authoritative); its last-active
  time is the file's mtime; its age is the file's creation time. It also carries its
  **opening prompt, last prompt, and last response** (read from the head and tail of the
  transcript).
- **subagent** (`schemas/subagent.schema.json`, bound) — a child of a session, under
  `<uuid>/subagents/agent-*.jsonl`. Not a session in its own right; counted as a detail
  of its parent, never listed as top-level. Declared as a type, not yet projected.
- **usage_day** (`schemas/usage_day.schema.json`, bound) — one calendar day of activity:
  `prompts` from `history.jsonl` (complete, current), and `messages`/`tool_calls`/
  `sessions` from `stats-cache.json` where that cache reaches (null past its cutoff). The
  Usage module's time series.
- **summary** (`schemas/summary.schema.json`, **contained**) — a generated synthesis of
  one session, one per session, stored in `data/summary/<uuid>.json`. The record carries
  a **watermark** (`source_size`, the transcript's byte size when summarized) so the
  trigger algo can tell when a summary has gone stale.
- **archive** (`schemas/archive.schema.json`, **contained**) — a session the user has set
  aside, one record per archived session in `data/archive/<uuid>.json`. Presence *is* the
  archived state; unarchiving deletes the record. Because a session is bound (read-only in
  `~/.claude`), "archived" cannot live on it — it is workspace-owned state, like a summary.

The summary and archive kinds are the things the workspace *owns* and writes — so the
tracker is a **bound + contained mix**: it reads sessions from `~/.claude` and writes its
own derived/decision state (summaries, archives) about them here.

## The rules

1. **Read-only, always.** The tracker never writes to `~/.claude/`. No tool in this
   workspace opens that tree for anything but reading.
2. **The transcript's `cwd` is the authoritative project path.** Folder names encode the
   path lossily (separators become `-`, and real names contain `-` too); resolve the path
   from file content, fall back to the raw folder name, never guess a decode.
3. **Two definitions of active, defined once.** *Currently active* = mtime within
   **2 seconds**. *Recently active* = mtime within **5 minutes**. Both live as constants
   in `repo.py` and travel in the projection so views label them without redefining.
4. **The poll interval is the currently-active window.** The dashboard polls every 2s and
   "currently active" is a 2s window — so a session being typed in is caught on the very
   next tick. This alignment is intentional (Cliff's spec).
5. **Cheap enough to poll.** The catalog is answered from `stat()` (timing) plus a cached
   first-line read (project path) — ~6ms to stat, ~70ms to resolve paths cold, then
   stat-only in steady state. Never parse whole transcripts to build the list; parse one
   only when a session is opened in detail.

## Where the data lives today

- **Bound, read-only:** `~/.claude/projects/*/*.jsonl` (session transcripts),
  `~/.claude/projects/*/<uuid>/subagents/*.jsonl` (subagents),
  `~/.claude/history.jsonl` (global prompt log, available for future enrichment). The
  home is `~/.claude` unless `CLAUDE_HOME` overrides it.
- Nothing to migrate; nothing seeded.

## What you'll ask of it

- **The board:** "What sessions are there?" → the live list, most-recently-active first.
- **Liveness:** "What's running right now?" → the currently-active pulse; "what's been
  touched lately?" → the recently-active filter.
- **Filter:** by age (today / this week / older), by last-active (live / minutes / hours
  / days), and by archived (hide / show / only — hidden by default); plus search across
  project, path, prompts, and summary.
- **Archive:** set a session aside — from the board (each card's **archive/unarchive**
  button) or in conversation (`tools/archive_session.py`, or just ask). Both call the same
  `repo.archive`/`repo.unarchive`, so the rule has one home; the board drops archived
  sessions from the default view and the summary queue. This is the workspace's **one
  write surface**: the archive/unarchive actions are published in `repo.ACTIONS` and served
  over `POST /action/<name>` by the kit server (the write counterpart of queries, empty in
  every other workspace). Everything else here stays a read-only lens.
- **Drill in:** open one session → its parsed detail (turn counts, first/last prompt, last
  response, model, git branch, subagent count, and its summary if one exists).
- **Summarize:** "summarize what's due" → the trigger algo `summaries_due()` names the
  settled, materially-changed sessions; the **delegated** `summarize-session` capability
  reads each transcript in its own context and writes the summary through
  `tools/write_summary.py`. The algo decides *when* (deterministic), the agent does *what*
  (judgment) — and because the summary is delegated, reading hundreds of megabytes of
  transcript never touches the conversation you are working in. Staleness knobs:
  `SUMMARY_SETTLE_S` (don't summarize until idle this long) and `SUMMARY_GROWTH_BYTES`
  (resummarize once the transcript grows this much past the watermark), both in `repo.py`.
- **Later (grow on demand):** join `history.jsonl` for the opening prompt without parsing
  the transcript; per-project rollups; a "currently active across all projects" ticker;
  project the `subagent` kind.
