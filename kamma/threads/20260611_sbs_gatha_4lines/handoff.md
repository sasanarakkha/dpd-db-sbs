# Handoff: SBS gāthā line normalization

## Current State

- Phase 1 is complete in the plan.
- The gāthā splitter now preserves existing `\n`, splits `", "` and internal `". "`, and merges short comma phrases instead of creating fragile one-word/short-phrase lines.
- The transfer helper was renamed to `scripts/change_in_db/sbs_dpd_example_transfers.py` and broadened to generate same-id / same-source / normalized-text matches from `DpdHeadword.example_1/2` into SBS examples.
- No DB writes have been run. All work so far is dry-run only.

## Files Touched

- `scripts/change_in_db/rearrange_sbs_gatha_lines.py`
- `scripts/change_in_db/sbs_dpd_example_transfers.py`
- `tests/test_rearrange_sbs_gatha_lines.py`
- `kamma/threads/20260611_sbs_gatha_4lines/spec.md`
- `kamma/threads/20260611_sbs_gatha_4lines/plan.md`

## What Was Learned

- The original flatten-first splitter was too aggressive. It joined existing lines and changed valid examples. That approach was abandoned.
- Trailing `", "` before an existing newline can create blank lines if not stripped first. That has been fixed.
- A simple “one-word line” warning is too noisy. Long single-word pādas like `niruttipadakovido` are valid; the useful warning surface is short comma phrases after the split/merge logic.
- The DPD transfer candidate preview was first too broad, then too narrow. The current helper now produces all same-id/same-source/normalized-text candidates, which is what the user asked for.

## Validation Run

All of these passed on the changed files:

1. `uv run ruff check --fix scripts/change_in_db/rearrange_sbs_gatha_lines.py scripts/change_in_db/sbs_dpd_example_transfers.py tests/test_rearrange_sbs_gatha_lines.py`
2. `uv run ruff format scripts/change_in_db/rearrange_sbs_gatha_lines.py scripts/change_in_db/sbs_dpd_example_transfers.py tests/test_rearrange_sbs_gatha_lines.py`
3. `uv run pyright scripts/change_in_db/rearrange_sbs_gatha_lines.py scripts/change_in_db/sbs_dpd_example_transfers.py tests/test_rearrange_sbs_gatha_lines.py`
4. `uv run --with pyrefly pyrefly check --min-severity warn scripts/change_in_db/rearrange_sbs_gatha_lines.py scripts/change_in_db/sbs_dpd_example_transfers.py tests/test_rearrange_sbs_gatha_lines.py`
5. `uv run pytest tests/test_rearrange_sbs_gatha_lines.py -v`

## Dry-Run Outputs

- `temp/sbs_gatha_review.tsv`
- `temp/sbs_gatha_concerns.tsv`
- `temp/sbs_dpd_example_transfers.tsv`

Latest dry-run counts:

- `sbs_gatha_review.tsv`: 447 rows plus header
- `sbs_gatha_concerns.tsv`: 0 rows plus header
- `sbs_dpd_example_transfers.tsv`: 1,880 transfer candidates

Simulation after applying all transfer candidates first, then running the gāthā splitter in memory:

- current changed fields: 1,612
- simulated changed fields after transfers: 1,308
- current review rows: 447
- simulated review rows after transfers: 447

That means the transfer list reduces heuristic changes, but it does not reduce the review TSV count yet.

## Top Remaining Suspicious Rows

The current top suspicious rows after simulated transfers are still prose-like or short-fragment cases, for example:

- `id=27328`, `extra_example`, `SNP4`
- `id=31979`, `extra_example`, `SNP4`
- `id=53764`, `extra_example`, `SN1.32`
- `id=57606`, `sbs_example_1`, `Sri Lanka`
- `id=30501`, `sbs_example_1`, `SNP8`
- `id=2600`, `class_example`, `SNP47`
- `id=24621`, `class_example`, `DHP153 (simpl)`
- `id=18083`, `extra_example`, `SNP38`
- `id=9719`, `class_example`, `DHP153 (simpl)`
- `id=6314`, `class_example`, `SNP16`

## Failed / Abandoned Approaches

- Flattening existing lines before splitting was abandoned because it joined valid line breaks and could damage already-correct examples.
- Filtering the DPD transfer helper to only current migration targets or only already-stable verse examples was abandoned because it was too narrow for the user’s request.
- Filtering the transfer helper too tightly to “safe” DPD verses was abandoned because the user explicitly wants all same-id/source/text matches for transfer consideration.

## Remaining Work

- Decide whether to add a manual override TSV for the remaining suspicious rows or proceed directly to the DB migration phase.
- If the next session continues the migration path, the likely next step is still Phase 2.1 `--apply`, but only after the user confirms the remaining suspicious set is acceptable.
- The exporter/display phases are still pending and untouched.

## Constraints For Next Session

- Keep DB writes off until the user explicitly approves `--apply`.
- Do not reintroduce line-joining in `split_gatha_lines`.
- Keep the transfer helper conservative about text normalization, but do not add extra source/format filters unless the user asks for them.
- Preserve the existing `temp/` outputs as dry-run artifacts until the next session decides whether to keep or regenerate them.

## Next Decision

The next session should decide one of these:

1. add a manual override TSV for the remaining suspicious cases, or
2. proceed to a DB dry-run/apply decision using the current transfer preview and suspicious list.
