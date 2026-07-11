# This repo is three things — route accordingly

This is the **living-workspace** repository: canon (how it works), worked examples, and a
starter template. The root is *not* a workspace; do not create data, schemas, tools, or
views here.

- **Understanding or explaining the system** → read `canon/` (definition, move rule,
  anatomy, operating manual).
- **Exploring or operating a worked example** → work inside its folder under `examples/`.
  Each example's own `CLAUDE.md` governs there; treat it as a live workspace (validate
  after writes, keep the live board up, regenerate outputs, use its tools). The examples:
  `lit-review` (client-commissioned literature review), `tablethat` (AI table builder,
  replicating `C:\code\table-that`), `newsletter` (weekly literature-monitoring
  newsletter, modeled on Knowledge Horizon's talc/asbestos stream), `life-tracker`
  (personal life-infrastructure tracker, seeded from the user's BotBeam backlog; beams
  its board back to BotBeam), `session-tracker` (a live dashboard over every Claude Code
  session on the machine — a purely **bound, read-only** lens on `~/.claude/`, so `data/`
  and `schemas/` stay empty and all the meaning lives in the read layer).
- **The user wants to start their own workspace** → copy `template/` to a new location
  *outside this repo* and begin there with the interview. Don't scaffold workspaces here.
- **Editing the canon or template** → these are the published doctrine and the published
  starting point; keep them general (nothing example-specific), and keep
  `template/CLAUDE.md` in sync with the canonical text in `canon/operating-manual.md`.
