# This repo is three things — route accordingly

This is the **living-workspace** repository: canon (how it works), a worked example, and a
starter template. The root is *not* a workspace; do not create data, schemas, tools, or
views here.

- **Understanding or explaining the system** → read `canon/` (definition, move rule,
  anatomy, operating manual).
- **Exploring or operating the worked example** → work inside `example/`. Its own
  `CLAUDE.md` governs there; treat it as a live workspace (validate after writes,
  regenerate views, use its tools).
- **The user wants to start their own workspace** → copy `template/` to a new location
  *outside this repo* and begin there with the interview. Don't scaffold new projects
  inside this repo.
- **Editing the canon or template** → these are the published doctrine and the published
  starting point; keep them general (nothing example-specific), and keep
  `template/CLAUDE.md` in sync with the canonical text in `canon/operating-manual.md`.
