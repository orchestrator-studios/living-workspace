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
Each step closes with its **delta** — the difference between the workspace before and
after, split along the two axes state evolves on:

| Content & data | Capability |
|---|---|
| what is now *known and recorded* — documents, records, results | what can now be *done* — schemas, tools, skills, views |

A dash means that axis didn't move. Watching which column fills, step by step, is half
the story of this journey.

*(Draft note: terminal output in this version is illustrative — the client and the papers
are fictional. The tooling is real, though: `tools/search_pubmed.py` already runs against
the live PubMed API. Outputs will be replaced with real captured runs once the workspace's
artifacts are regenerated to match this journey.)*

*(Client, correspondence, and papers are fictional throughout.)*

---

## Before the first request

What the user did before talking to Claude at all: copied [the template](../template/) —
`CLAUDE.md`, the blank `OVERVIEW.md`, the standard kit (the data-access skeleton, the
dashboard server, the validator, the dashboard skill and index page), and the empty
`data/` and `schemas/` folders — into a new project folder;
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

| Content & data | Capability |
|---|---|
| `OVERVIEW.md` — from skeleton to filled | — |

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

| Content & data | Capability |
|---|---|
| `DELIVERABLE.md` — the destination and the route | — |

---

## 3 · Write the queries

**Ask:** "Draft the search queries. I want to see them before anything runs."

The brief names the venue: everything runs on PubMed. So Claude drafts four PubMed
queries — telemonitoring × readmission, home devices × mortality, wearables for HF
management, RPM × cost — each written in PubMed's own syntax, MeSH terms plus
title/abstract terms, with a one-line rationale tying it to a brief criterion. Q-01, for
instance:

```
"heart failure"[MeSH Terms]
  AND (telemonitoring[Title/Abstract] OR "remote patient monitoring"[Title/Abstract])
  AND ("patient readmission"[MeSH Terms] OR readmission[Title/Abstract])
```

Then the first gap: the queries need to be *kept*, not just shown in chat — they'll be
run, revised, and cited by the report's method section. There is nowhere to put them. So
Claude proposes a query record — id, query text, database, rationale, status — the user
approves it, and it becomes the workspace's first schema. The four queries are written as
records.

| Content & data | Capability |
|---|---|
| `data/queries/Q-01…Q-04.json` — the search strategy, on the record | `schemas/query.schema.json` — the workspace's first schema |

---

## 4 · Run the queries

**Ask:** "Run them. Keep everything that comes back — I want the raw results, not your
summary of them."

Two gaps at once. There's no path to PubMed — that's a tool. And raw results need a home
of their own, separate from the queries that produced them — that's a second schema.
Claude writes [`tools/search_pubmed.py`](tools/search_pubmed.py) — a wrapper around
NCBI's E-utilities: `esearch` turns the query into PMIDs, `efetch` pulls each record —
and `schemas/result.schema.json`: one result record per query run — query id, date, hit
count, and the hits themselves, verbatim: title, authors, year, venue, PMID, DOI,
abstract, and PubMed's publication types.

```
$ python tools/search_pubmed.py --query Q-01
Q-01 → esearch: 41 PMIDs · efetch: 41 records → data/results/R-01.json

$ python tools/search_pubmed.py --query Q-02
Q-02 → esearch: 17 PMIDs · efetch: 17 records → data/results/R-02.json
```

Four runs, 96 raw hits, untouched and unjudged. Overlap between queries is expected and
preserved — deduplication is a judgment about *papers*, and papers don't exist as records
yet.

| Content & data | Capability |
|---|---|
| `data/results/R-01…R-04.json` — 96 raw hits, kept verbatim | `tools/search_pubmed.py` — the path to PubMed (NCBI E-utilities) · `schemas/result.schema.json` |

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
cost query's filter, for instance, spells out what counts as a cost outcome). Where PubMed
already knows the answer, the filter says so: the study-type criterion keys off the
publication types that came back with each hit — an editorial declares itself.

Filters are records too — they'll be applied, cited, and possibly revised — so they get a
schema and a folder.

| Content & data | Capability |
|---|---|
| `data/filters/F-01…F-04.json` — the judgment standard, written down, one per query | `schemas/filter.schema.json` |

---

## 6 · Run the results through the filters

**Ask:** "Now run every hit through its filter. I want a verdict per paper per criterion —
and show me the pool somewhere I can look at it."

This is where hits become *papers*. Claude writes `schemas/paper.schema.json` — one record
per unique paper: citation, which queries retrieved it (matched on PMID, the 96 hits
collapse to 71 unique papers), and a verdict block: per-criterion pass/fail with a reason,
and the overall call. Applying a filter is a judgment, but *recording* it is an operation
with rules — the same PMID never judged twice, a verdict once recorded is frozen — so the
recording goes through a tool, [`tools/apply_filter.py`](tools/apply_filter.py), which enforces both.

```
$ python tools/apply_filter.py --paper P-054 --filter F-03 --verdict fail \
    --criterion population --reason "Atrial fibrillation cohort, not heart failure"
P-054: FAIL on population — recorded, frozen.

$ python tools/apply_filter.py --paper P-054 --filter F-03 --verdict pass ...
REFUSED: P-054 already has a verdict. Verdicts are frozen.
```

