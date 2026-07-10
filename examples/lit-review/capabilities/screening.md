---
name: screening
description: Rules and workflow for screening sources in or out of the review. Use whenever a source needs an include/exclude decision, or the user asks what's unscreened.
runs: either
returns: |
  For each source screened: {id, decision: included|excluded, criterion, reason}.
  The decision is already written via tools/screen.py — the return value is the
  report, not the deposit.
---

# Screening

*Ambidextrous. One contested paper is a conversation — the reasoning is what the user
wants. A batch of twenty fresh sources is a fan-out: one delegate per source, each
reading the abstract in its own context and writing its decision through `screen.py`,
which refuses a decision with no criterion whether or not the delegate read this page.
Only the decisions come back. What a delegate may never do is change the criteria — those
come from the brief and the user.*

## Rules

1. Decisions are made **against the brief's criteria** (`seed/brief.md`), never improvised
   per paper. Every decision records **which criterion** it was decided on.
2. **Exclusions record a reason** a reviewer could defend to the client's medical director.
3. A decided source is **frozen**. The tool refuses re-screening; revisions happen as a new
   versioned pass, not silent edits.
4. Unscreened sources block the report — `assemble_report.py` refuses to run while any
   source is undecided.

## Workflow

```
python tools/screen.py --source S-006 --decision included \
    --criterion "HF population; RPM intervention; readmission outcome; pragmatic RCT" \
    --date 2026-07-04

python tools/screen.py --source S-009 --decision excluded \
    --criterion "exclusion: no outcome of interest" \
    --reason "Device accuracy only; no outcome of interest" --date 2026-07-04
```

After a screening pass: `python tools/validate.py`. The board needs no regeneration — it
is live (`capabilities/dashboard.md`); decisions appear on it as they land.
