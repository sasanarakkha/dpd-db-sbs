# plan.md — Vibhanga Rule Workflow Streamlining

## Context for executing agent
- Project root: `/Users/deva/Documents/dpd-db`
- Run all commands from project root with `uv run`
- Spec: `kamma/threads/20260412_vib_rule_workflow/spec.md` — read it first
- Key files to read before starting:
  - `tools/cst_sc_text_sets.py` lines 86–375 — upstream `make_cst_text_list` + shadow `make_cst_text_list_from_file`
  - `scripts/export/list_of_words_from_txt.py` — word extraction script (no `__main__` guard yet)
  - `scripts/change_in_db/copy_examples.py` — copy-examples script (no `__main__` guard yet)
  - `tools/paths_dps.py:166` — `dpspth.text_to_add_path = Path("temp/text.txt")`
  - `misc/pat/pc60.txt` — example PAT file to understand format
- Style rules (mandatory):
  - All `.py` files start with a one-sentence module docstring
  - All `.sh` files start with a one-sentence comment after `#!/bin/bash`
  - Modern type hints: `dict[str, str]`, `list[str]`, `str | None`, NOT `Dict`, `Optional`
  - `Path` from pathlib for all file paths
  - `from tools.printer import printer as pr` for terminal output
  - `pr.green("task")` → `pr.yes("ok")` on success, `pr.no(...)` on failure
  - No inline Python scripting (`python -c "..."` is forbidden)
- After every code change run:
  `uv run ruff check --fix <file> && uv run ruff format <file>`

---

## Phase 1: Bug Investigation and Fix

### Task 1.1 — Read and compare the two hyphenation functions
`[x]`
- Read `tools/cst_sc_text_sets.py` lines 86–156: `make_cst_text_list` (upstream)
- Read `tools/cst_sc_text_sets.py` lines 318–375: `make_cst_text_list_from_file` (shadow)
- List every structural difference between the two functions
- The only *intentional* difference is the localized filter:
  `make_cst_text_list_from_file` calls `dps_make_no_field_inflections_set` (checks
  `vib_example`/`pat_example` fields) instead of using the full inflections set
- Note the suspected bug: `for index, word in enumerate(words_list)` loop that inserts
  items into `words_list` mid-iteration — confirm empirically via a failing test

### Task 1.2 — Write a failing test (RED phase)
`[x]`
- Create `tests/test_vib_rule_workflow.py`
- File must start with:
  ```python
  """Tests for the Vibhanga rule workflow: word extraction and -pi/-ca clitic handling."""
  ```
- Write `test_clitics_not_skipped_from_file()`:
  - Use `tmp_path` pytest fixture to create a temp text file containing:
    ```
    saṃgho-pi dhammo-ca bhikkhu-pi nāgo
    ```
  - Monkeypatch `dpspth.text_to_add_path` on a `DPSPaths` instance to point to that file
  - Call `make_cst_text_list_from_file(dpspth)` (import from `tools.cst_sc_text_sets`)
  - Assert all compound forms without hyphens are present in the returned list:
    `"saṃghopi"`, `"dhammoca"`, `"bhikkhupī"` — NOTE: first check the actual output to
    see exactly what compound forms the function produces, then assert on those exact strings
  - Run: `uv run pytest tests/test_vib_rule_workflow.py::test_clitics_not_skipped_from_file -v`
  - **MUST fail (red). If it passes, the bug is not reproducible — document this and
    write a different test that demonstrates the actual skipping behavior, or skip the
    fix task and document "no fix needed".**

### Task 1.3 — Fix the bug (GREEN phase)
`[x]`
- Based on Task 1.1 comparison, apply the minimal patch to `make_cst_text_list_from_file`
  that makes the test pass while:
  1. Keeping the localized filter (`dps_make_no_field_inflections_set` call) intact
  2. Matching the upstream function's structure as closely as possible
  3. Not changing the function signature or return type
- If the fix involves rewriting the hyphenation loop to avoid list mutation during
  iteration, a safe approach is to build a new list instead of inserting in-place:
  collect hyphenated expansions separately and extend after iteration
- Run: `uv run pytest tests/test_vib_rule_workflow.py::test_clitics_not_skipped_from_file -v`
- Must pass (green)
- Run: `uv run ruff check --fix tools/cst_sc_text_sets.py && uv run ruff format tools/cst_sc_text_sets.py`

### Task 1.4 — Verify no regressions
`[x]`
- Run: `uv run pytest tests/test_vib_rule_workflow.py -v`
- All tests must pass before proceeding

