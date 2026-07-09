# views/ — view logic (templates)

This folder holds the **presentation logic** for views: the templates. It does **not** hold
rendered output — that was true here once (a committed `screening_board.html`), and the file
is gone: the board went live.

Every view is built from four separable parts (see
[the anatomy of a view](../../canon/anatomy.md#the-anatomy-of-a-view--and-how-views-mature)):

| Part | Lives in |
|---|---|
| **Data access** — reads the data, defines the projections | `tools/repo.py` (the one data-access layer) |
| **Code** — binds a projection into a rendering | `tools/` (`server.py`, `assemble_report.py`) |
| **Template** — the presentation markup | **here** (`screening_board.template.html`) |
| **Instance** — the rendered result | live: served on demand · static: `report.md` at the root |

## The two views this workspace has

**The live screening board** — server-backed; renders nothing to disk. `tools/server.py`
(stdlib only) serves `screening_board.template.html` with the board projection baked in, and
the page polls `/api/board`, re-rendering as screening decisions land in `data/sources/`:

```bash
python tools/server.py        # → http://127.0.0.1:8765/
```

Because the server reads through `repo.py` on every request, the board is real-time by
construction: no rebuild step, no direct data reads — the same projection every other tool
sees, served fresh.

**The report** — the static deliverable, assembled to `report.md` at the workspace root by
`tools/assemble_report.py`. Regenerate (never hand-edit) after any data change:

```bash
python tools/assemble_report.py --date YYYY-MM-DD
```
