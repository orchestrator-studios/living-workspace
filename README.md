# Living Workspace

Some work needs more structure than chat and less than software.

A literature review for a client. A due-diligence file. A grant pipeline. A competitive
landscape. The long tail of serious knowledge work — too structured to live in a chat thread,
too particular for any off-the-shelf app. So it ends up where it always ends up: a folder of
files, a spreadsheet, six browser tabs, and your head.

This repo is a different way to do that work. **You start with five empty folders and an
agent. You describe the project in conversation. The system assembles itself around the
work** — and keeps assembling for as long as you use it.

No install. No framework. No deploy step, ever.

## What you get

- **You talk instead of click.** "Pull in the papers the client already flagged." "What's
  still unscreened?" "Assemble the report." The conversation is the interface.
- **Your data lives in plain files you own.** Readable, diffable, portable. No vendor, no
  export button, no lock-in.
- **Rules are enforced, not remembered.** The rules you state get captured in files and
  enforced by small deterministic tools — so they hold even when nobody (human or model) is
  paying attention.
- **Views appear when you need to see.** A screening board, an evidence table, a report —
  generated from the data the day you first need them, regenerated whenever it changes.
- **Every obstacle makes the system stronger.** Hit something the workspace can't do, and
  the fix is added permanently. The workspace you have next month is more capable than the
  one you have today, as a side effect of using it.

## What a living workspace is

> A work environment on a shared file substrate, operated by an agent in conversation with
> its user, that grows its own capabilities as a side effect of the work — never deployed,
> never finished, always in use.

Three properties make it that, and each folder below serves one of them: the files carry the
data *and* its meaning *and* the operations on it (a shared, meaning-bearing substrate); an
agent is the operator, and every screen is a projection it can generate (agent operation);
and there is no boundary between using the system and extending it (capability accretion —
the "living" part).

## How it works — one rule

At any moment the workspace has what it has: the access it has, the understanding it has,
the tools and views it has. You say what you want.

**If it's reachable with what exists — it just gets done.**

**If it isn't, the next move is acquiring what's missing**, checked in order:

1. **Access** — can we reach the data or operation at all? If not, add the tool or connection.
2. **Understanding** — is the meaning encoded: the shapes, the rules that must hold? If not,
   write the schema or the skill.
3. **Presentation** — does the output form exist: the view, the report design? If not,
   generate it.

Then the original want goes through. Every gap-fill is deposited as a file the agent reads
from then on — so **every move pays twice**: the task done, and the capability that remains.
That's the whole method. Do it, or grow it.

## What's in the box

```
OVERVIEW.md   what this system is — filled in first, from your source material and an interview
CLAUDE.md     the operating manual the agent follows
data/         the persistent objects — the system of record
schemas/      their structure and validity
tools/        deterministic operations: create, validate, query, transform
skills/       workflow rules and know-how — how to use the tools correctly
views/        generated ways of seeing the data
```

## The worked example — a commissioned literature review

The repo doubles as a worked example: a consulting firm's client commissions a structured
literature review (*remote patient monitoring for heart failure — does it reduce
readmissions?*). The project bootstraps from the client's own file — an email thread, a
brief, five flagged papers — and runs to a delivered report.

The git history is the walkthrough: **one commit per milestone**, tagged, so you can check
out any moment and stand inside it. Each milestone is one firing of the rule above:

| Tag | Milestone | The want | Do it, or grow it? |
|---|---|---|---|
| `m0` | The template | — | the starting point: empty folders |
| `m1` | The Intake | "set up the project from the client's file" | grow **understanding** → OVERVIEW.md filled |
| `m2` | The Agreement | "manage sources properly" | grow **understanding** → four schemas |
| `m3` | The Move-In | "pull in what the client gave us" | **do it** — seed data, nothing new needed |
| `m4` | The Mirror | "how do I know what we've got?" | grow **presentation** → the screening board |
| `m5` | The Routine | "run sweeps without duplicate papers" | grow **access** → the `add_source` tool |
| `m6` | The Guarantee | "nothing may ever cite an excluded paper" | grow **understanding** (hard form) → skill + enforcer |
| `m7` | The Handoff | "assemble the client's report" | **do it** — one sentence; every capability already exists |

Note the shape: the biggest deliverable is the smallest move. By `m7`, every prerequisite has
already been deposited by an earlier milestone — the report assembles on demand, every claim
tracing to an included source, because `m6` made anything else impossible.

*(The client, correspondence, and papers in this example are fictional.)*

## Start your own

1. Copy the skeleton (clone this repo and check out `m0`, or just make the folders and copy
   in `CLAUDE.md` + `OVERVIEW.md`).
2. Open Claude Code in the folder.
3. Point it at whatever your project already has — a brief, an email thread, a spreadsheet —
   and start talking. The interview fills the overview; everything else follows the rule.

The folders start empty on purpose.

## What this is not

- **Not a framework.** Nothing to install, no API to learn — a folder convention plus an
  operating manual the agent reads.
- **Not model magic.** Everything exact — validation, id assignment, the rules — is
  deterministic code the model never freehands. The model handles conversation, judgment,
  and growth.
- **Not finished.** By design. "Finished" isn't a state capability systems have.