And the seeing: the workspace's first view, grown as exactly the two pieces a view costs —
a `pool_board` projection in the kit's `tools/repo.py` (every paper as a card, pass/fail
columns, the failing criterion on the card — the numbers defined once, where every surface
can reach them) and [`views/pool_board.template.html`](views/pool_board.template.html).
The kit's server binds the two with no wiring: the board appears on the dashboard's index
the moment the template exists, and the user — who has had the page open since the first
search ran (rule 9) — watches the columns fill as the 71 papers are judged. **9 pass.**
Nothing to regenerate, ever: the board reads the data live and cannot go stale.

| Content & data | Capability |
|---|---|
| `data/papers/P-001…P-071.json` — 71 papers judged, verdicts frozen, 9 in the pool | `schemas/paper.schema.json` · `tools/apply_filter.py` — carries the dedup and frozen-verdict rules · the `pool_board` projection in `tools/repo.py` + `views/pool_board.template.html` — the workspace's first live view |

---

## 7 · Check the flagged five

**Ask:** "Moment of truth. Dr. Reyes's five papers — are they in that pool? Check it
properly, don't eyeball it."

"Properly" means deterministically: Claude writes [`tools/check_flagged.py`](tools/check_flagged.py),
which reads the client's CSV and reports, for each flagged paper — matched by its PubMed
ID — whether any query retrieved it and what verdict it got.

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

| Content & data | Capability |
|---|---|
| — (the check's verdict drives the next step; nothing new is recorded) | `tools/check_flagged.py` — the strategy validator, rerunnable at any time |

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

| Content & data | Capability |
|---|---|
| `data/queries/Q-05.json` · `data/filters/F-05.json` · `data/results/R-05.json` · two paper records — the pool is now 11 · `DELIVERABLE.md` gains its validation section | — (nothing built; the existing machinery carried the whole repair) |

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
and worded, one claim per record, recorded only through the tool), and two enforcements —
[`tools/add_learning.py`](tools/add_learning.py), which **refuses any paper not in the
pool**, and the cross-record rules grown into the kit's
[`tools/validate.py`](tools/validate.py): no duplicate PMIDs, every verdict carries its
criterion and reason, and no learning cites anything outside the pool.

```
$ python tools/add_learning.py --paper P-054 ...
REFUSED: P-054 failed its filter (population: atrial fibrillation, not heart failure).
Learnings may only cite papers in the pool.

$ python tools/validate.py
OK — 94 records valid; citation closure holds (no learning cites outside the pool).
```

Twelve learnings, compiled under four themes: 30-day readmissions, mortality and
long-term outcomes, adherence and engagement, cost.

| Content & data | Capability |
|---|---|
| `data/learnings/L-001…L-012.json` — twelve claims under four themes | `schemas/learning.schema.json` · `skills/learnings.md` · `tools/add_learning.py` — the pool-only citation gate · the global closure check, grown into the kit's `tools/validate.py` |

---

## 10 · Generate the report

**Ask:** "Generate the client's report."

One sentence, because everything it needs already exists. Claude writes
[`tools/assemble_report.py`](tools/assemble_report.py) — the report is *generated from
the data*, never written by hand: the question; the method (five PubMed queries with
their filters, logged runs and counts, the flagged-five validation including the strategy
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

| Content & data | Capability |
|---|---|
| `report.md` — the deliverable itself | `tools/assemble_report.py` — regenerates it from the data, any time |

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
- **Read the delta tables down the page** and the workspace's economics are visible in
  one pass: the capability column is busiest early (steps 3–7) and the content column
  late — because [every move pays twice](../canon/the-move-rule.md), and the capability
  deposited by early steps is what lets late steps be pure content. Step 7 lands nothing
  but capability; step 8, its repair, lands nothing but content — the machinery already
  existed. Step 10 delivers the whole report as one row of content.
- **Everything stored, at every stage:** queries, raw results, filters, verdicts,
  learnings — each became records the moment it needed to outlive the conversation, and
  each got its schema at that moment, not in an up-front design phase.
- **The check earned its keep.** Validating the strategy against the flagged five caught
  a real hole (no query covered structured telephone support) *before* extraction, when
  fixing it cost one query — not after delivery, when it would have cost the client's trust.
- **The kit never appears in the delta tables** — the data-access layer, the dashboard
  server, the validator's generic checker, and the dashboard skill were all there before
  step 1, because they're the same in every workspace. What the journey grew *into* them
  is visible everywhere: the projections in `repo.py` (step 6), the integrity checks in
  `validate.py` (step 9). The seam between shipped and grown is exactly the seam between
  [the system and the domain](../canon/anatomy.md#the-standard-kit).
- **Every rule ends up in two or three forms:** stated in `OVERVIEW.md` and
  `DELIVERABLE.md`, encoded in `schemas/` and `skills/`, and — where it must hold
  unconditionally — enforced by a tool. The `REFUSED` outputs above are the enforced form
  doing its job.

*To start your own workspace: copy [the template](../template/) to a new folder, open
Claude Code there, and point it at whatever source material your project already has.*
