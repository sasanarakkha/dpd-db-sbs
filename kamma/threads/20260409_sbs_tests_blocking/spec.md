# Spec: Harden SBS Consistency Tests (Issue #20)

## Issue Reference
Local issue #20: "Tests for SBS examples" — https://github.com/sasanarakkha/dpd-db-sbs/issues/20

## Problem

12 SBS consistency tests exist in `db_tests/sbs_consistency_tests.py` and are already
wired into the `update_decks.sh` and `dpd-anki` workflows. However, they are
**non-blocking** — errors are printed but the pipeline always continues. A data error
will silently pass through to the Anki export.

Additionally, a few validation gaps remain from the original spec:
- `extra_example`/`extra_source`/`extra_sutta` triplet has no consistency check.
- `discourses_source` is only validated by prefix, not against the full canonical list.

## Goals

1. Make the tests **block the pipeline** on failure (exit code 1 when errors found).
2. Add the missing `extra_example` triplet test.
3. Validate full `discourses_source` values against `list_of_discourses`.
4. Modernize type hints (`List`/`Tuple`/`Optional` → builtins).
5. Update shell scripts to respect the exit code.

## Out of Scope

- CSV-level spot checks (deferred to a future thread).
- Changes to `anki_csv.py` itself.

## Files Affected

- `db_tests/sbs_consistency_tests.py` — main test module
- `tests/test_sbs_consistency.py` — unit test wrapper
- `scripts/bash/update_decks.sh` — pipeline integration
- `scripts/cl_dps/dpd-anki` — pipeline integration

## Acceptance Criteria

- `uv run python db_tests/sbs_consistency_tests.py` exits 1 when errors exist, 0 when clean.
- `uv run pytest tests/test_sbs_consistency.py -v` — all tests pass.
- `uv run ruff check db_tests/sbs_consistency_tests.py` — no lint errors.
- `update_decks.sh` aborts CSV export if tests fail.
- `dpd-anki` aborts Anki update if tests fail.
