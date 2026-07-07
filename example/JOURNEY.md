# The Journey — from empty folders to a delivered report

This is the timeline of how this workspace came to be: **eight milestones, all in this one
document**, each linking to the live files it produced. No git archaeology required — the
finished workspace is the tree around you; this file is how it got that way.

Every milestone is one firing of the same rule (see
[the move rule](../canon/the-move-rule.md)): state the want; **if it's reachable with what
exists, do it** — otherwise **grow** the missing capability (access → understanding →
presentation), then do it. The badge on each milestone says which branch fired.

*(Client, correspondence, and papers are fictional throughout.)*

---

<a id="m0"></a>
## m0 · The Template

**The starting point — before any want.** Five empty folders, an operating manual
([CLAUDE.md](CLAUDE.md)), and an unfilled overview (the skeleton is what
[the template](../template/OVERVIEW.md) still holds). Nothing installed, nothing configured.

```
OVERVIEW.md (skeleton)   CLAUDE.md
data/ (empty)   schemas/ (empty)   tools/ (empty)   skills/ (empty)   views/ (empty)
```

Then the client file arrives: an email thread, a brief, and five flagged papers — dropped
into [`seed/`](seed/). The project has source material before it has anything else. Watch
which folder wakes up when: the order is the whole lesson.

---

<a id="m1"></a>
## m1 · The Intake — **GROW: understanding**

**The want:** "Set up the project from the client's file."

Not reachable — the workspace doesn't yet *understand* the assignment. So the first move
grows understanding at its highest level: the agent reads
[`seed/client-email-thread.md`](seed/client-email-thread.md) and
[`seed/brief.md`](seed/brief.md), drafts the overview, and interviews for what the file
doesn't say (*What counts as "remote monitoring"? Do systematic reviews count as primary?
What happens to papers we rule out?*).

