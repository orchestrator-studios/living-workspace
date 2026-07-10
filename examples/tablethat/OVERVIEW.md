# System Overview

*Drafted at intake from the TableThat repo (`C:\code\table-that` — the backgrounder in
`_product-GTM/`, the specs in `_specs/product/`) and conversation with the user.*

## Purpose

Replicate **TableThat** — the AI table builder live at tablethat.ai — as a living
workspace. TableThat's core loop is **Build → Populate → Enrich**: the user describes a
table in plain English; a typed schema is proposed and approved before anything is
created; live research proposes real entities as rows; new columns are researched
per-row and coerced to the column's type, without disturbing existing data. The app does
this with a FastAPI backend, a React frontend, and ~14 tools. This workspace does it
with the standard kit, two fixed meta-schemas, and conversation.

The workspace's schema is **meta, and fixed**: it describes tables-in-general, and the
user's tables are *data inside it* — exactly as they are in the app's own database. The
user's schema is emergent; the workspace's schema never changes as tables are added.

## The things

- **table** — the definition of one user-commissioned table (`T-001`…): name,
  description, and its ordered columns — each a key, label, type (text / number / date /
  boolean / select-with-options), and whether it's required. The catalog of tables is a
  query over these records, not a folder listing.
- **row** — one real-world entity in one table (`R-0001`…): its `table_id`, a `values`
  map keyed by column key, a `provenance` map (column key → source URL or stated basis),
  and the date it was researched.

## The rules

1. **The Build gate — the only gate.** A table's schema is proposed in conversation and
   approved by the user before it is created. (TableThat: "user reviews and approves
   before anything is created.") Rows and enrichments are *not* gated: the agent commits
   them and the user audits on the live board — the board is the review surface.
   *(Agreed at intake, 2026-07-09.)*
2. **Populated from research, not memory.** Rows and researched values come from live
   web research; entities are real and checkable, never generated from training data
   alone.
3. **Enrich never disturbs.** Adding a column fills only the new column. Existing values
   are never modified without explicit user approval. (TableThat: "existing data is
   never touched without approval.")
4. **Every value conforms to its column type.** A row's values must match *its table's*
   declared columns — a cross-record rule between a row and its table, enforced by the
   grown `integrity_checks()` in `tools/validate.py`, checked after every write.
5. **Every researched value carries its source.** Provenance is recorded alongside the
   value — the workspace-native upgrade of TableThat's "Research Cascade."
6. **The Bottom Line.** After any material change — a populate, an enrichment — surface
   a short plain-language synthesis of what the table now says. (Soft rule: lives as a
   skill, not an enforcer.)

## Where the data lives today

- Nothing to migrate — tables start empty and fill from live research at populate and
  enrich time.
- Reference material (bound, read-only): the original app at `C:\code\table-that\` —
  used to check behavioral fidelity, not as a data source.

## What you'll ask of it

- **Build:** "Make me a table of X" → column proposal → approval → a `table` record.
- **Populate:** "Fill it in" → live research → `row` records appear on the board.
- **Enrich:** "Add a column for Y" → the table record grows a column → per-row research
  fills it, touching nothing else.
- **Typed asks:** filter, sort, count — *parameterized* named queries (`?table_id=…`):
  one question, asked of whichever table you point it at, never all tables at once.
- **Bottom line:** "So what does it say?" → the synthesis, on demand and after changes.
- **Export:** any table as CSV — a static view assembled by a tool.
