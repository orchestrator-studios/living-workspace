# Living Workspace

Some work needs more structure than chat and less than software.

A literature review for a client. A due-diligence file. A grant pipeline. A competitive
landscape. The long tail of serious knowledge work — too structured to live in a chat
thread, too particular for any off-the-shelf app. So it ends up where it always ends up:
a folder of files, a spreadsheet, six browser tabs, and your head.

A living workspace is a different way to do that work. **You start with five empty folders
and an agent. You describe the project in conversation. The system assembles itself around
the work** — and keeps assembling for as long as you use it.

> A work environment on a shared file substrate, operated by an agent in conversation with
> its user, that grows its own capabilities as a side effect of the work — never deployed,
> never finished, always in use.

It runs on one rule: state what you want; **if it's reachable with what exists, it just
gets done — if not, the next move grows the missing capability** (access → understanding →
presentation), permanently, in place. Every move pays twice: the task done, and the
capability that remains.

## What you get

- **You talk instead of click.** "Pull in the papers the client already flagged." "What's
  still unscreened?" "Assemble the report." The conversation is the interface.
- **Your data lives in plain files you own.** Readable, diffable, portable. No vendor, no
  export button, no lock-in.
- **Rules are enforced, not remembered.** The rules you state get captured in files and
  enforced by small deterministic tools — so they hold even when nobody (human or model)
  is paying attention.
- **Views appear when you need to see.** A screening board, an evidence table, a report —
  generated from the data the day you first need them, regenerated whenever it changes —
  or served live, so they can't go stale.
- **Every obstacle makes the system stronger.** Hit something the workspace can't do, and
  the fix is added permanently. The workspace you have next month is more capable than the
  one you have today, as a side effect of using it.

## This repo is three things

| Part | What it is | Start here |
|---|---|---|
| **[`canon/`](canon/)** | How it all works: the definition, the move rule, the anatomy, the operating manual. General — nothing project-specific. | [canon/README.md](canon/README.md) |
| **[`example/`](example/)** | A complete worked example: a client-commissioned literature review, from empty folders to the delivered report. Fully runnable. | [example/JOURNEY.md](example/JOURNEY.md) |
| **[`template/`](template/)** | A fresh start: the two documents and five empty folders. Copy it, open Claude Code, begin. | [template/](template/) |

## The worked example, at a glance

A consulting firm's client commissions a structured evidence review (*remote patient
monitoring for heart failure — does it reduce readmissions?*). The project bootstraps from
the client's own file — an email thread, a brief, five flagged papers — and runs to a
delivered report. **The whole timeline is one document,
[`example/JOURNEY.md`](example/JOURNEY.md):** eleven milestones, each linking to the live
files it produced, with the real tool outputs — including the refusals:

```
REFUSED: DOI already in the review (S-003, added from the client's flagged list).
REFUSED: source S-004 is excluded (Atrial fibrillation cohort, not heart failure).
OK — 27 records valid; citation closure holds.
Wrote report.md — 4 themes, 9 findings, 8 included sources; every claim cites an included source.
```

Try it (Python 3.10+, no dependencies):

```bash
cd example
python tools/validate.py
python tools/server.py                    # → http://127.0.0.1:8765 — the live screening board
python tools/assemble_report.py --date 2026-07-06
```

*(The client, correspondence, and papers in the example are fictional.)*

## Start your own

1. Copy [`template/`](template/) to wherever your project will live.
2. Open Claude Code in that folder.
3. Point it at whatever the project already has — a brief, an email thread, a spreadsheet —
   and start talking. The intake fills the overview; everything else follows
   [the rule](canon/the-move-rule.md).

The folders start empty on purpose.

## What this is not

- **Not a framework.** Nothing to install, no API to learn — a folder convention plus an
  operating manual the agent reads.
- **Not model magic.** Everything exact — validation, id assignment, the rules — is
  deterministic code the model never freehands. The model handles conversation, judgment,
  and growth.
- **Not finished.** By design. "Finished" isn't a state capability systems have.
