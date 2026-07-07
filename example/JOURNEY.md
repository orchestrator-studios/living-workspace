# JOURNEY — how this workspace was built, step by step

This file is the trace of one [journey](../canon/the-journey.md) — a client-commissioned
literature review, from empty folders to the delivered report — navigated by
[the move rule](../canon/the-move-rule.md). It runs the canonical shape: the final state
described first (step 2), the route chunked coarse, and the insides taken one hop at a
time. Each step records what was wanted, what was missing, what got built to close the
gap, and what was deposited on disk. The gaps are called out inline, in prose — when a
step needed a schema, a tool, or a skill that didn't exist yet, that's where it got made,
and not before.

**How to read each step:** the **Ask** is what the user typed, verbatim. The prose after
it is what actually happened — including any capability that had to be created first.
**New on disk** is what the workspace permanently gained.

*(Draft note: terminal output in this version is illustrative. It will be replaced with
real captured output once the workspace's artifacts are regenerated to match this journey.)*

*(Client, correspondence, and papers are fictional throughout.)*

---

## Before the first request

What the user did before talking to Claude at all: copied [the template](../template/) —
`CLAUDE.md`, the blank `OVERVIEW.md`, and five empty folders — into a new project folder;
created a `seed/` folder holding the client's material — the
[email thread](seed/client-email-thread.md), the [brief](seed/brief.md), and
[`flagged-papers.csv`](seed/flagged-papers.csv), the five papers the client's medical
director considers the starting point; then opened a terminal there and started Claude Code.

---

## 1 · Intake

**Ask:** "Read everything in seed/ and set up the project. Fill in OVERVIEW.md."

Claude reads the three seed files and drafts the overview: the review question, the
secondary outcomes, the inclusion/exclusion criteria, the deadline. Three things the
client file doesn't answer, it asks — do systematic reviews count as primary research
(yes); do adherence studies count without readmission data (yes); should every decision
record the criterion it was made on (yes, always) — and writes the answers into
[`OVERVIEW.md`](OVERVIEW.md).

**New on disk:** `OVERVIEW.md` — from skeleton to filled.

---

## 2 · The deliverable, described before any work

**Ask:** "Before we search for anything: write one document that describes the finished
deliverable. What exactly does the client get, and what must be true of it?"

Claude drafts the spec from the brief and the email: the report's contents (question,
method, findings by theme, included-sources list, exclusions appendix with reasons) and
its acceptance criteria — every claim cites a paper that passed screening; every search
is logged; and the search strategy itself is **validated against the client's five flagged
papers**: a strategy that can't find the papers the medical director already knows about
can't be trusted to find the ones he doesn't.

With the destination described, the spec sketches the route — three chunks, coarse on
purpose, each naming where it ends, not how it goes:

1. **A validated pool** — a set of papers that passed the brief's criteria, produced by a
   search strategy proven against the client's five flagged papers.
2. **The learnings** — every claim the pool supports, extracted and compiled under themes.
3. **The report** — generated from the data, meeting the acceptance criteria above.

The insides of the chunks are not planned here. They get discovered one hop at a time —
steps 3 through 8 below are chunk one unfolding — per
[the journey doctrine](../canon/the-journey.md): commit fully to the destination,
coarsely to the route, and one move at a time to everything else.

Then a question with no obvious answer: **where does this document live?** It isn't data,
a schema, a tool, a skill, or a view — none of the five folders fit a document *about the
work itself*. For now it sits at the workspace root, next to `OVERVIEW.md`, as
`DELIVERABLE.md`. (Open question, flagged and parked: the right home for spec-like
documents — the report will pose the same question at the end.)

**New on disk:** `DELIVERABLE.md` — the spec and the plan.

---

## 3 · Write the queries

**Ask:** "Draft the search queries. I want to see them before anything runs."

Claude drafts four queries from the brief — telemonitoring × readmission, home devices ×
mortality, wearables for HF management, RPM × cost — each with the database it targets
and a one-line rationale tying it to a brief criterion.

Then the first gap: the queries need to be *kept*, not just shown in chat — they'll be
run, revised, and cited by the report's method section. There is nowhere to put them. So
Claude proposes a query record — id, query text, database, rationale, status — the user
approves it, and it becomes the workspace's first schema. The four queries are written as
records.

**New on disk:** `schemas/query.schema.json` · `data/queries/Q-01.json` … `Q-04.json`.

---

## 4 · Run the queries

**Ask:** "Run them. Keep everything that comes back — I want the raw results, not your
summary of them."

Two gaps at once. There's no path to the database — that's a tool. And raw results need a
home of their own, separate from the queries that produced them — that's a second schema.
Claude writes [`tools/run_query.py`](tools/run_query.py) (in this fictional example,
against a stand-in database) and `schemas/result.schema.json`: one result record per query
run — query id, date, hit count, and the hits themselves with title, authors, year, venue,
DOI, abstract.

