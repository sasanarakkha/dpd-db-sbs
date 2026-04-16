# Handoff — Vibhanga Rule Workflow Streamlining
**Date:** 2026-04-12
**Branch:** `sbs-ru`
**Thread dir:** `kamma/threads/20260412_vib_rule_workflow/`

---

## Status

| Phase | Status |
|-------|--------|
| Phase 1 — Bug fix in `make_cst_text_list_from_file` | ✅ DONE |
| Phase 2 — `__main__` guards + `dry_run` param | ✅ DONE |
| Phase 3 — Unified workflow script | ✅ DONE |
| Phase 4 — Final quality gates | ✅ DONE |
| Review (`/kamma:3-review`) | ✅ PASSED |
| Post-review refactor (vib_rule.sh removed, script moved) | ✅ DONE |

---

## What Was Done (Full Thread)

### Phase 1 — Bug fix (`tools/cst_sc_text_sets.py`)

Rewrote the hyphenation loop in `make_cst_text_list_from_file` from a
list-mutation-during-iteration pattern to a safe collect-and-replace pattern.
Old code used `enumerate()` + `insert()` which caused index drift and silently
skipped words (confirmed on real PAT files with `-pi`/`-ca` clitics).

**New loop:**
```python
expanded: list[str] = []
for word in words_list:
    if "-" in word:
        expanded.append(word.replace("-", ""))
        expanded.extend(word.split("-"))
    else:
        expanded.append(word)
words_list = expanded
```

Upstream `make_cst_text_list` still has the old loop — shadow divergence is
intentional and documented here. Output order is identical.

### Phase 2 — Importability refactor

- `scripts/change_in_db/copy_examples.py`: module-level function call (lines
  148–154) wrapped in `if __name__ == "__main__":`. `dry_run: bool = False`
  parameter added to `update_column_for_some_criteria`. When `dry_run=True`,
  all queries run but `db_session.commit()` is skipped.
  **Note:** module-level `pth = ProjectPaths()` and `db_session = get_db_session(...)`
  remain at module level (by design — the function references the global `db_session`).
  Importing the module still creates a DB session; this is expected and harmless.

- `scripts/export/list_of_words_from_txt.py`: both module-level blocks (session
  init at lines 19–23 AND function call at lines 146–150) moved inside
  `if __name__ == "__main__":`. Import is now clean.

### Phase 3 — Unified workflow script

- `scripts/change_in_db/vib_rule_workflow.py` — main Python logic (was
  originally created as `scripts/rus_exporter/vib_rule_workflow.py`, moved
  post-review to `scripts/change_in_db/` to co-locate with `copy_examples.py`)
- `scripts/cl_dps/dpd-vib-rule` — shortcut using `run_and_log.sh` pattern
  (same as `dpd-gui2`, `dpd-build-db`, etc.); logs to `~/logs/vib_rule_*.log`
- `scripts/bash/vib_rule.sh` — was created, then **removed** post-review as
  redundant (single line); logic folded directly into `dpd-vib-rule`

### Phase 4 — Tests and lint

- `tests/test_vib_rule_workflow.py` — 8 tests, all passing:
  - `test_clitics_not_skipped_from_file`
  - `test_clitics_order_in_result`
  - `test_dry_run_does_not_commit`
  - `test_dry_run_commits_by_default`
  - `test_strip_variant_readings`
  - `test_suggest_next_pat_file_pc`
  - `test_suggest_next_pat_file_np`
  - `test_save_and_load_progress`
- All changed files pass `ruff check` + `ruff format`

---

## Current State

**Awaiting manual review.** User will run the script in real use and provide feedback
in the next session. No further code changes should be made until that feedback is received.

Changes since last handoff (this session):
- Added first copy_examples pre-populate run (step 3b in `run_rule`) — mirrors step 1
  of the original 7-step workflow; eliminates false positives in word extraction.
- Removed dry-run preview prompt from step 6 — second copy_examples run now commits
  directly without confirmation dialog.
- Updated module docstring to reflect the actual 8-step flow.

### Files to stage and commit

```bash
git add \
  tools/cst_sc_text_sets.py \
  scripts/change_in_db/copy_examples.py \
  scripts/change_in_db/vib_rule_workflow.py \
  scripts/export/list_of_words_from_txt.py \
  scripts/cl_dps/dpd-vib-rule \
  tests/test_vib_rule_workflow.py \
  kamma/threads/20260412_vib_rule_workflow/
```

Note: `scripts/bash/vib_rule.sh` was deleted — `git rm` was already run, so
after `git restore --staged .` it appears as an untracked deletion. Re-apply
with: `git rm scripts/bash/vib_rule.sh` before committing.

### Draft commit message

```
feat(vib): unified rule workflow script + fix -pi/-ca word extraction bug

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## Known Errors / Pitfalls

1. **`list_of_words_from_txt.py` had TWO module-level blocks** — both guarded.
   If re-editing, keep all instantiation (pth, dpspth, db_session) inside `__main__`.
2. **`copy_examples.py` module-level DB session is intentional** — do not move
   it inside `__main__` without also refactoring the function to accept a session
   parameter (out of scope).
3. **No inline Python** — never `python -c "..."`. Write to `temp/<name>.py`, run, delete.
4. **No `git commit`** — prepare `git add` + draft message only. User commits manually.
5. **Pre-existing test failure**: `test_namespace_isolation.py::test_symbol_naming_convention[tpr_exporter_ru.py]`
   — pre-existing, unrelated to this thread, do not touch.
6. **`dry_run` is not an early return** — only `db_session.commit()` is skipped;
   all queries and field assignments must still run so the preview is accurate.
7. **Script rename**: the main Python file was renamed from
   `scripts/rus_exporter/vib_rule_workflow.py` → `scripts/change_in_db/vib_rule_workflow.py`
   after the review. Thread docs (spec.md, plan.md) still reference the old path —
   these are historical records and intentionally not updated.
