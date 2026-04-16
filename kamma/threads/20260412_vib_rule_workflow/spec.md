# spec.md — Vibhanga Rule Workflow Streamlining

## Overview
Consolidate the 7-step per-rule Vibhanga word-filling process into a single interactive
terminal script. The script remembers progress, accepts pasted text, extracts unrecognized
words, waits for the user to add them in gui2, previews DB changes for safety, then
commits. A parallel bug fix ensures clitic-suffixed words (`-pi`, `-ca`) are never
silently skipped.

## Current Workflow (7 steps per rule)
1. Edit `copy_examples.py` → set `source_value` (e.g. `"VIN2.5.6.10"`) → run
2. Manually copy Vibhanga rule text → `misc/pat/pc60.txt`
3. Copy that text → `temp/text.txt`
4. Run `scripts/export/list_of_words_from_txt.py`
5. Open `temp/text_vib_example_pat_example.tsv`, review word list
6. Add each word in `gui2/main.py` → Pass2Add tab
7. Run `copy_examples.py` again with same `source_value`

## Known Bug
`list_of_words_from_txt.py` silently skips some words ending in `-pi`/`-ca`.
Suspected root cause: `make_cst_text_list_from_file` in `tools/cst_sc_text_sets.py`
mutates `words_list` while iterating with `enumerate()` during hyphenation splitting,
causing index drift.
**Fix constraint:** `make_cst_text_list_from_file` is a strict shadow copy of upstream
`make_cst_text_list`. The fix must maintain full logic parity with upstream — only the
localized filter (`vib_example`/`pat_example` field check) may differ. Mirror whatever
upstream does for the hyphenation loop.

## What It Should Do

### Task 1 — Fix -pi/-ca bug (shadow-safe)
- Compare `make_cst_text_list_from_file` (lines 318–375) with upstream
  `make_cst_text_list` (lines 86–175) in `tools/cst_sc_text_sets.py`
- Reproduce the bug in a unit test (red phase)
- Patch the hyphenation loop to match upstream's fix, preserving the localized filter
- Green phase: test passes, full suite still passes

### Task 2 — Single interactive workflow script
Create `scripts/rus_exporter/vib_rule_workflow.py` (Python logic) +
`scripts/bash/vib_rule.sh` (bash entry point) +
`scripts/cl_dps/dpd-vib-rule` (shortcut).

**Script behavior — full session loop:**

1. **Startup: recall progress**
   - Read state from `misc/pat/vib_progress.json`
     (`{"last_source": "VIN2.5.6.10", "last_pat_file": "misc/pat/pc60.txt"}`)
   - If state exists, display:
     > Last rule: VIN2.5.6.10 (misc/pat/pc60.txt)
     > Suggested next: misc/pat/pc61.txt
     > Enter source value for next rule [or press Enter to quit]:
   - If no state, prompt for source value and PAT file name

2. **Text input**
   - Print: `Paste the rule text below. When done, press Ctrl-D (EOF):`
   - Read multiline stdin until EOF
   - Strip `{...}` patterns (variant readings) from pasted text using regex `\{[^}]+\}`
   - Save cleaned text to:
     - `misc/pat/pcXX.txt` (the PAT file for this rule)
     - `temp/text.txt` (for word extraction)

3. **Word extraction**
   - Run the fixed word extraction (same logic as `list_of_words_from_txt.py`)
   - Print: `Found N unrecognized words:`
   - Print each word, one per line
   - Also save backup TSV to `temp/text_vib_example_pat_example.tsv`

4. **GUI step pause**
   - Print: `Add the above words in gui2/main.py → Pass2Add tab.`
   - Print: `Press Enter when done (or type 'q' to quit):`
   - If user types `q`: save current progress, exit
   - If user presses Enter: continue

5. **Dry-run safety gate (copy examples)**
   Before writing anything to the database, the script must:
   - Run `copy_examples` logic in dry-run mode — collect all rows that would be
     changed but do NOT call `db_session.commit()`
   - Print a full preview: word ID, lemma_1, which fields would be set, old → new value
   - Ask: `Apply these changes to the database? [y/N]:`
   - Only commit if user types `y`. Any other input skips the DB write and prints "Skipped."

   `update_column_for_some_criteria` in `copy_examples.py` must accept a
   `dry_run: bool = False` parameter. When `dry_run=True`, all logic runs
   (queries, field comparisons, logging) but `db_session.commit()` is NOT called.

6. **Save progress and loop**
   - Save `misc/pat/vib_progress.json` with current `last_source` and `last_pat_file`
   - Print: `Rule VIN2.5.6.10 done. Suggested next: misc/pat/pc61.txt`
   - Print: `Continue to next rule? [Enter] or quit [q]:`
   - If continue: loop back to step 1 with next suggested PAT file pre-filled
   - If quit: exit

## Affected Files
| File | Purpose |
|------|---------|
| `tools/cst_sc_text_sets.py` | Bug fix in `make_cst_text_list_from_file` |
| `scripts/change_in_db/copy_examples.py` | Add `__main__` guard + `dry_run` param |
| `scripts/export/list_of_words_from_txt.py` | Add `__main__` guard |
| `scripts/rus_exporter/vib_rule_workflow.py` | New — main Python logic |
| `scripts/bash/vib_rule.sh` | New — bash entry point |
| `scripts/cl_dps/dpd-vib-rule` | New — cl_dps shortcut |
| `misc/pat/vib_progress.json` | New — persisted state |
| `tests/test_vib_rule_workflow.py` | New — tests |

## Constraints
- `copy_examples.py` and `list_of_words_from_txt.py` remain callable standalone; not
  structurally changed beyond `__main__` guards and `dry_run` parameter
- PAT files in `misc/pat/` continue to be saved (archival source)
- Shadow-parity rule for `make_cst_text_list_from_file` — fix mirrors upstream logic,
  only the localized filter differs
- All code: `ruff check --fix` + `ruff format`, modern type hints, `Path` for paths
- `from tools.printer import printer as pr` for output
- No inline Python scripting

## How We'll Know It's Done
- `bash scripts/bash/vib_rule.sh` runs the full loop interactively
- Known `-pi`/`-ca` words appear in the word list (not skipped)
- Dry-run preview shows proposed DB changes before any commit
- `misc/pat/vib_progress.json` is written/updated correctly after each rule
- `uv run pytest tests/test_vib_rule_workflow.py -v` passes

## What's Not Included
- Automating text extraction from Vibhanga PDF/HTML
- gui2 Pass1/Pass2Add modifications
- Batch-processing multiple rules non-interactively
