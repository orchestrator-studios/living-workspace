#!/usr/bin/env python3
"""beam_board.py — re-render the board onto the BotBeam tab (grown). The
static-view discipline pointed at the bound external surface (OVERVIEW rule 5):
the "Life Infrastructure Backlog" display is regenerated from the substrate after
data changes — never hand-edited, never read back. Run it after a work session's
writes, or whenever the user says "beam the board".

It renders the same repo.board() answer the live dashboard shows (one definition
of every number) as markdown, and pushes it to the display tab via the BotBeam
skill script recorded in OVERVIEW ("Where the data lives today").

Usage:  python tools/beam_board.py [--dry-run]     (--dry-run prints the markdown)
"""
import argparse
import subprocess
import sys

import repo

# The render contains non-cp1252 glyphs (the stalled flag); Windows consoles
# default to a codepage that can't print them.
sys.stdout.reconfigure(encoding="utf-8")

BOTBEAM_SCRIPT = r"C:\code\botbeam\skill\botbeam\scripts\botbeam.py"
DEVICE = "nnQDZwhG"   # the "Life Infrastructure Backlog" display tab

STATUS_MARK = {"open": "[ ]", "done": "[x]", "someday": "[~]"}


def render(answer):
    lines = [f"# Life Infrastructure Backlog", ""]
    for area in answer["areas"]:
        lines += [f"## {area['name']}", ""]
        if not area["projects"]:
            lines += ["*(nothing here)*", ""]
            continue
        for p in area["projects"]:
            flag = " **⚠ stalled — needs a next action**" if p["stalled"] else ""
            lines.append(f"- {STATUS_MARK[p['status']]} {p['title']}{flag}")
            for a in p["actions"]:
                if a["status"] == "open":
                    when = (f"follow up {a['follow_up']}" if a["follow_up"]
                            else f"{a['days_stale']}d since last touch")
                    lines.append(f"  - → {a['description']} *({when})*")
        lines.append("")
    t = answer["totals"]
    lines += ["---",
              f"*{t['projects_open']} open projects ({t['stalled']} stalled) · "
              f"{t['actions_open']} open actions · rendered from the life-tracker "
              f"workspace as of {answer['as_of']} — this tab is a view, never a source.*"]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Re-render the board onto the BotBeam tab.")
    ap.add_argument("--dry-run", action="store_true", help="print the markdown, beam nothing")
    args = ap.parse_args()

    body = render(repo.board())
    if args.dry_run:
        print(body)
        return 0
    result = subprocess.run(
        [sys.executable, BOTBEAM_SCRIPT, "existing", "--device", DEVICE,
         "--type", "markdown", "--body", body],
        capture_output=True, text=True)
    if result.returncode != 0:
        print(f"BEAM FAILED: {result.stderr.strip() or result.stdout.strip()}")
        return 1
    print(f"OK — board beamed to BotBeam tab {DEVICE} ({len(body)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