### Phase 1 Completion Verification
`[x]`
- Announce: "Phase 1 complete — bug fix verified"
- Confirm `tests/test_vib_rule_workflow.py` exists and the clitic test passes
- Confirm `uv run pytest tests/test_vib_rule_workflow.py -v` is fully green
- Ask user: "Does this meet your expectations? Please confirm with yes or provide feedback."
- **PAUSE and await user response before proceeding to Phase 2**

---

## Phase 2: Importability Refactor

Both scripts below execute code at module level (no `__main__` guard). Importing them
in `vib_rule_workflow.py` would trigger unintended DB operations. Fix this first.

### Task 2.1 — Add `__main__` guard to `copy_examples.py`
`[x]`
- Read `scripts/change_in_db/copy_examples.py` fully
- Lines 148–154 run at module level: set `source_value`, call `update_column_for_some_criteria`
- Wrap lines 148–154 in `if __name__ == "__main__":` block
- Verify the script still works standalone:
  Write `temp/test_copy_examples_main.py` containing just `import scripts.change_in_db.copy_examples`,
  run `uv run python temp/test_copy_examples_main.py`, confirm no DB call fires, delete the file
- Run: `uv run ruff check --fix scripts/change_in_db/copy_examples.py && uv run ruff format scripts/change_in_db/copy_examples.py`

### Task 2.2 — Add `__main__` guard to `list_of_words_from_txt.py`
`[x]`
- Read `scripts/export/list_of_words_from_txt.py` fully
- Line 146–147: module-level call `words_to_add_list = dps_make_words_to_add_list_from_text_no_field(...)`
- Wrap in `if __name__ == "__main__":` block
- Write `temp/test_list_import.py` with `import scripts.export.list_of_words_from_txt`,
  run it, confirm no execution fires, delete the file
- Run: `uv run ruff check --fix scripts/export/list_of_words_from_txt.py && uv run ruff format scripts/export/list_of_words_from_txt.py`

### Task 2.3 — Add `dry_run` parameter to `update_column_for_some_criteria`
`[x]`
- Read `scripts/change_in_db/copy_examples.py` (already done in 2.1)
- Add `dry_run: bool = False` to the function signature (line 23):
  ```python
  def update_column_for_some_criteria(
      source_value: str,
      column_to_update: str,
      value_to_update: str,
      modifier_column_to_copy: str,
      dry_run: bool = False,
  ) -> None:
  ```
- Locate `db_session.commit()` (line ~144) and wrap:
  ```python
  if not dry_run:
      db_session.commit()
  else:
      console.print("[bold yellow]DRY RUN — no changes written to database[/bold yellow]")
  ```
- Add test `test_dry_run_does_not_commit()` to `tests/test_vib_rule_workflow.py`:
  - Mock `db_session.commit` using `unittest.mock.patch`
  - Call `update_column_for_some_criteria("VIN2.5.6.10", "", "vib", "vib", dry_run=True)`
    with a mocked session
  - Assert `commit` was NOT called
- Run: `uv run pytest tests/test_vib_rule_workflow.py::test_dry_run_does_not_commit -v`
- Must pass
- Run: `uv run ruff check --fix scripts/change_in_db/copy_examples.py && uv run ruff format scripts/change_in_db/copy_examples.py`

---

## Phase 3: Unified Workflow Script

### Task 3.1 — Create `scripts/rus_exporter/vib_rule_workflow.py`
`[x]`
- File must start with:
  ```python
  """Run the end-to-end Vibhanga rule word-filling workflow: paste text, extract unrecognized words, pause for GUI entry, preview DB changes, then commit."""
  ```
- Imports:
  ```python
  import json
  import re
  import sys
  from pathlib import Path

  from db.db_helpers import get_db_session
  from scripts.change_in_db.copy_examples import update_column_for_some_criteria
  from scripts.export.list_of_words_from_txt import dps_make_words_to_add_list_from_text_no_field
  from tools.paths import ProjectPaths
  from tools.paths_dps import DPSPaths
  from tools.printer import printer as pr
  ```
- State file path constant: `VIB_PROGRESS_PATH = Path("misc/pat/vib_progress.json")`

- **`load_progress() -> dict`**
  - If `VIB_PROGRESS_PATH.exists()`: return `json.loads(VIB_PROGRESS_PATH.read_text())`
  - Else: return `{}`

- **`save_progress(source: str, pat_file: str) -> None`**
  - `VIB_PROGRESS_PATH.write_text(json.dumps({"last_source": source, "last_pat_file": pat_file}, ensure_ascii=False, indent=2))`

- **`suggest_next_pat_file(last_pat: str) -> str`**
  - Parse with `re.search(r"([a-z]+)(\d+)\.txt$", last_pat)`
  - If match: return `f"misc/pat/{match.group(1)}{int(match.group(2)) + 1}.txt"`
  - Else: return `""`

