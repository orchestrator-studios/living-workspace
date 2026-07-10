---
name: findings-and-citations
description: Rules and workflow for extracting findings and keeping the report's citation integrity. Use whenever extracting claims from papers, organizing themes, or assembling the report.
runs: either
returns: |
  For each source mined: {source_id, findings: [{id, claim, theme}]}.
  Findings are already written via tools/add_finding.py — the return value is the
  report, not the deposit.
---

# Findings and citations

*Ambidextrous. Extraction from one paper's full text is a delegation candidate — the text
is bulky, the findings are small, and `add_finding.py` refuses a finding against an
excluded source no matter who holds the pen. Theme organization and report assembly stay
in-context: they are judgments about the whole review, and the user is steering them.*

## Rules

1. **A finding may only cite an included source.** This is the review's integrity guarantee:
   nothing in the client's report may reference a paper that wasn't screened in. The tool
   enforces it — `add_finding.py` refuses excluded and unscreened sources. Never work around
   it by writing findings by hand.
2. One finding = one claim from one source, with the supporting numbers in `evidence`.
   Composite claims get split.
3. Findings are organized under **themes**; a finding without a theme is unfinished
   synthesis, not an error.
4. The report is **assembled, never written**: `assemble_report.py` projects themes,
   findings, and included sources into `report.md`. Excluded sources appear only in its
   appendix, with reasons. Regenerate after any change; never edit `report.md` directly.

## Workflow

```
python tools/add_finding.py --source S-006 --outcome readmission --direction reduction \
    --claim "Pragmatic RCT found a significant reduction in 30-day readmission" \
    --evidence "n=1,022; 14.9% vs 19.6%; p=0.01" --theme T-01

python tools/validate.py            # citation closure is checked here too
python tools/assemble_report.py --date 2026-07-06
```
