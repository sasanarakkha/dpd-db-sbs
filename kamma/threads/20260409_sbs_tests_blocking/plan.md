# Plan: Harden SBS Consistency Tests (Issue #20)

## Phase 1: Exit Code & Blocking

- [ ] Task 1.1: Add return-value and `sys.exit` to `run_sbs_consistency_tests()`
  - Count total errors across all tests.
  - `sys.exit(1)` if total > 0, else `sys.exit(0)`.
  - File: `db_tests/sbs_consistency_tests.py`

- [ ] Task 1.2: Update shell scripts to check exit code
  - `scripts/bash/update_decks.sh`: fail before running `anki_csv.py` if tests fail.
  - `scripts/cl_dps/dpd-anki`: fail before running updater if tests fail.

---

## Phase 2: Missing Validations

- [ ] Task 2.1: Add `check_extra_consistency()` — extra_example/source/sutta triplet
  - Mirror `check_vib_consistency` pattern.
  - Register in `run_sbs_consistency_tests()`.
  - File: `db_tests/sbs_consistency_tests.py`

- [ ] Task 2.2: Extend `check_discourses_source_prefix()` to validate full source value
  - After prefix check passes, validate full `discourses_source` against `list_of_discourses`.
  - File: `db_tests/sbs_consistency_tests.py`

---

## Phase 3: Type Hints & Lint

- [ ] Task 3.1: Replace `List`, `Tuple`, `Optional` with modern builtins across the file
  - `List[x]` → `list[x]`, `Tuple[x, y]` → `tuple[x, y]`, `Optional[x]` → `x | None`
  - File: `db_tests/sbs_consistency_tests.py`

- [ ] Task 3.2: Add/update unit tests for new checks (extra_example, full discourse source)
  - File: `tests/test_sbs_consistency.py`

- [ ] Task 3.3: Run `uv run ruff check --fix` and `uv run ruff format` to confirm clean
