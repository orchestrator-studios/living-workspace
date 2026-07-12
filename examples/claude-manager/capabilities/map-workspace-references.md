---
name: map-workspace-references
description: Read a workspace's capabilities and extract the SEMANTIC reach edges a machine
  can't parse — enriching its graph in the Workspaces module. Use on demand for one workspace.
runs: delegated
returns: |
  {workspace_id, added: <count>, note?}. The edges are already written via
  tools/write_workspace_graph.py — the return value is the report, not the deposit.
  On refusal, return {refused: the tool's message}.
---

# Mapping a workspace's semantic reach edges

The reach graph in the Workspaces module (`/view/workspace?workspace_id=<name>`) has a
**deterministic skeleton** — computed live, free, every poll: view→query bindings,
schema→projection, and the references a regex can catch in capability prose (`[[wikilinks]]`,
`tools/x.py`, `` `x.py` ``, `repo.fn`). What it can't catch is the **semantic** wiring: a
capability that says "the verdict tool refuses X" without naming the file, that *gates* on
another, that is *about* a kind it never backticks. That reading-comprehension pass is this
capability's job.

## Why this is delegated, on demand

Reading every capability's full prose to infer relationships is bulky-in, small-out — an
edge list — and it's a judgment call, not a lookup. So it's a delegated agent pass, run when
asked (not every poll), and cached as a contained `wsgraph` record the graph merges in
(drawn dashed). Same shape as session summaries.

## The procedure

You're given a `workspace_id` (e.g. `tablethat`).

1. **See the live graph's nodes** — the edges you emit must reference existing node ids:

       cd <this workspace> && python -c "import sys,json; sys.path.insert(0,'tools'); import repo; g=repo.workspace('WORKSPACE_ID')['graph']; print(json.dumps([n['id'] for n in g['nodes']]))"

   Node ids look like `cap:<name>`, `tool:<file.py>`, `schema:<kind>`, `query:<name>`,
   `view:<name>`.

2. **Read the workspace's capabilities** — `<workspace>/capabilities/*.md`, in full. This
   is bulky; read it in YOUR context, it must not reach the caller.

3. **Emit the edges the skeleton missed** — only *semantic* ones (don't re-emit obvious
   `tools/x.py` mentions the regex already has). Good relations: `about` (a capability is
   about a kind), `gates` (a capability gates a write behind approval), `enforces` (names a
   rule a tool enforces), `ref` (a conceptual link to another capability). Each edge:
   `{"from": "<node id>", "to": "<node id>", "kind": "<relation>", "note": "<why, short>"}`.
   Endpoints MUST be node ids from step 1 — invalid ones are dropped.

4. **Write them** (the tool keeps only edges whose endpoints are real nodes):

       cd <this workspace> && python tools/write_workspace_graph.py WORKSPACE_ID --file edges.json --model claude-fable-5

5. **Return** `{workspace_id, added: <count>}`, or the tool's refusal.

Keep it honest: an edge should be defensible from the prose, not decorative. A sparse,
correct map beats a dense, speculative one.
