---
name: time-tracking
description: Rules and workflow for logging billable time. Use whenever the user reports work done, asks to log hours, or mentions time spent on a project.
---

# Time tracking

## Rules

1. Time is logged **against a project**, never against a client directly. If the user names a
   client, resolve to the project — ask which one if the client has more than one active.
2. **Quarter-hour increments** (0.25). Round to the nearest quarter; confirm with the user if
   the rounding changes what they said by more than a few minutes.
3. The project must be **active**. Logging time to a paused or completed project is refused by
   the tool — surface that to the user rather than working around it.
4. A time entry, once **billed**, is frozen: never edit its hours, date, or project. If it was
   wrong, the correction happens on the next invoice, as a new entry with a note.
5. Descriptions say what the time bought, in one line a client could read on an invoice.

## Workflow

Log time with the tool — never by hand-editing `data/time/`:

```
python tools/add_time.py --project PR-001 --date 2026-07-03 --hours 1.5 \
    --description "Stakeholder interviews: operations team"
```

The tool assigns the next id, refuses inactive projects, and validates the record before
keeping it. After logging, if the user asks where things stand, use
`python tools/report.py unbilled` or `python tools/report.py projects`.
