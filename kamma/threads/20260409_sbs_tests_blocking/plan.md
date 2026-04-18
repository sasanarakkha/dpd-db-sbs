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

### Task 1.1: Make `run_sbs_consistency_tests()` return an exit code

**File:** `db_tests/sbs_consistency_tests.py`

**Change:**
1. Add `import sys` at top.
2. Change signature: `def run_sbs_consistency_tests() -> int:`.
3. Count total errors across all `results_list` entries:
   ```python
   total_errors = sum(count for _, _, count, _ in results_list)
   ```
4. After the existing per-test print loop, add:
   ```python
   if total_errors > 0:
       pr.red(f"SBS consistency tests FAILED with {total_errors} total errors.")
       return 1
   pr.green("All SBS consistency tests passed.")
   return 0
   ```
5. Update `__main__` block:
   ```python
   if __name__ == "__main__":
       pr.tic()
       exit_code = run_sbs_consistency_tests()
       pr.toc()
       sys.exit(exit_code)
   ```

**Verification:** `uv run python db_tests/sbs_consistency_tests.py; echo "exit=$status"` (fish) — must print `exit=0` on clean DB, `exit=1` when any check has `count > 0`.

### Task 1.2: Update `scripts/bash/update_decks.sh`

**File:** `scripts/bash/update_decks.sh` lines 20–22.

**Before:**
```bash
uv run python scripts/change_in_db/class_relation.py
uv run python db_tests/sbs_consistency_tests.py
uv run python scripts/export/anki_csv.py
```

**After:**
```bash
uv run python scripts/change_in_db/class_relation.py
if ! uv run python db_tests/sbs_consistency_tests.py; then
    echo -e "\033[1;31m SBS consistency tests FAILED. Aborting before anki_csv.py. \033[0m"
    exit 1
fi
uv run python scripts/export/anki_csv.py
```

### Task 1.3: Update `scripts/cl_dps/dpd-anki`

**File:** `scripts/cl_dps/dpd-anki` line 16.

**Before:**
```bash
bash "${MASTER_SCRIPT}" "${LOG_BASE_NAME}" bash -c "cd '${PROJECT_ROOT}' && uv run python '${TEST_SCRIPT_PATH}'"
```

**After:**
```bash
if ! bash "${MASTER_SCRIPT}" "${LOG_BASE_NAME}" bash -c "cd '${PROJECT_ROOT}' && uv run python '${TEST_SCRIPT_PATH}'"; then
    echo -e "\033[1;31m SBS consistency tests FAILED. Aborting Anki update. \033[0m"
    exit 1
fi
```

**Pre-check:** Before committing, verify `run_and_log.sh` propagates the wrapped command's exit code — inspect `$HOME/.local/bin/run_and_log.sh`. If it swallows non-zero codes, the `if ! ...` guard becomes a no-op and must be rewritten to read the log/status file. Document finding in review.md regardless.

---

## Phase 2: Reorganize File Into Sections

### Task 2.1: Add section banners

**File:** `db_tests/sbs_consistency_tests.py`

Add five banner comments in this order (place functions between them):

```python
# ============================================================
# SHARED HELPERS & CONSTANTS
# ============================================================

# ============================================================
# TRIPLET CHECKS (example/source/sutta must be all-or-none)
# ============================================================

# ============================================================
# FORMATTING (bold tags, capitals, spacing)
# ============================================================

# ============================================================
# SOURCE VALIDATION
# ============================================================
# MARKER: add full-source validations below (issue #20)
# - dhp_source  → pattern DHP\d+ (1..423)
# - pat_source  → pattern "VIN PAT (PA|SA|AN|NP|PC|PD|SE|AS) \d+" or "PAT"
# - class_source → shared_data/sbs_csvs/class_index.csv
# When adding, load the canonical list once, compare full value, and
# register the new check in run_sbs_consistency_tests().

# ============================================================
# CROSS-REFERENCE (inter-table / inter-row consistency)
# ============================================================
```

