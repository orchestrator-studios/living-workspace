---
name: reading-sessions
description: What a Claude Code session is on disk, how to read it, and what the two
  grades of "active" mean. The meaning layer for this workspace's bound substrate.
runs: in-context
---

# Reading Claude Code sessions

This workspace contains no data — its system of record is Claude Code's own state tree,
`~/.claude/`, read live and never written. This file is where the *meaning* of that
external data lives (a bound substrate keeps its understanding here and in `repo.py`,
not in `schemas/`, because there are no local records to validate).

## The layout

    ~/.claude/
      projects/
        <encoded-project>/
          <uuid>.jsonl                      ← a SESSION transcript (this is "a session")
          <uuid>/subagents/agent-*.jsonl    ← subagent transcripts, children of that session
      history.jsonl                         ← global prompt log across all projects

- **A session is a top-level `<uuid>.jsonl`.** The uuid is its id.
- **The folder name is a lossy encoding of the project path** — separators become `-`,
  and real path segments contain `-` too, so it cannot be reversed reliably. Do not
  decode it. The transcript records its own `cwd` on its early lines; that is the
  authoritative project path. `repo._resolve_cwd` reads it (and caches it — a file's cwd
  never changes).
- **Subagent transcripts are not sessions.** They belong to their parent session and are
  counted as a detail of it, never listed on their own.

## What the filesystem tells you for free

The catalog never parses a transcript — everything the list needs is a `stat()`:

- **last active** = mtime. When the transcript last changed.
- **age / created** = ctime (creation time on this platform).
- **size** = byte length, a rough proxy for how much happened.

Parsing is reserved for the *detail* of one opened session (turn counts, first prompt,
model, branch) — see `repo.session(session_id=...)`. Never parse the whole tree to build
the list; that is the difference between a 70ms poll and an unusable one.

## The two grades of active (defined once in repo.py)

| Grade | Definition | Meaning |
|---|---|---|
| **currently active** | mtime within **2 seconds** | someone is in this session *right now* |
| **recently active** | mtime within **5 minutes** | touched lately, probably still warm |

The constants (`CURRENTLY_ACTIVE_S`, `RECENTLY_ACTIVE_S`) live in `repo.py` and ride along
in the projection's `thresholds`, so the view labels them without a second copy. The
dashboard polls every 2 seconds — the same window as *currently active* — so a live
session lights up on the next tick after it writes.

## The one rule that matters

**Read-only.** Nothing in this workspace writes to `~/.claude/`. It is someone else's
system of record; we are only a lens. The enforcement is simple because the surface is
small: every access goes through `repo.py`, and `repo.py` only ever opens these files for
reading.
