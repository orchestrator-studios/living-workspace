# Skill: screening records

Decide each record against the protocol's inclusion criteria. Judge from title + abstract
first; escalate to full text only when the abstract is genuinely ambiguous.

## Decision rule
Mark `status: included` only if ALL inclusion criteria plausibly hold. Otherwise `excluded`
with the single most decisive `exclusion_reason` and the `screening_stage` at which you decided.

## Reason vocabulary (this review)
- `not-mouse` — primary model is rat, human, or other species (or human epidemiology).
- `no-genetic-modification` — asbestos/mesothelioma study with no defined mutant/transgenic model.
- `no-asbestos-exposure` — mesothelioma model without asbestos/mineral-fibre exposure.
- `no-mesothelioma-outcome` — asbestos + genetics but the measured outcome isn't mesothelioma.
- `in-vitro-only` — cell lines / organoids only, no in-vivo mouse tumor endpoint.
- `review-or-commentary` — review, editorial, or perspective, not primary data.
- `not-primary-research` — methods, protocol, conference abstract with no results, etc.
- `not-susceptibility-focus` — uses a genetic mesothelioma model but does NOT assess how the
  genotype affects susceptibility: e.g. drug/chemoprevention, biomarker, expression-profiling,
  model-building, or fibre-toxicity studies with no genotype-vs-comparator incidence/latency result.
  (A full-text-stage reason — the abstract often looks on-topic until you check the aim.)
- `wrong-language` — not assessable in English and no translation.
- `duplicate` — same study as another retained record.

## Conservative bias
When a title/abstract can't rule a study out, do NOT exclude it — either mark it `included`
pending full-text, or fetch the full text before deciding. False exclusions are the costly error
in a systematic review; a few false inclusions get caught at extraction.

## Borderline cases for this topic
- Rat models (e.g. many classic crocidolite studies) → `not-mouse`, even if excellent.
- Genetically engineered mouse mesothelioma models with NO asbestos (spontaneous/Cre-only) →
  `no-asbestos-exposure`.
- Asbestos + inflammation (e.g. Nlrp3, macrophage studies) where mesothelioma incidence is
  actually scored over time → include; where only acute inflammation is measured →
  `no-mesothelioma-outcome`.