### Task 2.2: Function placement

Group existing and new functions under the banners:

| Banner | Functions |
|---|---|
| SHARED HELPERS | `regex_results` (existing), `EXAMPLE_FIELDS`, `SOURCE_FIELDS`, `SUTTA_EXCEPTION_SOURCES`, `_check_triplet`, `_check_fields_regex` |
| TRIPLET | `check_dhp_triplet_consistency`, `check_vib_consistency`, `check_class_consistency`, `check_discourses_consistency`, `check_extra_consistency` (NEW), `check_sbs_example_consistency`, `check_pat_consistency` |
| FORMATTING | `check_bold_tags`, `check_example_capital_letters` (NEW), `check_example_spacing` (NEW) |
| SOURCE VALIDATION | `check_discourses_source_prefix`, `check_discourses_source_full` (NEW), `check_source_has_space` (NEW) |
| CROSS-REFERENCE | `check_sbs_index_mapping`, `check_class_translation_uniqueness`, `check_dhp_source_consistency`, `check_class_anki_consistency` |

---

## Phase 3: Shared Helpers & Constants

### Task 3.1: Module-level constants

Place under `SHARED HELPERS` banner:

```python
EXAMPLE_FIELDS: list[str] = [
    "sbs_example_1",
    "sbs_example_2",
    "dhp_example",
    "pat_example",
    "vib_example",
    "class_example",
    "discourses_example",
]

SOURCE_FIELDS: list[str] = [
    "sbs_source_1",
    "sbs_source_2",
    "dhp_source",
    "pat_source",
    "vib_source",
    "class_source",
    "discourses_source",
]

# Source values where sutta is allowed to be empty (from TSV rows 71-77).
SUTTA_EXCEPTION_SOURCES: list[str] = ["MJG", "Sri Lanka", "Thai", "Trad"]

# Source substrings where a space is allowed in the source value (TSV rows 108-114).
SOURCE_SPACE_EXEMPT_SUBSTRINGS: list[str] = ["PAT", "Sri Lanka"]
```

### Task 3.2: `_check_triplet` helper

```python
def _check_triplet(
    db_session: Session,
    *,
    name: str,
    example_field: str,
    source_field: str,
    sutta_field: str,
    solution: str,
    allow_sutta_exception: bool = True,
) -> tuple[str, str | None, int, str]:
    """Generic example/source/sutta triplet check.

    - If all three are empty → OK.
    - If any is present → example AND source must be present.
    - If allow_sutta_exception: sutta may be empty when source is in
      SUTTA_EXCEPTION_SOURCES (matches TSV rows 71-77 behavior).
    """
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        example = getattr(sbs, example_field) or ""
        source = getattr(sbs, source_field) or ""
        sutta = getattr(sbs, sutta_field) or ""
        if not (example or source or sutta):
            continue
        if not example or not source:
            results.append(str(sbs.id))
            continue
        if sutta:
            continue
        if allow_sutta_exception and source in SUTTA_EXCEPTION_SOURCES:
            continue
        results.append(str(sbs.id))
    return (name, regex_results(results), len(results), solution)
```

### Task 3.3: `_check_fields_regex` helper

```python
def _check_fields_regex(
    db_session: Session,
    *,
    name_prefix: str,
    fields: list[str],
    pattern: str,
    solution: str,
) -> list[tuple[str, str | None, int, str]]:
    """Run one regex across many fields; emit one result tuple per field."""
    compiled = re.compile(pattern)
    all_results: list[tuple[str, str | None, int, str]] = []
    sbs_data = db_session.query(SBS).all()
    for field in fields:
        results: list[str] = []
        for sbs in sbs_data:
            val = getattr(sbs, field) or ""
            if val and compiled.search(val):
                results.append(str(sbs.id))
        all_results.append(
            (f"{name_prefix}_{field}", regex_results(results), len(results), solution)
        )
    return all_results
```

