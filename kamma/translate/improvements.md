# Improvements & Future Analysis

## 2026-07-06 Synonym Audit: ru_meaning_raw

Ran the old `synonym_audit.py --field ru_meaning_raw --fix --ai --fix-ai` (the `--fix-ai` flag has since been removed; AI trims now go through a reviewed TSV and `--apply-tsv`).

- **Fixed (483 rows):** exact duplicates (e.g. `"наступающий; наступающий"` → `"наступающий"`) via `--fix`, plus 280 AI-confirmed near-duplicate trims.
- **Not fixed — AI-judged distinct:** 646 pairs across 362 entries were flagged by the algorithm (ratio ≥ 0.85) but judged semantically distinct; they need human review to decide whether to keep both or merge.

The per-entry list of those 362 entries was dropped; regenerate it with `synonym_audit.py --ai`.
