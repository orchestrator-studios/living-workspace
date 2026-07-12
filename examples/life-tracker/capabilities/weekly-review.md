---
name: weekly-review
description: The recurring sweep — what moved, what stalled, what should wake up;
  follow-ups re-set, board re-beamed. Use when the user asks for a review, or when
  a week has passed since the record last moved.
runs: in-context
---

# Capability: the weekly review

*Runs in-context: the review is a conversation — every judgment in it (is this
stalled project still wanted? should this someday wake up?) belongs to the user.
The queries do the gathering; nothing here is bulky enough to delegate.*

The daily driver (`/view/run_down`) answers "what today"; the weekly review is the
counterweight that keeps the *record itself* honest — so stalls, parked work, and
sleeping projects don't quietly become permanent.

## The sweep

Work from the queries, not from re-reading `data/` (rule 8):

1. **What moved** — `repo.board()`: actions logged or completed since the last
   review, projects closed. Name them back to the user; momentum seen is momentum
   kept.
2. **What stalled** — `run_down`'s `stalled` list. For each: does he still want the
   outcome? Then decide one concrete next action together (`add_action.py`). No
   longer wanted → `done.py` it with a note, or park it `someday` — an honest
   `someday` beats a fake next action.
3. **What's parked** — open actions whose follow-up is still in the future
   (`run_down`'s `parked` count; details on the board). Scan for follow-ups that
   were optimistic: anything that should have resurfaced, move with
   `log.py A-#### "review: moved up" --follow-up ...`.
4. **What should wake** — `someday` projects on the board. Any whose moment has
   come? (Waking one currently means a hand-edit of `status` — if this starts
   repeating, that's the signal to grow the tool for it, rule 6.)
5. **Staleness check** — the `next` list's stalest entries. Weeks untouched usually
   means the action is mis-stated (too big, actually blocked, or not really next) —
   restate it, split it, or log the blocker.

## Close it out

`python tools/validate.py`, then `python tools/beam_board.py` — the review isn't
done until the tab shows its result. Note anywhere the placeholder ordering ranked
the week's reality wrong: those observations are the raw material for open
question 2 (the prioritization capability), which is deliberately unsettled.