---

## Phase 4: Refine Existing Triplet Checks (MJG/Sri Lanka/Thai/Trad sutta exception)

**Covers TSV rows 73–77.** Rows 71–72 (`sbs_example_1/2`) already handled by `check_sbs_example_consistency`.

### Task 4.1: Replace four existing triplet functions with `_check_triplet` calls

Replace `check_dhp_triplet_consistency`, `check_vib_consistency`, `check_class_consistency`, `check_discourses_consistency` implementations. Behavior change: sutta may now be empty when source is in `SUTTA_EXCEPTION_SOURCES`.

**`check_dhp_triplet_consistency`:**
```python
def check_dhp_triplet_consistency(db_session: Session) -> tuple[str, str | None, int, str]:
    """If any of dhp_example, dhp_source, or dhp_sutta is present, example+source must be present.
    Sutta may be empty when source is in SUTTA_EXCEPTION_SOURCES."""
    return _check_triplet(
        db_session,
        name="dhp_triplet_consistency",
        example_field="dhp_example",
        source_field="dhp_source",
        sutta_field="dhp_sutta",
        solution="ensure dhp_example, dhp_source, and dhp_sutta are all present",
    )
```

**`check_vib_consistency`:** identical pattern, fields `vib_*`.

**`check_discourses_consistency`:** identical pattern, fields `discourses_*`.

**`check_class_consistency`:** NOTE the existing `upāsak`/`thero`/`sīho` exception is tied to `class_anki == 2`. Keep that inline (the helper only handles source-based sutta exception). Implement as:

```python
def check_class_consistency(db_session: Session) -> tuple[str, str | None, int, str]:
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        example = sbs.class_example or ""
        source = sbs.class_source or ""
        sutta = sbs.class_sutta or ""
        if not (example or source or sutta):
            continue
        if not example or not source:
            results.append(str(sbs.id))
            continue
        if sutta:
            continue
        # Existing class_anki exception
        if sbs.class_anki == 2 and any(w in example for w in ["upāsak", "thero", "sīho"]):
            continue
        # New: MJG/Sri Lanka/Thai/Trad sutta exception
        if source in SUTTA_EXCEPTION_SOURCES:
            continue
        results.append(str(sbs.id))
    return (
        "class_consistency",
        regex_results(results),
        len(results),
        "ensure class_example, class_source, and class_sutta are all present",
    )
```

### Task 4.2: Add `check_extra_consistency` (NEW)

```python
def check_extra_consistency(db_session: Session) -> tuple[str, str | None, int, str]:
    """Triplet check for extra_example/extra_source/extra_sutta."""
    return _check_triplet(
        db_session,
        name="extra_consistency",
        example_field="extra_example",
        source_field="extra_source",
        sutta_field="extra_sutta",
        solution="ensure extra_example, extra_source, and extra_sutta are all present",
    )
```

Register in `run_sbs_consistency_tests()` under TRIPLET group.

---

## Phase 5: Formatting Checks (NEW)

### Task 5.1: `check_example_capital_letters` (TSV rows 78–84)

```python
def check_example_capital_letters(
    db_session: Session,
) -> list[tuple[str, str | None, int, str]]:
    """No example field should contain stray ASCII capital letters (Pali is lowercase)."""
    return _check_fields_regex(
        db_session,
        name_prefix="capital_letter",
        fields=EXAMPLE_FIELDS,
        pattern=r"[A-Z]",
        solution="remove stray ASCII capital letters from example",
    )
```

### Task 5.2: `check_example_spacing` (TSV rows 87–107)

Three independent regex sweeps across all 7 example fields:

