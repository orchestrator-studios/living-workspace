---
name: research-row
description: Research one entity's values for one table's columns, from live sources,
  and add it as a row. Use during Populate (a new entity) and Enrich (a new column).
runs: delegated
returns: |
  {id, name, filled: [column keys with values], unknown: [column keys left null],
   note?: one line if something surprising turned up}.
  The row is already written via tools/add_row.py — the return value is the report,
  not the deposit. On refusal (duplicate, type violation, missing provenance), return
  {refused: the tool's message} and write nothing.
---

# Researching one row

The soft form of OVERVIEW rules 2, 4, and 5. The hard form is `tools/add_row.py`, which
refuses a duplicate, a value that violates its column's type, and any non-null value
with no provenance.

## Why this is delegated

Filling one row means fetching guideline pages, chasing redirects, reading around 403s,
and searching when a fetch fails — thousands of tokens of page text per entity, of which
maybe forty words survive into the table. The conversation needs the forty words. A
fan-out of one fresh agent per entity keeps the session's context flat no matter how wide
the table grows, and the rows land in `data/` regardless, because the delegate writes
through the tool.

The rule of thumb: **the flood is bulky, the conclusion is small, and the deposit is
durable.** That's the delegation signature.

Delegation cannot substitute for the Build gate. A schema — what columns a table has —
is agreed with the user in conversation (OVERVIEW rule 1). A delegate fills columns; it
never invents them.

## The procedure

1. **Read the table's definition** — `python -c "import repo, json;
   print(json.dumps(repo.load('table','T-001')['columns'], indent=2))"` — so you know the
   column keys, types, and the options a select column allows.
2. **Research the entity from live sources.** Prefer the primary source (the
   organization's own page) over aggregators; an aggregator is acceptable provenance when
   the primary is unreachable, and should be named as such.
3. **One value per column, or null.** A guess is worse than a null — the board shows "—"
   honestly and the gap is enrichable later. Coerce to the column's type: a number is a
   number, a date is `YYYY-MM-DD`, a select is exactly one of its declared options.
4. **Provenance for every non-null value** — the URL you read it from, plus a short
   parenthetical when the page says it in different words than the cell does
   (`"...guidelines (14 cents/word)"`). A value whose source you cannot name is a value
   you do not have.
5. **Write through the tool**, never by hand:

       python tools/add_row.py T-001 --file row.json

   where `row.json` is `{"values": {...}, "provenance": {...}, "researched": "YYYY-MM-DD"}`.

6. **Report back** in the contract's shape. If the tool refuses, do not retry around it —
   the refusal is information. Return it.

## Enrich is the same capability, narrowed

Adding a column to an existing table is this procedure restricted to one column across
many rows: research that column's value for each row, fill only it, touch nothing else
(OVERVIEW rule 3). One delegate per row, same contract.
