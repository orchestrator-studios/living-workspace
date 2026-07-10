# This repo is three things — route accordingly

This is the **living-workspace** repository: canon (how it works), a worked example, and a
starter template. The root is *not* a workspace; do not create data, schemas, tools, or
views here.

- **Understanding or explaining the system** → read `canon/` (definition, move rule,
  anatomy, operating manual).
- **Exploring or operating the worked example** → work inside `example/`. Its own
  `CLAUDE.md` governs there; treat it as a live workspace (validate after writes, keep
  the live board up, regenerate the report, use its tools).
- **Working on TableThat** → work inside `tablethat/`, a live workspace being grown as a
  second test of the concept (replicating the TableThat app, `C:\code\table-that`). Its
  own `CLAUDE.md` governs there.
- **The user wants to start their own workspace** → copy `template/` to a new location
  *outside this repo* and begin there with the interview. Don't scaffold workspaces here.
- **Editing the canon or template** → these are the published doctrine and the published
  starting point; keep them general (nothing example-specific), and keep
  `template/CLAUDE.md` in sync with the canonical text in `canon/operating-manual.md`.