```python
def check_example_spacing(
    db_session: Session,
) -> list[tuple[str, str | None, int, str]]:
    """Three spacing rules: TSV rows 87-107."""
    all_results: list[tuple[str, str | None, int, str]] = []
    all_results.extend(
        _check_fields_regex(
            db_session,
            name_prefix="space_comma",
            fields=EXAMPLE_FIELDS,
            pattern=r" ,",
            solution="remove space before comma",
        )
    )
    all_results.extend(
        _check_fields_regex(
            db_session,
            name_prefix="space_comma_edge",
            fields=EXAMPLE_FIELDS,
            pattern=r" ,$| , ",
            solution="remove trailing or floating ' ,'",
        )
    )
    all_results.extend(
        _check_fields_regex(
            db_session,
            name_prefix="space_fullstop_edge",
            fields=EXAMPLE_FIELDS,
            pattern=r" \.$| \. ",
            solution="remove trailing or floating ' .'",
        )
    )
    return all_results
```

Note: `space_comma` is the superset sweep (catches ` ,bar`); `space_comma_edge` is a narrower sweep. Both are ported verbatim from TSV to preserve distinct error messages.

### Task 5.3: `check_bold_tags` — keep strict behavior

No change to logic. Only modernize type hints (Phase 7) and move under the FORMATTING banner.

---

## Phase 6: Source Validation (NEW + extension)

### Task 6.1: Extend `check_discourses_source_prefix` → add `check_discourses_source_full`

Keep existing prefix check as-is. Add a new function that validates the **full** `discourses_source` string against `list_of_discourses` (75 entries).

```python
def check_discourses_source_full(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """discourses_source must match an entry in list_of_discourses exactly."""
    from tools.sbs_table_functions import list_of_discourses
    valid = set(list_of_discourses)
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        if sbs.discourses_source and sbs.discourses_source not in valid:
            results.append(str(sbs.id))
    return (
        "discourses_source_full",
        regex_results(results),
        len(results),
        "ensure discourses_source matches an entry in tools/sbs_table_functions.py:list_of_discourses",
    )
```

Register in `run_sbs_consistency_tests()` **after** `check_discourses_source_prefix` so prefix errors surface first.

### Task 6.2: `check_source_has_space` (TSV rows 108–114)

```python
def check_source_has_space(
    db_session: Session,
) -> list[tuple[str, str | None, int, str]]:
    """No source field should contain a space, except values containing 'PAT' or 'Sri Lanka'."""
    all_results: list[tuple[str, str | None, int, str]] = []
    sbs_data = db_session.query(SBS).all()
    for field in SOURCE_FIELDS:
        results: list[str] = []
        for sbs in sbs_data:
            val = getattr(sbs, field) or ""
            if not val or " " not in val:
                continue
            if any(exempt in val for exempt in SOURCE_SPACE_EXEMPT_SUBSTRINGS):
                continue
            results.append(str(sbs.id))
        all_results.append(
            (
                f"source_has_space_{field}",
                regex_results(results),
                len(results),
                f"remove space from {field}",
            )
        )
    return all_results
```

---

## Phase 7: Type Hints Modernization

**Rule (from CLAUDE.md):** `List` → `list`, `Tuple` → `tuple`, `Optional[X]` → `X | None`.

### Task 7.1: Remove legacy typing imports

**File:** `db_tests/sbs_consistency_tests.py` line 6.

**Before:** `from typing import List, Tuple, Optional`
**After:** (delete line)

### Task 7.2: Rewrite all signatures

Every occurrence of `Tuple[str, Optional[str], int, str]` → `tuple[str, str | None, int, str]`. Every `List[...]` → `list[...]`. Every `Optional[X]` → `X | None`.

Affected signatures (count ≈ 15): all existing `check_*` return types, plus `regex_results`, plus any new helpers.

### Task 7.3: Register all checks in `run_sbs_consistency_tests()`

Final call order (preserve existing grouping + add new):

