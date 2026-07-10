---
name: bottom-line
description: Write the plain-language synthesis of what a table now says. Use after any
  material change — a populate, an enrichment, a refresh.
runs: in-context
---

# The bottom line

OVERVIEW rule 6, the soft rule with no hard form — and deliberately so. It is a judgment
about what the table *means*, and no tool can refuse a bad one.

*Runs in-context:* the synthesis is the thing the user actually reads, and it depends on
what they asked for, what they already know, and what changed since last time. A fresh
agent has none of that. Where [research-row](research-row.md) is delegated because the
conversation doesn't need the page text, this is in-context because the conversation is
precisely where its value lands.

## What it is

Two to five sentences answering *so what does the table say?* — written for someone who
will not read the rows:

- **Lead with the answer to the table's own question.** The table exists because the user
  asked something; say what it now answers.
- **Name the standouts by name**, with the number that makes them stand out.
- **Say what's still unknown**, if a column has meaningful gaps. An honest "—" is a
  finding.
- **No hedging, no restating the schema.** "Five of eight are open" — not "the status
  column contains a mix of values."

## Where it goes

On the table record, as `bottom_line` — so the catalog card and the table viewer both
render the same words (rule 8: one definition of every answer). Never write it into the
view.

    python -c "import repo; t=repo.load('table','T-001'); t['bottom_line']='...'; repo.save('table',t)"

Refresh it after every material change. A stale bottom line is a confident lie about the
substrate, exactly like a stale view.