```
$ python tools/run_query.py --query Q-01
Q-01 ran against fictdb — 41 hits → data/results/R-01.json

$ python tools/run_query.py --query Q-02
Q-02 ran against fictdb — 17 hits → data/results/R-02.json
```

Four runs, 96 raw hits, untouched and unjudged. Overlap between queries is expected and
preserved — deduplication is a judgment about *papers*, and papers don't exist as records
yet.

**New on disk:** `tools/run_query.py` · `schemas/result.schema.json` ·
`data/results/R-01.json` … `R-04.json`.

---

## 5 · Build the semantic filters

**Ask:** "Keyword hits aren't inclusion decisions. For each query, write the filter that
decides whether a hit actually belongs in this review — the brief's criteria, applied
paper by paper."

A query retrieves; a filter judges. Each filter states, for the hits of one query, the
criteria a paper must pass — population is heart failure, intervention is remote
monitoring, at least one outcome of interest, primary research or systematic evidence —
each criterion with its pass rule in plain language, lifted from the brief, not improvised
per paper. The filters share the brief's core but each carries its query's specifics (the
cost query's filter, for instance, spells out what counts as a cost outcome).

Filters are records too — they'll be applied, cited, and possibly revised — so they get a
schema and a folder.

**New on disk:** `schemas/filter.schema.json` · `data/filters/F-01.json` … `F-04.json` —
one per query.

---

## 6 · Run the results through the filters

**Ask:** "Now run every hit through its filter. I want a verdict per paper per criterion —
and show me the pool somewhere I can look at it."

This is where hits become *papers*. Claude writes `schemas/paper.schema.json` — one record
per unique paper: citation, which queries retrieved it (the 96 hits collapse to 71 unique
papers), and a verdict block: per-criterion pass/fail with a reason, and the overall call.
Applying a filter is a judgment, but *recording* it is an operation with rules — same DOI
never judged twice, a verdict once recorded is frozen — so the recording goes through a
tool, [`tools/apply_filter.py`](tools/apply_filter.py), which enforces both.

```
$ python tools/apply_filter.py --paper P-054 --filter F-03 --verdict fail \
    --criterion population --reason "Atrial fibrillation cohort, not heart failure"
P-054: FAIL on population — recorded, frozen.

$ python tools/apply_filter.py --paper P-054 --filter F-03 --verdict pass ...
REFUSED: P-054 already has a verdict. Verdicts are frozen.
```

And the seeing: [`views/build_pool_board.py`](views/build_pool_board.py) generates a
static HTML page — every paper as a card, pass/fail columns, the failing criterion on the
card. 71 papers judged; **9 pass**. The board is regenerated after any data change, never
edited by hand.

**New on disk:** `schemas/paper.schema.json` · `data/papers/P-001.json` … `P-071.json` ·
`tools/apply_filter.py` · `views/build_pool_board.py` · `views/pool_board.html`.

---

## 7 · Check the flagged five

**Ask:** "Moment of truth. Dr. Reyes's five papers — are they in that pool? Check it
properly, don't eyeball it."

"Properly" means deterministically: Claude writes [`tools/check_flagged.py`](tools/check_flagged.py),
which reads the client's CSV and reports, for each flagged paper, whether any query
retrieved it and what verdict it got.

```
$ python tools/check_flagged.py
Hartwell 2023 (telemonitoring cohort)       retrieved by Q-01 · verdict: PASS
Mbeki 2022 (structured telephone support)   NOT RETRIEVED by any query
Solano 2024 (adherence, older adults)       retrieved by Q-01, Q-04 · verdict: PASS
Chen 2023 (wearables in AF)                 retrieved by Q-03 · verdict: FAIL (population)
Vance 2021 (editorial)                      retrieved by Q-01 · verdict: FAIL (study type)

CAPTURE: 4/5 retrieved — 1 MISSED. Strategy not validated.
```

Two different signals here. Chen and Vance failing is the *filters working* — one is the
wrong population, the other isn't primary research; the brief itself excludes both. But
Mbeki never being retrieved at all is a **query gap**: every query says telemonitoring,
remote monitoring, wearables — none says *structured telephone support*, which the brief
explicitly includes as an intervention.

**New on disk:** `tools/check_flagged.py`.

---

## 8 · The decision

**Ask:** "So the strategy has a hole. Fix the queries, not the check — and rerun."

The gap is repaired at its source. Claude writes `Q-05` (structured telephone support ×
HF outcomes) with its filter `F-05`, runs it, and filters its hits — 9 more hits, 2 new
papers, one of which is Mbeki 2022: retrieved, judged, **pass**. The pool is now 11.

```
$ python tools/check_flagged.py
...
CAPTURE: 5/5 retrieved — 3 in the pool, 2 correctly excluded by the brief's own criteria.
Strategy validated.
```

The decision: **proceed to extraction.** The validation is recorded in `DELIVERABLE.md` —
which queries, which filters, what the check found on each pass, and the basis for the two
exclusions the client will see in the appendix. Dr. Reyes's question — "why did anything
get ruled in or out?" — now has a mechanical answer for all five of his papers.

**New on disk:** `data/queries/Q-05.json` · `data/filters/F-05.json` ·
`data/results/R-05.json` · two paper records · `DELIVERABLE.md` — validation section.

---

## 9 · Extract the learnings

**Ask:** "Extract the learnings from the pool. And the client's rule holds absolutely:
nothing may ever cite a paper that isn't in the pool. Make that impossible, not just
agreed."

Extraction is judgment — Claude and the user go through the 11 pool papers in chat, one
claim at a time. But the rule attached to it is enforcement, so before any learning is
recorded, the capability is built in all three forms: a schema
(`schemas/learning.schema.json` — one claim, one paper, outcome, direction, evidence,
theme), a skill ([`skills/learnings.md`](skills/learnings.md) — how a claim is extracted
and worded, one claim per record, recorded only through the tool), and two tools —
[`tools/add_learning.py`](tools/add_learning.py), which **refuses any paper not in the
pool**, and [`tools/validate.py`](tools/validate.py), which checks every record in the
workspace against its schema plus the cross-record rules: no duplicate DOIs, every verdict
carries its criterion and reason, and no learning cites anything outside the pool.

```
$ python tools/add_learning.py --paper P-054 ...
REFUSED: P-054 failed its filter (population: atrial fibrillation, not heart failure).
Learnings may only cite papers in the pool.

$ python tools/validate.py
OK — 94 records valid; citation closure holds (no learning cites outside the pool).
```

Twelve learnings, compiled under four themes: 30-day readmissions, mortality and
long-term outcomes, adherence and engagement, cost.

**New on disk:** `schemas/learning.schema.json` · `skills/learnings.md` ·
`tools/add_learning.py` · `tools/validate.py` · `data/learnings/L-001.json` … `L-012.json`.

---

## 10 · Generate the report

**Ask:** "Generate the client's report."

One sentence, because everything it needs already exists. Claude writes
[`tools/assemble_report.py`](tools/assemble_report.py) — the report is *generated from
the data*, never written by hand: the question; the method (five queries with their
filters, logged runs and counts, the flagged-five validation including the strategy
revision — the client sees that the check failed once and why); the learnings by theme,
every claim cited to a pool paper; the pool as the included-sources list; and the
appendix of excluded papers with the criterion each failed. The tool refuses to run if
`validate.py` doesn't pass.

```
$ python tools/assemble_report.py --date 2026-07-06
validate: OK — citation closure holds.
Wrote report.md — 4 themes, 12 learnings, 11 pool papers, 5/5 flagged papers accounted for.
```

And the same placement question as step 2, with the same provisional answer: the report
is a document about the work, not data or machinery — it lands at the workspace root,
[`report.md`](report.md), next to the spec it fulfills. The user reads it and sends it.

**New on disk:** `tools/assemble_report.py` · `report.md`.

---

## Notes

- **The journey ran the canonical shape** ([the journey](../canon/the-journey.md)): the
  final state written down before any work (step 2), the route sketched as three coarse
  chunks, and every step after taken as a hop — with capability grown at exactly the hop
  that was blocked without it. Chunk one took six steps to unfold; chunks two and three
  took one each, because the hops inside chunk one had already deposited most of what
  they needed.
- **The deliverable was described before any work and generated after all of it** — the
  spec (step 2) and the report (step 10) bracket the journey, and both live at the root:
  the workspace's one unresolved placement question.
- **Everything stored, at every stage:** queries, raw results, filters, verdicts,
  learnings — each became records the moment it needed to outlive the conversation, and
  each got its schema at that moment, not in an up-front design phase.
- **The check earned its keep.** Validating the strategy against the flagged five caught
  a real hole (no query covered structured telephone support) *before* extraction, when
  fixing it cost one query — not after delivery, when it would have cost the client's trust.
- **Every rule ends up in two or three forms:** stated in `OVERVIEW.md` and
  `DELIVERABLE.md`, encoded in `schemas/` and `skills/`, and — where it must hold
  unconditionally — enforced by a tool. The `REFUSED` outputs above are the enforced form
  doing its job.

*To start your own workspace: copy [the template](../template/) to a new folder, open
Claude Code there, and point it at whatever source material your project already has.*