**What was added:** [OVERVIEW.md](OVERVIEW.md), filled — the question, the four things,
the rules (including the client's own ground rule: *"we've been burned before by
consultants' reviews citing things nobody screened"*), where the data lives, the recurring
asks.

```
OVERVIEW.md ✓ filled   ·   everything else still empty
```

---

<a id="m2"></a>
## m2 · The Agreement — **GROW: understanding**

**The want:** "Manage the sources and what we take from them, properly."

Not reachable — the things have no agreed shape. The agent proposes four, straight from the
overview; the user says yes. The smallest possible hop:

**What was added:** [`schemas/source.schema.json`](schemas/source.schema.json) ·
[`schemas/finding.schema.json`](schemas/finding.schema.json) ·
[`schemas/theme.schema.json`](schemas/theme.schema.json) ·
[`schemas/search.schema.json`](schemas/search.schema.json)

The conversation is *in* the schemas. From `source.schema.json`: every screening decision
carries the criterion it was decided on. From `finding.schema.json`: a finding names
exactly one source. The rules stated in m1 are now machine-checkable shape.

```
OVERVIEW.md ✓   schemas/ 4   ·   data/ tools/ skills/ views/ still empty
```

---

<a id="m3"></a>
## m3 · The Move-In — **DO IT**

**The want:** "Pull in the papers the client already flagged."

**Reachable — nothing new needed.** The access exists (the client file is in `seed/`), the
understanding exists (the source schema). The agent reads
[`seed/flagged-papers.csv`](seed/flagged-papers.csv) and writes five source records into
[`data/sources/`](data/sources/), each `unscreened`, each marked `found_via: seeded`.
Screening follows the same day — against the brief's criteria, decision by decision:
three in, two out (an atrial-fibrillation study: wrong population; an editorial: not
primary research).

```
OVERVIEW.md ✓   schemas/ 4   data/ 5 sources (3 included · 2 excluded)
```

The first milestone that deposits nothing — and that's the point. Moves get cheaper as
capability accumulates.

---

<a id="m4"></a>
## m4 · The Mirror — **GROW: presentation**

**The want:** "The project is seeded — but how do I *know*? I want to see what we've got,
not ask about it record by record."

Not reachable — no way of *seeing* exists yet. So the move grows presentation:

**What was added:** [`views/build_screening_board.py`](views/build_screening_board.py) →
[`views/screening_board.html`](views/screening_board.html) — three columns (unscreened ·
included · excluded), a card per source with how it was found and why it was decided,
regenerated from `data/` after every change, never hand-edited.

```
$ python views/build_screening_board.py
Wrote views/screening_board.html — 0 unscreened · 8 included · 4 excluded.
```

```
OVERVIEW.md ✓   schemas/ 4   data/ growing   views/ 1 board   ·   tools/ skills/ still empty
```

---

<a id="m5"></a>
## m5 · The Routine — **GROW: access**

**The want:** "Run the sweeps from the brief's criteria — and I keep seeing the same papers
from different queries. Duplicates can't get in."

The searching is conversation; the *adding* needs a guarded path that doesn't exist. One
tool arrives, alone:

**What was added:** [`tools/add_source.py`](tools/add_source.py) — assigns ids, records
provenance (`found_via: search:Q-01`), and checks the DOI against every source already in
the review. Two sweeps get logged as data ([`data/searches/`](data/searches/)); seven new
sources enter; and the refusals happen for real:

```
$ python tools/add_source.py --doi 10.9999/fict.2024.0117 ...
REFUSED: DOI already in the review (S-003, added from the client's flagged list).
```

```
OVERVIEW.md ✓   schemas/ 4   data/ 12 sources + 2 searches   views/ 1   tools/ 1   skills/ –
```

---

<a id="m6"></a>
## m6 · The Guarantee — **GROW: understanding (hard form)**

**The want:** "Nothing in the client's report may cite a paper we screened *out*. And I
don't want to rely on either of us remembering what got excluded."

*"I don't want to rely on either of us remembering"* is the whole architecture of this
milestone. The rule already exists as prose (m1) and shape (m2); now it becomes
*enforcement* — captured twice, in two forms:

**What was added:**
[`skills/screening.md`](skills/screening.md) and
[`skills/findings-and-citations.md`](skills/findings-and-citations.md) — the rules in
language, for the agent to reason with; and
[`tools/screen.py`](tools/screen.py), [`tools/add_finding.py`](tools/add_finding.py),
[`tools/validate.py`](tools/validate.py) — the rules in code, for when nobody's reasoning.

Extraction proceeds: nine findings from the eight included sources, organized under four
themes. And the guarantee holds when tested — try to extract a finding from the excluded
atrial-fibrillation study:

```
$ python tools/add_finding.py --source S-004 ...
REFUSED: source S-004 is excluded (Atrial fibrillation cohort, not heart failure).
Findings may only cite included sources.

$ python tools/screen.py --source S-004 --decision included ...
REFUSED: S-004 is already excluded — screening decisions are frozen.

$ python tools/validate.py
OK — 27 records valid; citation closure holds (no finding cites anything but an included source).
```

Not the model remembering the rule. The substrate *being* the rule.

```
OVERVIEW.md ✓   schemas/ 4   data/ 27 records   views/ 1   tools/ 5   skills/ 2
```

---

<a id="m7"></a>
## m7 · The Handoff — **DO IT**

**The want:** "Assemble the client's report."

**Reachable — every capability already exists.** The access (all sources in, all screened),
the understanding (findings themed, closure enforced), the presentation (the assembler
projects the substrate into the deliverable). The biggest deliverable in the project is
the smallest move in it:

```
$ python tools/assemble_report.py --date 2026-07-06
Wrote report.md — 4 themes, 9 findings, 8 included sources; every claim cites an included source.
```

**The deliverable:** [report.md](report.md) — question, method (searches logged, counts,
criteria), findings by theme with citations, included-sources list, and the exclusions
appendix with reasons — exactly what the client asked for in
[the original email](seed/client-email-thread.md). It is generated, never hand-written:
run the assembler again tomorrow and it will say whatever the data says then.

```
OVERVIEW.md ✓   schemas/ 4   data/ 27 records   views/ 1   tools/ 6   skills/ 2   report.md ✓
```

---

## What to notice

- **The folders woke in need-order, not build-order** — understanding first (m1, m2), data
  second (m3), a view before any tool (m4), tools when repetition demanded a guarded path
  (m5), enforcement when a rule had to outlive memory (m6). A conventional project builds
  this stack in reverse.
- **The two "DO IT" milestones teach as much as the five "GROW"s.** m3 was cheap because
  m1–m2 paid for it; m7 was nearly free because everything paid for it. Every move pays
  twice — the task done, and the capability that remains.
- **There was never a launch.** The workspace was in use from m1 and never stopped being
  built. That's not a phase that ended; it's what kind of thing this is.

*Start your own: copy [the template](../template/) to wherever your project will live, open
Claude Code there, and point it at whatever the project already has.*