- **`strip_variant_readings(text: str) -> str`**
  - `return re.sub(r"\{[^}]+\}", "", text).strip()`

- **`accept_pasted_text() -> str`**
  - `pr.green("Paste the rule text below. Press Ctrl-D (EOF) when done:")`
  - `return sys.stdin.read()`

- **`run_rule(source: str, pat_file: str, pth: ProjectPaths, dpspth: DPSPaths, db_session) -> bool`**
  Returns `True` to continue loop, `False` to exit.

  Step 1 — Get text:
  - If `Path(pat_file).exists()`:
    - `pr.green(f"Reading existing file: {pat_file}")`
    - `text = Path(pat_file).read_text()`
  - Else:
    - `text = accept_pasted_text()`

  Step 2 — Clean:
  - `text = strip_variant_readings(text)`

  Step 3 — Save:
  - `Path(pat_file).parent.mkdir(parents=True, exist_ok=True)`
  - `Path(pat_file).write_text(text)`
  - `Path(dpspth.text_to_add_path).write_text(text)`
  - `pr.yes(f"Text saved to {pat_file} and {dpspth.text_to_add_path}")`

  Step 3b — First copy_examples run (pre-populate existing words):
  - `update_column_for_some_criteria(source, "", "vib", "vib", dry_run=False)`
  - This mirrors step 1 of the original 7-step workflow. Fills `vib_example`/`pat_example`
    for words already in the DB under this source, so they won't appear as false positives
    in word extraction.

  Step 4 — Extract words (now without false positives):
  - `words = dps_make_words_to_add_list_from_text_no_field(pth, dpspth, db_session, ["vib_example", "pat_example"])`
  - `pr.green(f"Found {len(words)} unrecognized words:")`
  - Print each word on its own line
  - `pr.green("Backup TSV saved to temp/text_vib_example_pat_example.tsv")`

  Step 5 — GUI pause:
  - `pr.green("Add the above words in gui2/main.py → Pass2Add tab.")`
  - `choice = input("Press Enter when done (or type 'q' to quit): ").strip().lower()`
  - If `choice == "q"`: `save_progress(source, pat_file)` then `return False`

  Step 6 — Dry-run preview:
  - `pr.green(f"Previewing copy_examples for {source} (DRY RUN)...")`
  - `update_column_for_some_criteria(source, "", "vib", "vib", dry_run=True)`
  - `choice = input("Apply these changes to the database? [y/N]: ").strip().lower()`
  - If `choice == "y"`:
    - `pr.green("Applying changes...")`
    - `update_column_for_some_criteria(source, "", "vib", "vib", dry_run=False)`
  - Else:
    - `pr.warning("Database changes skipped.")`

  Step 7 — Save progress:
  - `save_progress(source, pat_file)`
  - `pr.yes(f"Rule {source} done.")`

  Step 8 — Continue prompt:
  - `next_pat = suggest_next_pat_file(pat_file)`
  - `pr.green(f"Suggested next PAT file: {next_pat}")`
  - `choice = input("Continue to next rule? [Enter] or quit [q]: ").strip().lower()`
  - If `choice == "q"`: `return False`
  - Else: `return True`

- **`main() -> None`**
  ```python
  pth = ProjectPaths()
  dpspth = DPSPaths()
  db_session = get_db_session(pth.dpd_db_path)
  progress = load_progress()

  while True:
      if progress.get("last_source"):
          pr.green(f"Last rule: {progress['last_source']} ({progress['last_pat_file']})")
          next_pat = suggest_next_pat_file(progress["last_pat_file"])
          source = input(f"Source for next rule (suggested next PAT: {next_pat}) [or Enter to quit]: ").strip()
          if not source:
              break
          pat_file = input(f"PAT file [{next_pat}]: ").strip() or next_pat
      else:
          source = input("Enter source value (e.g. VIN2.5.6.10) [or Enter to quit]: ").strip()
          if not source:
              break
          pat_file = input("Enter PAT file path (e.g. misc/pat/pc61.txt): ").strip()

      should_continue = run_rule(source, pat_file, pth, dpspth, db_session)
      progress = {"last_source": source, "last_pat_file": pat_file}
      if not should_continue:
          break

  pr.yes("Workflow finished.")
  ```

- Guard at bottom:
  ```python
  if __name__ == "__main__":
      main()
  ```

- Run: `uv run ruff check --fix scripts/rus_exporter/vib_rule_workflow.py && uv run ruff format scripts/rus_exporter/vib_rule_workflow.py`

### Task 3.2 — Create `scripts/bash/vib_rule.sh`
`[x]`
- Content:
  ```bash
  #!/bin/bash
  # Run the Vibhanga rule word-filling workflow.
  uv run python scripts/rus_exporter/vib_rule_workflow.py "$@"
  ```