```python
def run_sbs_consistency_tests() -> int:
    print("[bright_yellow]run sbs consistency tests")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    results_list: list[tuple[str, str | None, int, str]] = []

    # Triplet
    results_list.append(check_pat_consistency(db_session))
    results_list.append(check_dhp_source_consistency(db_session))
    results_list.append(check_dhp_triplet_consistency(db_session))
    results_list.append(check_vib_consistency(db_session))
    results_list.append(check_class_consistency(db_session))
    results_list.append(check_discourses_consistency(db_session))
    results_list.append(check_extra_consistency(db_session))           # NEW
    results_list.append(check_sbs_example_consistency(db_session))
    results_list.append(check_class_anki_consistency(db_session))

    # Source validation
    results_list.append(check_discourses_source_prefix(db_session))
    results_list.append(check_discourses_source_full(db_session))       # NEW
    results_list.extend(check_source_has_space(db_session))             # NEW

    # Formatting
    results_list.extend(check_bold_tags(db_session))
    results_list.extend(check_example_capital_letters(db_session))     # NEW
    results_list.extend(check_example_spacing(db_session))              # NEW

    # Cross-reference
    results_list.append(check_sbs_index_mapping(db_session))
    results_list.append(check_class_translation_uniqueness(db_session))

    total_errors = 0
    for name, results, count, solution in results_list:
        print(f"[green]{name.replace('_', ' ')} [{count}]")
        if count > 0:
            total_errors += count
            print(f"solution: {solution}")
            if results:
                print(results)
        print()

    if total_errors > 0:
        pr.red(f"SBS consistency tests FAILED with {total_errors} total errors.")
        return 1
    pr.green("All SBS consistency tests passed.")
    return 0
```

---

## Phase 8: Unit Tests

**File:** `tests/test_sbs_consistency.py`

### Task 8.1: Update `test_triplet_consistency_logic` for MJG/Sri Lanka/Thai/Trad exception

Add cases to the existing test:
- vib row: `source="MJG", sutta=""` with example present → **NOT** flagged (new behavior)
- discourses row: `source="Sri Lanka", sutta=""` with example present → **NOT** flagged
- dhp row: `source="Thai", sutta=""` with example present → **NOT** flagged
- class row: `source="Trad", sutta=""` with example present → **NOT** flagged
- class row: `source="OTHER", sutta=""` with example present → **flagged**

### Task 8.2: `test_extra_consistency_logic` (NEW)

Mirror `test_dhp_triplet_consistency_logic`. Cases:
1. All three populated → OK.
2. `extra_example="ex", extra_source="so", extra_sutta=""` → flagged.
3. `extra_source="MJG", extra_example="ex", extra_sutta=""` → OK (exception).
4. All three empty → OK.

### Task 8.3: `test_discourses_source_full_logic` (NEW)

Mock data:
1. `discourses_source="SN12.1"` → OK (in list).
2. `discourses_source="SN12.99"` → flagged (prefix OK but full value not in list).
3. `discourses_source="MN107"` → OK.
4. `discourses_source=""` → OK (skipped).

### Task 8.4: `test_example_capital_letters_logic` (NEW)

Cases per field:
1. `dhp_example="pure pali text"` → OK.
2. `dhp_example="Text with Capital"` → flagged (matches in 1 field).
3. `dhp_example="<b>...</b>"` → flagged (capital B). *This is expected per TSV behavior.*
4. Verify result tuple names have `capital_letter_dhp_example` etc.

> **Note on HTML tags:** `<b>`/`</b>` are lowercase so they pass. But HTML entities like `&Auml;` or capitalized Unicode wouldn't. Document expected behavior in the test; current regex is ASCII `[A-Z]` only.

### Task 8.5: `test_example_spacing_logic` (NEW)

Cases per pattern:
1. `sbs_example_1="foo ,bar"` → flagged by `space_comma` but **not** `space_comma_edge`.
2. `sbs_example_1="foo ."` (end) → flagged by `space_fullstop_edge`.
3. `sbs_example_1="foo . bar"` → flagged by `space_fullstop_edge`.
4. `sbs_example_1="foo, bar"` → OK (no space before comma).
5. `sbs_example_1="foo."` → OK.

