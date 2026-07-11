# System Overview

*Drafted 2026-07-10 from the user's BotBeam backlog (`seed/life-infrastructure-backlog.md`,
pulled from the "Life Infrastructure Backlog" display tab) plus intake interview. Two
questions were deliberately left open at intake — see **Open questions** below; the
placeholders that stand in for them are marked.*

## Purpose

Help the user **run down the open infrastructure of his life** — the standing obligations
across family, health, home, car, and the rest that are nobody's project and therefore
stall: estate planning, doctor follow-ups, car registration, the apartment, the bike, the
cats. The system holds every area's open work, keeps each piece moving with a concrete
next step, preserves context between touches (what happened last call, what's blocked on
what), and answers the daily question: **"what should I run down today?"** This is not a
one-shot deliverable; it is a permanent operational surface.

## The things

- **area** (`AR-##`) — one life domain, from the seed: Family & Legal, Health, Food, Home,
  Car, Bike, Pets. Carries a name and a one-line statement of what "in good shape" means
  there. Areas are few and stable; everything else hangs off them.
- **project** (`P-###`) — one outcome in one area: "estate planning for mom done",
  "car legal in Colorado". Title, `area_id`, a plain statement of what done looks like,
  and status (`open` / `done` / `someday`). Quick errands that need no decomposition are
  still projects — just ones whose single action is the whole job.
- **action** (`A-####`) — one concrete next step on one project: "call the DMV about form
  X". Description, `project_id`, status (`open` / `done`), and a dated **log** of progress
  notes ("called 7/10 — need the title first"), so context survives between sessions.
  *Placeholder (see open question 1):* an optional `follow_up` date — when this should
  resurface if nothing has happened.

## The rules

1. **Everything hangs on the tree.** Every action belongs to an existing project; every
   project to an existing area — cross-record integrity, checked after every write.
2. **An open project always has a next action.** A project with no open action is
   **stalled** — the system's job is to make stalling visible, not silently tolerate it.
   The detectable core (open project, zero open actions) is a validator warning and a
   standing query; deciding *what* the next action should be is judgment, done in
   conversation.
3. **Progress lands in the log.** When something happens on an action — a call, a
   discovery, a blocker — it is recorded as a dated log entry through the tool, not held
   in the conversation. The record, not the chat, is the memory.
4. **Done is dated.** Completing an action or project records when. History is data.
5. **The BotBeam tab is a rendered view, never a source.** The "Life Infrastructure
   Backlog" display is regenerated from the substrate by the beam tool after data
   changes — the static-view discipline pointed at an external surface. It is never
   hand-edited and nothing is read back from it; the seed copy in `seed/` is its frozen
   original.
6. *Placeholder (see open question 2):* **Prioritization is manual for now.** "What
   should I run down today" answers with open actions ordered by follow-up date, then
   staleness (longest since last log entry). No scoring, no urgency model — yet.

## Where the data lives today

- The seed: `seed/life-infrastructure-backlog.md` — the BotBeam tab's content as pulled
  at intake (2026-06-17 vintage). Migrated into `data/` as areas + projects at first
  move; historical after that.
- BotBeam (bound, write-only): the display tab `nnQDZwhG` at `botbeam.ironcliff.ai`,
  reached via the skill script at `C:\code\botbeam\skill\botbeam\scripts\botbeam.py`
  (token in `~/.config/orchestra/botbeam.json`). The workspace beams views *to* it;
  it is not a data source.

## What you'll ask of it

- **The daily driver:** "What should I run down today?" → the needs-attention list
  (rule 6's placeholder ordering, until the prioritization question is settled).
- **Capture on the fly:** "Add: schedule the dentist" → an action (and project, if new)
  lands in the right area from any conversation.
- **Log progress:** "Called the DMV — need form X first" → a dated log entry on the
  action; follow-up moved if warranted.
- **The weekly review:** a recurring sweep — what moved, what stalled, what's `someday`
  that should wake up; follow-ups re-set. A capability with a cadence.
- **The board:** the live dashboard locally, and "beam the board" → the BotBeam tab
  re-rendered from the substrate.

## Open questions (agreed at intake to defer)

1. **The time model.** What makes something "need attention" — follow-up dates on every
   action, real deadlines only, decay/staleness, or something else? Needs a deep
   discussion. Until then: optional `follow_up` on actions, and staleness derived from
   the log.
2. **The prioritization capability.** The user wants the system to *help manage*
   prioritization and tracking — not just list open items — and the shape of that isn't
   known yet (scoring? energy/context tags? a triage conversation? the weekly review
   feeding a ranked queue?). Expected to grow out of using the placeholder and noticing
   where it fails.
