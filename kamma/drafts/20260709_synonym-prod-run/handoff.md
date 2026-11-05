# handoff.md — Synonym Audit v2: Follow-Up Threads

Source: `kamma/archive/20260709_synonym-rerun-pro/` (mechanism-validated thread)

## 1. Full Production `--fix-ai` Run (Primary)

Run the validated mechanism across all `ru_meaning_raw` rows with DeepSeek-V4-Pro.

- Backup checkpoint: run `db/backup_tsv/backup_dps.py` before any `--fix-ai` write.
- Full judge run: `uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw --ai --provider deepseek --model deepseek-v4-pro`
- Review the generated TSV (`<timestamp>_review.tsv`) sorted by max_ratio descending.
- Apply run: `uv run python3 kamma/translate/scripts/synonym_audit.py --field ru_meaning_raw --fix-ai --provider deepseek --model deepseek-v4-pro`
- Compare counts against the 362-entry / 646-pair baseline from `kamma/translate/improvments.md`.

## 2. Re-Audit `ru_meaning` and `ta_meaning`

The rewritten per-entry judging machinery supports any field. Run the same `--ai` → review → `--fix-ai` workflow on `ru_meaning` and/or `ta_meaning` when needed.

## 3. `batch_runner.py` Integration

Wrap `synonym_audit.py` calls into `batch_runner.py` for automated scheduling if the audit becomes part of the release pipeline.