- `chmod +x scripts/bash/vib_rule.sh`

### Task 3.3 — Create `scripts/cl_dps/dpd-vib-rule`
`[x]`
- Content:
  ```bash
  #!/bin/bash
  # Shortcut to the Vibhanga rule word-filling workflow.
  cd "$HOME/Documents/dpd-db" && bash scripts/bash/vib_rule.sh "$@"
  ```
- `chmod +x scripts/cl_dps/dpd-vib-rule`

### Task 3.4 — Write integration tests
`[x]`
- Add to `tests/test_vib_rule_workflow.py`:

  `test_strip_variant_readings()`:
  - Input: `"dhammo-pi {variant reading here} vinayo-ca"`
  - Assert output equals `"dhammo-pi  vinayo-ca"` (or stripped equivalent — check exact whitespace)

  `test_suggest_next_pat_file_pc()`:
  - Input: `"misc/pat/pc60.txt"` → assert returns `"misc/pat/pc61.txt"`

  `test_suggest_next_pat_file_np()`:
  - Input: `"misc/pat/np25.txt"` → assert returns `"misc/pat/np26.txt"`

  `test_save_and_load_progress(tmp_path, monkeypatch)`:
  - Monkeypatch `vib_rule_workflow.VIB_PROGRESS_PATH` to `tmp_path / "vib_progress.json"`
  - Call `save_progress("VIN2.5.6.10", "misc/pat/pc60.txt")`
  - Call `load_progress()`, assert returns `{"last_source": "VIN2.5.6.10", "last_pat_file": "misc/pat/pc60.txt"}`

- Run: `uv run pytest tests/test_vib_rule_workflow.py -v`
- All must pass

### Phase 3 Completion Verification
`[x]`
- Announce: "Phase 3 complete — workflow script ready"
- Verify import works without triggering DB calls:
  Write `temp/test_workflow_import.py` with:
  ```python
  from scripts.rus_exporter import vib_rule_workflow
  print("import OK")
  ```
  Run `uv run python temp/test_workflow_import.py`, confirm prints "import OK", delete file
- Run: `uv run pytest tests/test_vib_rule_workflow.py -v` — must pass
- Ask user: "Does this meet your expectations? Please confirm with yes or provide feedback."
- **PAUSE and await user response**

---

## Phase 4: Final Quality Gates

### Task 4.1 — Lint all changed files
`[x]`
```bash
uv run ruff check --fix \
  tools/cst_sc_text_sets.py \
  scripts/change_in_db/copy_examples.py \
  scripts/export/list_of_words_from_txt.py \
  scripts/rus_exporter/vib_rule_workflow.py \
  tests/test_vib_rule_workflow.py
uv run ruff format \
  tools/cst_sc_text_sets.py \
  scripts/change_in_db/copy_examples.py \
  scripts/export/list_of_words_from_txt.py \
  scripts/rus_exporter/vib_rule_workflow.py \
  tests/test_vib_rule_workflow.py
```

### Task 4.2 — Full test suite
`[x]`
- `uv run pytest tests/test_vib_rule_workflow.py -v`
- All tests green

### Task 4.3 — Prepare commit
`[x]`
- Stage all modified and new files:
  ```bash
  git add \
    tools/cst_sc_text_sets.py \
    scripts/change_in_db/copy_examples.py \
    scripts/export/list_of_words_from_txt.py \
    scripts/rus_exporter/vib_rule_workflow.py \
    scripts/bash/vib_rule.sh \
    scripts/cl_dps/dpd-vib-rule \
    tests/test_vib_rule_workflow.py \
    misc/pat/vib_progress.json
  ```
- Draft commit message (present to user, do NOT run `git commit`):
  ```
  feat(vib): unified rule workflow script + fix -pi/-ca word extraction bug
  
  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  ```

---

## Known Errors / Repeated Mistakes to Avoid
- **No inline Python.** Never use `python -c "..."`. Write any one-off logic to
  `temp/<name>.py`, run it, delete it.
- **Import order matters.** Do NOT import `copy_examples.py` or `list_of_words_from_txt.py`
  before Task 2.1/2.2 are complete — both execute module-level code on import without guards.
- **Dry-run is NOT an early return.** When `dry_run=True`, all queries and field-set
  operations must still run (so the preview is accurate). Only `db_session.commit()` is
  skipped. Do not add early-return logic that bypasses the field assignments.
- **Shadow parity.** The localized filter in `make_cst_text_list_from_file`
  (`dps_make_no_field_inflections_set`) is the ONLY intentional divergence from upstream.
  Do not add any other divergences.
- **No `git commit`.** Prepare `git add` + draft message only. User commits manually.
