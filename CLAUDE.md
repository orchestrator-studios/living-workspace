# This repo is four things — route accordingly

This is the **living-workspace** repository: canon (how it works), a worked example, a
starter template, and one live workspace we run ourselves. The root is *not* a workspace;
do not create data, schemas, tools, or views here.

- **Understanding or explaining the system** → read `canon/` (definition, move rule,
  anatomy, operating manual).
- **Exploring or operating the worked example** → work inside `example/`. Its own
  `CLAUDE.md` governs there; treat it as a live workspace (validate after writes,
  regenerate views, use its tools).
- **Working in `working/`** → that's our own live workspace — the dogfood. Its own
  `CLAUDE.md` governs there; this file only routes. Nothing in `working/` is doctrine:
  don't generalize from it into `canon/` or `template/` without being asked.
- **The user wants to start their own workspace** → copy `template/` to a new location
  *outside this repo* and begin there with the interview. `working/` is the one live
  workspace that belongs in this repo; don't scaffold others here.
- **Editing the canon or template** → these are the published doctrine and the published
  starting point; keep them general (nothing example-specific), and keep
  `template/CLAUDE.md` in sync with the canonical text in `canon/operating-manual.md`.
