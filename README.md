# Living Workspace

Software 3.0 is slowly emerging to fully unleash AI. No one is quite sure yet what it
will look like — but one cornerstone seems increasingly settled: **a well-behaved agent
between users and their systems and data, as the primary interface.**

Living workspace is a new architecture built on that cornerstone:

> A living workspace is a work environment on a shared file substrate, operated by an
> agent in conversation with its user, that grows its own capabilities as a side effect
> of the work — never deployed, never finished, always in use.

Not a rigid, pre-built application, but a fluid, agent-operated environment that evolves
alongside the project it serves. The rest of this page unpacks that sentence.

## The shape

Every application until now was built the same way:

```
repo  →  app  →  user
```

Developers write code in a repo. The repo builds into an app. The app ships, and users
operate it by hand — clicking through whatever interface the developers froze at release.

A living workspace is a different shape:

```
repo  →  living workspace  →  agent  →  user
```

The repo never builds into anything, and no one ships it. **The repo becomes an
environment that an agent works inside, on behalf of the user.** You state what you want
in conversation; the agent operates the system for you.

## What kind of work this is for

Some work needs more structure than chat and less than software. A literature review for
a client. A due-diligence file. A grant pipeline. A competitive landscape. The long tail
of serious knowledge work — too structured to live in a chat thread, too particular for
any off-the-shelf app — so it ends up in a folder of files, a spreadsheet, six browser
tabs, and your head.

That's the gap this architecture fills. You start with a small standard kit, empty data
folders, and an agent. You describe the project in conversation. The application
assembles itself around the work — and you watch it happen: the kit includes a live
dashboard that shows the workspace filling in as you talk.

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
  the fix is added permanently — no release cycle, no feature request, no waiting.

## Same substrate, three differences

Under the hood, a living workspace has everything a regular application has: entities
defined in schemas, records stored in a system of record, rules that must hold,
deterministic operations, views over the data. The substrate is the same. What's different
is what surrounds it:

1. **The repo carries its own operating instructions.** Alongside the data sit the
   schemas that say what it means, the skills that say how to work with it correctly, and
   the tools that enforce its rules — all laid out in files any agent can read, understand,
   and then navigate on the user's behalf. A file here is simultaneously something to
   read, an instruction to follow, and a program to run. There is no interface layer to
   learn, because the conversation *is* the interface.

2. **The agent is half of the application.** In a normal app, the user is the operator.
   Here the agent is: it reads the manual the repo contains, runs the tools, respects the
   rules, and hands back answers, boards, and reports. The repo alone does nothing — an
   agent reading its instructions completes the system. Every other interface — a live
   dashboard, an assembled document, an export — is an answer the agent computes from
   the substrate on demand.

3. **There is no separate building and using.** A normal app is built, then used; wanting
   a new capability means waiting for the next release. Here, capability is built *as part
   of* using the system. It runs on [one rule](canon/the-move-rule.md): state what you
   want; **if it's reachable with what exists, it just gets done — if not, the next move
   grows the missing capability** (access → understanding → presentation), permanently, in
   place. Every move pays twice: the task done, and the capability that remains. The
   workspace you have next month is more capable than the one you have today, as a side
   effect of using it.

## Where this sits

A living workspace is an application written in two languages. The parts that must be
exact — validation, id assignment, the rules that must hold — are compiled down into
deterministic code in `tools/`. The parts that need judgment — how to work the data, what
to watch for — stay as English in `skills/`. The agent is the runtime that binds the two,
and the operating manual (`CLAUDE.md`) is effectively its `main()`. This is software 3.0's
"natural language as programming language, model as runtime" taken literally — with the
boundary drawn honestly: English where judgment lives, code where exactness lives.

Its learning lives in artifacts, not weights. The workspace gets more capable the way a
skill-library agent does: every gap the agent fills is deposited as a permanent file —
a tool, a schema, a skill — that every future move lands on. Nothing is retrained;
everything is readable, diffable, and yours.

And it delivers something software has promised for decades and never managed: **malleable
software** — tools their users reshape through use. That dream always failed on the same
step: reshaping required programming skill. An agent removes that step. Say what's
missing, and the workspace grows it — which is why the deploy boundary can collapse
entirely, and building and using become the same activity in the same conversation.

## This repo is three things

| Part | What it is | Start here |
|---|---|---|
| **[`canon/`](canon/)** | How it all works: the definition, the move rule, the anatomy, the operating manual. General — nothing project-specific. | [canon/README.md](canon/README.md) |
| **[`example/`](example/)** | A complete worked example: a client-commissioned literature review, from empty folders to the delivered report. Fully runnable. | [example/JOURNEY.md](example/JOURNEY.md) |
| **[`template/`](template/)** | A fresh start: the two documents, the standard kit (data-access layer, dashboard server, validator), and empty data folders. Copy it, open Claude Code, begin. | [template/](template/) |

## The worked example, at a glance

A consulting firm's client commissions a structured evidence review (*remote patient
monitoring for heart failure — does it reduce readmissions?*). The project bootstraps from
the client's own file — an email thread, a brief, five flagged papers — and runs to a
delivered report. **The whole timeline is one document,
[`example/JOURNEY.md`](example/JOURNEY.md):** ten milestones, each linking to the live
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

The data folders start empty on purpose; the kit keeps the workspace visible from minute
one — start `python tools/server.py` and watch it assemble itself on screen.

## What this is not

- **Not a framework.** Nothing to install, no API to learn — a folder convention plus an
  operating manual the agent reads.
- **Not a chatbot bolted onto a backend.** The agent doesn't sit in front of an app that
  someone else built and froze; the repo it operates *contains* the app — data,
  understanding, capability, and presentation — and the agent grows all four as it works.
- **Not model magic.** Everything exact — validation, id assignment, the rules — is
  deterministic code the model never freehands. The model handles conversation, judgment,
  and growth.
- **Not finished.** By design. "Finished" isn't a state this kind of application has —
  there is never a launch, and the attention split between building and using starts near
  all-building, drifts toward all-using, and never arrives.
