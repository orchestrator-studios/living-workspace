# views/ — view logic (templates)

This folder holds the **presentation logic** for views: the templates. It does **not** hold
rendered output.

Every view separates four parts (see
[the anatomy of a view](../../canon/anatomy.md#the-anatomy-of-a-view)):

| Part | Lives in | Here, that is |
|---|---|---|
| **Data access** — the named queries | `tools/repo.py` | `screening_board()` (grown) |
| **Code** — binds a query's answer to a rendering | `tools/` | `server.py` (kit) · `assemble_report.py` (grown) |
| **Template** — the markup | **here** | `index.template.html` (kit) · `screening_board.template.html` (grown) |
| **Instance** — the rendered result | live: served on demand · static: `report.md` at the root | |

## The views this workspace has

**The live screening board** — grown as exactly two pieces: the `screening_board`
query in `tools/repo.py` and `screening_board.template.html` here. The kit's server
binds them with no wiring — the page at `/view/screening_board`, the answer it polls at
`/api/screening_board` — and the board updates as screening decisions land in
`data/sources/`:

```bash
python tools/server.py        # → http://127.0.0.1:8765/
```

Because the server re-asks the query through `repo.py` on every request, the board is
real-time by construction: the same query every other tool renders, answered fresh.

**The report** — the static deliverable, assembled to `report.md` at the workspace root by
`tools/assemble_report.py` (it refuses to run unless validation passes). Regenerate (never
hand-edit) after any data change:

```bash
python tools/assemble_report.py --date YYYY-MM-DD
```
