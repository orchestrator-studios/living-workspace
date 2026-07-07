# JOURNEY — how this workspace was built, step by step

This file records how this workspace went from empty folders to a delivered report, in
eight milestones (m0–m7). Each milestone states exactly what the user typed, what Claude
did, and what appeared — with links to the actual files in this repo.

**How to read the blocks:**

- **You type** — a message the user sends to Claude, in the Claude Code chat. Verbatim.
- **Claude does** — the concrete actions Claude takes: files it reads, questions it asks,
  files it writes, commands it runs.
- **Terminal** — real command output. Every output quoted in this file was produced by
  actually running the tools (early-milestone outputs were reproduced against that
  milestone's data state).
- **Files changed** — what is different on disk after the milestone, with links.

Each milestone header carries a tag: **DO IT** means the request was completed with
capabilities that already existed; **GROW** means a missing capability had to be added
first (access, understanding, or presentation — see
[the move rule](../canon/the-move-rule.md)).

*(Client, correspondence, and papers are fictional throughout.)*

---

<a id="m0"></a>
## m0 · Setup — before any request

What the user did, before talking to Claude at all:

1. Copied the [template](../template/) — `CLAUDE.md`, the blank `OVERVIEW.md`, and five
   empty folders — into a new project folder.
2. Created a `seed/` folder and put the client's material in it: the two emails saved as
   [`seed/client-email-thread.md`](seed/client-email-thread.md), the attached brief as
   [`seed/brief.md`](seed/brief.md), and the medical director's list of five papers as
   [`seed/flagged-papers.csv`](seed/flagged-papers.csv). (`seed/` is not part of the
   template — it's just a folder for source material.)
3. Opened a terminal in the project folder and started Claude Code.

**State of the workspace:** `OVERVIEW.md` is the unfilled skeleton. `data/`, `schemas/`,
`tools/`, `skills/`, `views/` are empty. `seed/` holds the three client files.

---

<a id="m1"></a>
## m1 · The Intake — GROW: understanding

**You type:**

> Read everything in seed/ and set up the project. Fill in OVERVIEW.md.

**Claude does:**

1. Reads the three files in `seed/`.
2. Drafts the overview from them: the review question, the secondary outcomes, the
   inclusion/exclusion criteria, the deadline — all of which are stated in the brief.
3. Asks the user three questions the client file does not answer:
   - *"Do systematic reviews and meta-analyses count as primary research for inclusion?"*
     — User: yes.
   - *"Should adherence and engagement studies be included even if they report no
     readmission data?"* — User: yes; adherence is a secondary outcome.
   - *"The brief says decisions must be defensible to Dr. Reyes. Do you want every
     screening decision to record which criterion it was made on?"* — User: yes, always.
4. Writes the answers into [`OVERVIEW.md`](OVERVIEW.md).

**Files changed:** `OVERVIEW.md` — from skeleton to filled. Nothing else.

The overview now contains: the purpose, the four kinds of record this work will need
(source, finding, theme, search), the rules (including "a finding may only cite an
included source"), where the data lives today (`seed/`), and the requests the user
expects to make.

---

<a id="m2"></a>
## m2 · The Agreement — GROW: understanding

**You type:**

> Propose the data structures we need to run this review.

**Claude does:**

1. Replies in chat with a proposal derived from the overview — four record types and the
   fields of each:
   - **source** — citation fields, how it was found, and a screening block (status,
     criterion, reason, date);
   - **finding** — one claim from one source: outcome, direction, evidence, theme;
   - **theme** — a named synthesis bucket;
   - **search** — a logged sweep: query, database, date, hits, which sources it added.
2. Waits for approval.

**You type:**

> Yes. Go ahead.

**Claude does:** writes the four schema files:
[`schemas/source.schema.json`](schemas/source.schema.json) ·
[`schemas/finding.schema.json`](schemas/finding.schema.json) ·
[`schemas/theme.schema.json`](schemas/theme.schema.json) ·
[`schemas/search.schema.json`](schemas/search.schema.json)

The rules from m1 are now field definitions. For example, in `source.schema.json` the
screening block has `status`, `criterion`, `reason`, `date` — so a decision *without* its
criterion is invalid data, not just bad practice.

**Files changed:** `schemas/` — four files. `data/`, `tools/`, `skills/`, `views/` are
still empty.

---

<a id="m3"></a>
## m3 · The Move-In — DO IT

Nothing new is built in this milestone. The request is completed with what already exists:
the papers are in `seed/`, and the schemas define what a source record looks like.

**You type:**

> Add the five flagged papers from seed/flagged-papers.csv as sources.

**Claude does:** reads the CSV and writes five records —
[`data/sources/S-001.json`](data/sources/S-001.json) through `S-005.json` — each with
`"found_via": "seeded"` and `"screening": {"status": "unscreened"}`.

**You type:**

> Now screen them against the brief's criteria. Walk me through each one.

**Claude does:** goes paper by paper in chat, proposing a decision and the criterion for
each; the user confirms each one. The result:

| Source | Decision | On what basis |
|---|---|---|
| S-001 (telemonitoring cohort, 30-day readmissions) | **included** | HF population; RPM intervention; readmission outcome; primary research |
| S-002 (telephone support + device data RCT) | **included** | HF population; RPM intervention; readmission + mortality outcomes; RCT |
| S-003 (adherence in older adults) | **included** | HF population; RPM intervention; adherence outcome; cohort |
| S-004 (wearables in **atrial fibrillation**) | **excluded** | different patient population |
| S-005 (an **editorial**) | **excluded** | not primary research |

Claude records each decision in the source's file (there is no screening tool yet — Claude
edits the records directly, conforming to the schema), then checks its own work is valid.
At this point there is no validator either, so Claude re-reads each file against the
schema in chat.

**Files changed:** `data/sources/` — five files created, then updated with decisions.

---

<a id="m4"></a>
## m4 · The Mirror — GROW: presentation

**You type:**

> How do I know the data is right? I don't want to ask you record by record — give me
> something I can open in my browser that shows every source and where it stands.

This is not reachable with what exists — there is no way of *seeing* the data yet. So a
view gets built.

**Claude does:**

1. Writes [`views/build_screening_board.py`](views/build_screening_board.py) — a script
   that reads `data/` and generates a static HTML page: three columns (unscreened /
   included / excluded), one card per source showing its title, how it was found, and the
   basis for its decision.
2. Runs it.

**Terminal:**

```
$ python views/build_screening_board.py
Wrote views/screening_board.html — 0 unscreened · 3 included · 2 excluded.
```

**What you see:** you open `views/screening_board.html` in a browser. Five cards in three
columns. The two excluded cards show their reasons on the card. The user checks the board
against the CSV and the brief — this is the moment the seeded data gets verified by eye.

The page is regenerated by re-running the script after any data change. It is never edited
by hand. (The copy checked into this repo shows the *current* data — 12 sources — because
it has been regenerated since; the output above is what it printed at this milestone,
reproduced against this milestone's five-source state.)

**Files changed:** `views/` — the script and the generated HTML.

---

<a id="m5"></a>
## m5 · The Routine — GROW: access

**You type:**

> Time to search. Run sweeps for: heart failure, remote monitoring or telemonitoring or
> telephone support, with readmission, mortality, adherence, or cost outcomes. Log every
> search. And one thing — I keep seeing the same papers come up in different searches.
> It must be impossible to add the same paper twice.

Adding sources is about to become a repeated operation with a rule attached ("same DOI
never enters twice"). That path doesn't exist yet, so one tool gets built — and only that.

**Claude does:**

1. Writes [`tools/add_source.py`](tools/add_source.py). The tool assigns the next `S-` id,
   records how the source was found, sets it unscreened — and **refuses any DOI that is
   already in the review**.
2. Runs the first sweep (in this fictional example, against a stand-in database), judges
   the 41 hits against the brief, and adds the relevant ones **through the tool** — one
   command per paper. Five are new; three are papers already seeded by the client.

**Terminal (one success and one refusal, verbatim):**

```
$ python tools/add_source.py --title "Home telemonitoring and 30-day readmission after acute decompensated heart failure: a pragmatic randomized trial" --authors "Ijeoma N; Kaplan S; Verhoeven D" --year 2023 --venue "Annals of Digital Medicine" --doi 10.9999/fict.2023.0790 --found-via search:Q-01
Added S-006: Home telemonitoring and 30-day readmission after acute decom… (unscreened)

$ python tools/add_source.py --doi 10.9999/fict.2024.0117 ...
REFUSED: DOI already in the review (S-003, added from the client's flagged list).
```

3. Logs the sweep as [`data/searches/Q-01.json`](data/searches/Q-01.json): the query, the
   date, 41 hits, the five sources added, and a note that three duplicates were refused.
4. Repeats for a second sweep ([`Q-02.json`](data/searches/Q-02.json): 17 hits, 2 added,
   1 duplicate refused).
5. Screens the seven new sources the same way as m3 — decision plus criterion, confirmed
   in chat, recorded in the files — and re-runs the board script.

**Files changed:** `tools/` — one file (`add_source.py`). `data/sources/` — seven new
records (S-006 … S-012), then their screening decisions. `data/searches/` — two records.
`views/screening_board.html` — regenerated.

**State of the review:** 12 sources — 8 included, 4 excluded, 0 unscreened.

---

<a id="m6"></a>
## m6 · The Guarantee — GROW: understanding (enforced)

**You type:**

> Before we extract anything: nothing in the client's report may cite a paper we excluded.
> And I don't want to rely on you or me remembering what got excluded — make it impossible.

"Make it impossible" cannot be satisfied by conversation. Until now the rules have lived
in `OVERVIEW.md` (prose) and `schemas/` (shape). This milestone adds the third form:
enforcement in code, plus written procedures for the agent to follow.

**Claude does:**

1. Writes two skills — the procedures in plain language:
   [`skills/screening.md`](skills/screening.md) (decisions record their criterion;
   exclusions record a reason; a decided source is frozen) and
   [`skills/findings-and-citations.md`](skills/findings-and-citations.md) (a finding may
   only cite an included source; the report is assembled by tool, never written by hand).
2. Writes four tools — the same rules in code:
   - [`tools/screen.py`](tools/screen.py) — records a decision; refuses to re-screen a
     decided source.
   - [`tools/add_finding.py`](tools/add_finding.py) — creates a finding; **refuses any
     source that is not included**.
   - [`tools/validate.py`](tools/validate.py) — checks every record against its schema,
     plus the cross-record rules: no duplicate DOIs, decisions carry criteria, and no
     finding cites anything but an included source.
   - [`tools/assemble_report.py`](tools/assemble_report.py) — generates the report from
     the data (used in m7); refuses to run if any source is still unscreened.
3. Extracts the findings. The user and Claude go through the eight included papers in
   chat; each agreed claim is added **through the tool** — nine findings
   ([`data/findings/`](data/findings/)) organized under four themes
   ([`data/themes/`](data/themes/)) — 30-day readmissions, mortality and long-term
   outcomes, adherence and engagement, cost.
4. Demonstrates that the guarantee holds, by trying to break it:

**Terminal (all three verbatim):**

```
$ python tools/add_finding.py --source S-004 ...
REFUSED: source S-004 is excluded (Atrial fibrillation cohort, not heart failure).
Findings may only cite included sources.

$ python tools/screen.py --source S-004 --decision included ...
REFUSED: S-004 is already excluded — screening decisions are frozen.

$ python tools/validate.py
OK — 27 records valid; citation closure holds (no finding cites anything but an included source).
```

**Files changed:** `skills/` — two files. `tools/` — four files. `data/findings/` — nine
records. `data/themes/` — four records.

---

<a id="m7"></a>
## m7 · The Handoff — DO IT

Nothing new is built in this milestone. Every capability the request needs was deposited
earlier: the sources are in and screened (m3, m5), the findings exist and can only cite
included sources (m6), and the assembler was built as part of the integrity tooling (m6).

**You type:**

> Assemble the client's report.

**Claude does:** runs the assembler.

**Terminal:**

```
$ python tools/assemble_report.py --date 2026-07-06
Wrote report.md — 4 themes, 9 findings, 8 included sources; every claim cites an included source.
```

**What you see:** [`report.md`](report.md) — the question, the method (both searches
logged with queries and counts; 12 screened → 8 included, 4 excluded), the findings
grouped by theme with citations, the included-sources list, and the appendix of excluded
sources with reasons — the exact ground rules the client set in
[the original email](seed/client-email-thread.md). The user reads it and sends it.

The report is generated, not written: re-running the assembler after any data change
produces a report that says whatever the data says then. If a source were still
unscreened, the tool would refuse to produce a report at all.

**Files changed:** `report.md`.

---

## Notes

- **What got built, and when:** understanding first (m1 overview, m2 schemas), data second
  (m3), a view before any tool (m4), the first tool when an operation became repetitive
  and rule-bound (m5), enforcement when a rule had to hold without anyone remembering it
  (m6). Each thing was added at the moment its absence blocked a request — not before.
- **Two milestones added nothing** (m3, m7). They were completable entirely with what
  earlier milestones had deposited. m7 — the deliverable itself — was a one-line request
  because everything it needed already existed.
- **Every rule ends up in two or three forms:** stated in `OVERVIEW.md`, encoded in
  `schemas/` or `skills/`, and — where it must hold unconditionally — enforced by a tool.
  The three `REFUSED` outputs above are the enforced form doing its job.

*To start your own workspace: copy [the template](../template/) to a new folder, open
Claude Code there, and point it at whatever source material your project already has.*