### Task 8.6: `test_source_has_space_logic` (NEW)

Cases:
1. `sbs_source_1="DN 33"` → flagged.
2. `pat_source="VIN PAT PA 1"` → OK (contains `PAT`).
3. `sbs_source_1="Sri Lanka monks"` → OK (contains `Sri Lanka`).
4. `dhp_source="DHP100"` → OK (no space).
5. `discourses_source="SN 12.1"` → flagged.

### Task 8.7: `test_run_returns_exit_code` (NEW)

Skip if running against in-memory DB only is hard. Minimum acceptance: a smoke test that calls `run_sbs_consistency_tests()` on an empty in-memory DB and asserts `== 0`.

If fully coupling requires `ProjectPaths`, use `unittest.mock.patch` to stub `get_db_session` to return the fixture session.

---

## Phase 9: Lint & Verification

### Task 9.1: Lint

```bash
uv run ruff check --fix db_tests/sbs_consistency_tests.py tests/test_sbs_consistency.py
uv run ruff format db_tests/sbs_consistency_tests.py tests/test_sbs_consistency.py
```

### Task 9.2: Run targeted tests (NOT full suite — per memory rule)

```bash
uv run pytest tests/test_sbs_consistency.py -v
```

### Task 9.3: Manual end-to-end

1. Run against live DB:
   ```fish
   uv run python db_tests/sbs_consistency_tests.py
   echo "exit=$status"
   ```
   Record baseline counts and exit code.

2. Inject a known bad row (e.g., set `sbs.dhp_example` on one row where triplet is incomplete). Re-run. Expect non-zero exit and that row's ID in regex output.

3. Revert the test row.

4. Simulate shell wrapper abort. Inject the bad row, run the wrapper's test step:
   ```fish
   bash -c "uv run python db_tests/sbs_consistency_tests.py && echo would-continue || echo would-abort"
   ```
   Expect `would-abort`. Revert the bad row.

### Task 9.4: Verify run_and_log.sh behavior

Inspect `$HOME/.local/bin/run_and_log.sh`. Confirm that the exit code of the wrapped `bash -c ...` propagates. If not, record finding in `review.md` and either:
- fix the wrapper, or
- run the test directly (not via wrapper) inside `dpd-anki`.

---

## Acceptance Criteria

- [ ] `uv run python db_tests/sbs_consistency_tests.py` exits `1` when errors exist, `0` when clean.
- [ ] `uv run pytest tests/test_sbs_consistency.py -v` passes — covers all new checks + MJG exception refinement.
- [ ] `uv run ruff check db_tests/sbs_consistency_tests.py tests/test_sbs_consistency.py` — zero errors.
- [ ] `update_decks.sh` aborts before `anki_csv.py` when tests fail (manual verification).
- [ ] `dpd-anki` aborts before the updater when tests fail (manual verification).
- [ ] `db_tests/sbs_consistency_tests.py` has four `# ==== ... ====` section banners and a `# MARKER: add full-source validations below (issue #20)` comment in SOURCE VALIDATION.
- [ ] `from typing import List, Tuple, Optional` is removed; all signatures use modern builtins.
- [ ] New checks registered in `run_sbs_consistency_tests()` and visible in the on-screen output of a full run.

---

## Implementation Order (for `/kamma:2-do`)

1. Phase 1 (exit code + shell guards) — quickest unblock.
2. Phase 2 (section banners, empty) — reserve placement before touching bodies.
3. Phase 3 (shared helpers & constants).
4. Phase 4 (triplet refinement + `check_extra_consistency`).
5. Phase 5 (formatting NEW).
6. Phase 6 (source validation NEW).
7. Phase 7 (type hints sweep across the whole file).
8. Phase 8 (unit tests).
9. Phase 9 (lint + manual verify).

Each phase: Red (test written/updated) → Green → commit-ready diff preview. One commit at the end covering all phases (per local rule: one commit per feature/thread, not per task).
