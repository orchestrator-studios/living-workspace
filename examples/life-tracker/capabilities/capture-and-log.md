---
name: capture-and-log
description: Landing life in the record — capturing projects and actions from any
  conversation, logging progress, completing work, and beaming the board after.
  Use whenever the user mentions something that happened or something to do.
runs: in-context
---

# Capability: capture and log

*Runs in-context: capture is a judgment call about what the user just said — which
area, which project, is this new or progress on something known — and the user is
steering it. The writes themselves are one tool call each.*

The user talks about his life; the record is where it lands (OVERVIEW rule 3 — the
record, not the chat, is the memory). Every mention of something to do, something
that happened, or something finished is a capture opportunity. Don't ask permission
to record — recording is the system's job; do ask when the *placement* is genuinely
ambiguous.

## Routing what you heard

- **A new outcome** ("I need to deal with the storage unit") → find the area, then
  `python tools/add_project.py AR-## "title" --done-when "..."` — and immediately ask
  for (or propose) the first concrete action, so it doesn't start life stalled.
  Not urgent, just someday? `--status someday`.
- **A new step on known work** ("next I should call the DMV") →
  `python tools/add_action.py P-### "call the DMV" [--follow-up YYYY-MM-DD] [--note "..."]`.
  Set a follow-up only when there's a real date something resurfaces (a callback, an
  appointment, "give it two weeks"); otherwise let staleness carry it.
- **Progress or a blocker** ("called — they need the title first") →
  `python tools/log.py A-#### "called 7/11 — they need the title first" [--follow-up ...]`.
  Log verbatim enough that next month's session reconstructs the state from the entry
  alone. If the news changes when this resurfaces, move the follow-up in the same call.
- **Something finished** → `python tools/done.py A-#### [--note "how it ended"]` or
  `python tools/done.py P-###`. The tool dates it (rule 4) and tells you if the
  project just stalled — relay that and get the next action decided while the
  context is warm.

## After the writes

1. `python tools/validate.py` — the stalled warnings it prints are signal, not noise;
   surface them.
2. End of a work session (not after every single write):
   `python tools/beam_board.py` — the BotBeam tab is regenerated from the substrate
   (rule 5), never hand-edited.

## What this capability does not decide

*What* the next action on a stalled project should be, and what to run down today
beyond the placeholder ordering — both are open questions (OVERVIEW), settled in
conversation with the user, not by this procedure.
