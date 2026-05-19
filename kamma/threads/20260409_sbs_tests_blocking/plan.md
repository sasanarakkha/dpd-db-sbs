# Plan: Harden SBS Consistency Tests (Issue #20)

## Context

`db_tests/sbs_consistency_tests.py` contains 13 SBS data-integrity checks that are already wired into `scripts/bash/update_decks.sh` and `scripts/cl_dps/dpd-anki`, but they are **non-blocking** — errors are printed and the pipeline continues, so a corrupt row can silently flow into the Anki export.

This thread closes that gap. Scope:

1. Make the test runner return an exit code and abort the pipeline on failure.
2. Fill in validation gaps from the original spec:
   - `extra_example`/`extra_source`/`extra_sutta` triplet has no check.
   - `discourses_source` is validated only by prefix, not against the canonical `list_of_discourses` (75 entries).
3. Port the SBS example/source/sutta-related checks from `shared_data/sbs_csvs/dps_internal_tests.tsv` (currently GUI-only) into the Python runner so they also block the pipeline. Scope (confirmed with user):
   - **Rows 71–77:** example-but-no-sutta with `MJG|Sri Lanka|Thai|Trad` source exception (refine existing triplet checks).
   - **Rows 78–84:** example must not contain `[A-Z]` (stray ASCII capitals).
   - **Rows 87–107:** example spacing — ` ,` anywhere; ` ,$| , ` edge/floating; ` \.$| \. ` edge/floating.
   - **Rows 108–114:** source must not contain space, exempting substrings `"PAT"` and `"Sri Lanka"`.
4. Modernize type hints (`List`/`Tuple`/`Optional` → `list`/`tuple`/`| None`).
5. Keep the file as one script but reorganize with section banners and extract helpers so the additions don't bloat the file; add a future-extension marker.

Deferred (not this thread):
- RU crossover checks (TSV rows 85–86).
- Full-source validation for `class_source`, `pat_source`, `dhp_source`, `sbs_source_1/2`, `vib_source`. Left as a MARKER comment in the code.
- CSV-level spot checks.

---

## Files Affected

| File | Purpose |
|---|---|
| `db_tests/sbs_consistency_tests.py` | Main refactor + new checks + exit code |
| `tests/test_sbs_consistency.py` | Unit tests for new checks + triplet refinement |
| `scripts/bash/update_decks.sh` | Abort pipeline if tests fail |
| `scripts/cl_dps/dpd-anki` | Abort pipeline if tests fail |

Reference (read-only, used but not modified):
- `tools/sbs_table_functions.py` — `list_of_discourses` (line 86), `sbs_category_list` (line 107)
- `db/models.py` — `SBS` table (line 1655–1704)

---

## Phase 1: Pipeline Blocking

### Task 1.1: Make `run_sbs_consistency_tests()` return an exit code [x]
### Task 1.2: Update `scripts/bash/update_decks.sh` [x]
### Task 1.3: Update `scripts/cl_dps/dpd-anki` [x]

---

## Phase 2: Reorganize File Into Sections

### Task 2.1: Add section banners [x]
### Task 2.2: Function placement [x]

---

## Phase 3: Shared Helpers & Constants

### Task 3.1: Module-level constants [x]
### Task 3.2: `_check_triplet` helper [x]
### Task 3.3: `_check_fields_regex` helper [x]

---

## Phase 4: Refine Existing Triplet Checks (MJG/Sri Lanka/Thai/Trad sutta exception)

### Task 4.1: Replace four existing triplet functions with `_check_triplet` calls [x]
### Task 4.2: Add `check_extra_consistency` (NEW) [x]

---

## Phase 5: Formatting Checks (NEW)

### Task 5.1: `check_example_capital_letters` (TSV rows 78–84) [x]
### Task 5.2: `check_example_spacing` (TSV rows 87–107) [x]
### Task 5.3: `check_bold_tags` — keep strict behavior [x]

---

## Phase 6: Source Validation (NEW + extension)

### Task 6.1: Extend `check_discourses_source_prefix` → add `check_discourses_source_full` [x]
### Task 6.2: `check_source_has_space` (TSV rows 108–114) [x]

---

## Phase 7: Type Hints Modernization

### Task 7.1: Remove legacy typing imports [x]
### Task 7.2: Rewrite all signatures [x]
### Task 7.3: Register all checks in `run_sbs_consistency_tests()` [x]

---

## Phase 8: Unit Tests [x]

---

## Phase 9: Lint & Verification [x]

---

## Acceptance Criteria

- [x] `uv run python db_tests/sbs_consistency_tests.py` exits `1` when errors exist, `0` when clean.
- [x] `uv run pytest tests/test_sbs_consistency.py -v` passes — covers all new checks + MJG exception refinement.
- [x] `uv run ruff check db_tests/sbs_consistency_tests.py tests/test_sbs_consistency.py` — zero errors.
- [x] `update_decks.sh` aborts before `anki_csv.py` when tests fail (manual verification).
- [x] `dpd-anki` aborts before the updater when tests fail (manual verification).
- [x] `db_tests/sbs_consistency_tests.py` has four `# ==== ... ====` section banners and a `# MARKER: add full-source validations below (issue #20)` comment in SOURCE VALIDATION.
- [x] `from typing import List, Tuple, Optional` is removed; all signatures use modern builtins.
- [x] New checks registered in `run_sbs_consistency_tests()` and visible in the on-screen output of a full run.
