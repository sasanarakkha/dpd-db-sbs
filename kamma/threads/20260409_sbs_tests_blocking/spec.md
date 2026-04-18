# Spec: Harden SBS Consistency Tests (Issue #20)

## Issue Reference
Local issue #20: "Tests for SBS examples" — https://github.com/sasanarakkha/dpd-db-sbs/issues/20

## Problem

`db_tests/sbs_consistency_tests.py` contains 13 SBS data-integrity checks wired into
`update_decks.sh` and `dpd-anki`, but they are **non-blocking** — errors are printed and the
pipeline continues. A corrupt row silently flows through to the Anki export.

Additional gaps remain:
- `extra_example`/`extra_source`/`extra_sutta` triplet has no consistency check.
- `discourses_source` is validated only by prefix (`sbs_category_list`, 9 entries), not against the full
  canonical `list_of_discourses` (75 exact values in `tools/sbs_table_functions.py`).
- Several SBS quality checks from `shared_data/sbs_csvs/dps_internal_tests.tsv` (rows 71–114)
  exist only in the GUI, not in the pipeline-blocking runner.

## Goals

1. **Block the pipeline** on failure (exit code 1 when any check has errors).
2. **Add `check_extra_consistency`** — triplet for `extra_example`/`extra_source`/`extra_sutta`.
3. **Extend source validation** — `check_discourses_source_full` validates the full
   `discourses_source` value against `list_of_discourses`; add a
   `# MARKER: add full-source validations below (issue #20)` comment for future expansion.
4. **Port TSV checks into the runner** (confirmed in scope):
   - **Rows 71–77:** Refine existing dhp/pat/vib/class/discourses triplet checks to allow sutta
     to be empty when source is one of `["MJG", "Sri Lanka", "Thai", "Trad"]`.
   - **Rows 78–84:** `check_example_capital_letters` — example fields must not contain `[A-Z]`.
   - **Rows 87–107:** `check_example_spacing` — three spacing patterns across 7 example fields
     (` ,` anywhere; ` ,$| , ` edge/floating; ` \.$| \. ` edge/floating).
   - **Rows 108–114:** `check_source_has_space` — source fields must not contain a space, exempt
     values containing `"PAT"` or `"Sri Lanka"`.
5. **Reorganize file** with four section banners (`# ==== TRIPLET CHECKS ====`, `# ==== FORMATTING ====`,
   `# ==== SOURCE VALIDATION ====`, `# ==== CROSS-REFERENCE ====`) and shared helpers
   (`_check_triplet`, `_check_fields_regex`) to keep growth manageable.
6. **Modernize type hints** — `List`/`Tuple`/`Optional` → `list`/`tuple`/`| None`.
7. **Update shell scripts** to abort on non-zero exit from the test runner.

## Out of Scope

- RU-crossover checks (TSV rows 85–86 — `ru_meaning` empty while `sbs_example` present).
  Deferred to a future `russian_consistency` thread.
- Full-source validation for `class_source`, `pat_source`, `dhp_source`, `sbs_source_1/2`,
  `vib_source` (no authoritative canonical list for all; marked with `# MARKER` for future work).
- Changes to `anki_csv.py` itself.
- CSV-level spot checks.

## Files Affected

| File | Change |
|---|---|
| `db_tests/sbs_consistency_tests.py` | Main: exit code, new checks, helpers, section banners, type hints |
| `tests/test_sbs_consistency.py` | New unit tests for all new + modified checks |
| `scripts/bash/update_decks.sh` | Abort before `anki_csv.py` if tests fail |
| `scripts/cl_dps/dpd-anki` | Abort before updater if tests fail |

Reference files (read-only):
- `tools/sbs_table_functions.py` — `list_of_discourses`, `sbs_category_list`
- `db/models.py` — `SBS` model columns
- `shared_data/sbs_csvs/dps_internal_tests.tsv` — source of ported checks (rows 71–114)

## Acceptance Criteria

- `uv run python db_tests/sbs_consistency_tests.py` exits `1` when errors exist, `0` when clean.
- `uv run pytest tests/test_sbs_consistency.py -v` — all tests pass.
- `uv run ruff check db_tests/sbs_consistency_tests.py tests/test_sbs_consistency.py` — zero errors.
- `update_decks.sh` aborts CSV export if tests fail.
- `dpd-anki` aborts Anki update if tests fail.
- File has four section banners and a `# MARKER: add full-source validations below (issue #20)` comment.
- `from typing import List, Tuple, Optional` removed; all signatures use modern builtins.
