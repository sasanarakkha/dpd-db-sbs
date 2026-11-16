> **Thread type:** Loop (standing thread)

# Spec: Grammar TSV fixes (Pali Class)

## Overview
Standing loop for correcting the Pali Class grammar data in `shared_data/pali_class/grammar/`. Each cycle is one targeted find-and-replace across the TSVs, and does ONLY what the user explicitly asks for in that cycle.

## Loop Domain
Tracked TSVs in `shared_data/pali_class/grammar/` (61 sheets listed in `sheet_order.txt`). They feed the grammar Anki deck via `scripts/work_with_csv/anki_class_grammar.py`.

## In-Scope
- Typo and diacritic fixes.
- Content corrections (wrong forms or glosses).

## Out-of-Scope
- Terminology/label renames, formatting normalisation, structural changes (rows, columns, file names).
- Edits to the exporter script, tests, or anything outside the grammar folder.
- Any preliminary, exploratory or "while here" work the user did not ask for in the cycle. No scanning for further errors unless asked.

## Hard Rules
- TSVs are never edited by hand or in an editor. Changes are made only by scripted find-and-replace, scoped (files / columns / anchored context) so as not to hit false positives.
- All preliminary setup is done once, up front (see `baseline.md`). Cycles do not repeat it.

## Validation Standards (every cycle)
1. Dry run: list every match with file, row, column, context; user reviews and marks false positives.
2. Replace only the approved matches.
3. `git diff` on the grammar folder equals exactly the approved matches; row/column counts per file match `baseline.md`.
4. `uv run python scripts/work_with_csv/anki_class_grammar.py` runs with exit 0 and no amber/red lines (baseline has none).
5. `git -C ../sasanarakkha/study-tools status --short` is unchanged before/after the script; report any change, do not revert.
6. `uv run pytest tests/test_anki_class_grammar.py tests/test_anki_class_grammar_feedback.py` (loader sanity only; they do not read the real TSVs).

## Completion Condition
The user declares the loop done, after the Pre-Commit Cross-Check (another model, new session) has reviewed all uncommitted changes (see plan.md).

## Assumptions & uncertainties
None open. Facts established (see `baseline.md`): script output goes to gitignored `temp/anki_csvs/pali_class/grammar/`; it also rewrites column-name-only field-list md files in the external study-tools repo (unchanged by the baseline run); the tests never read the real TSVs.

## Constraints
- No model splitting.
- Scratch work under `temp/`, deleted afterwards.
- No commits unless asked; draft a commit message per cycle.

## How we'll know it's done (overall)
The user says so, and every cycle record shows clean validation.
