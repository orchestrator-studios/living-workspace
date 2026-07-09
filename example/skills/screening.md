---
name: screening
description: Rules and workflow for screening sources in or out of the review. Use whenever a source needs an include/exclude decision, or the user asks what's unscreened.
---

# Screening

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
is live (`skills/live-board.md`); decisions appear on it as they land.
