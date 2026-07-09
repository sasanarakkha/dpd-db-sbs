# Handoff: Upstream Sync 2026-07-09

## Status

Stage 1 COMPLETE. Chain green end-to-end; triage verdict routes to Stage 2 (blockers + discuss
items present, no fast path). Awaiting user approval of the `#pre-sync` commit, then a fresh
session for Stage 2a.

## Current Stage

Stage 1 done (ADVANCED ran the scripted chain directly per the guide's carve-out).
Next: Stage 2a Impact assessment. Owner: ADVANCED.

## Stage 1 verdict (from sync_triage)

- `blocker_paths` (8): `exporter/analysis/ui_utils.py`, `shared_data/help/README.md`,
  `shared_data/help/abbreviations.tsv`, `shared_data/help/abbreviations_other.tsv`,
  `shared_data/help/abbreviations_other_README.md`, `shared_data/help/bibliography.tsv`,
  `shared_data/help/help.tsv`, `shared_data/help/thanks.tsv`
- `discuss_paths` (6): `.gitignore`, `.pre-commit-config.yaml`, `AGENTS.md`, `db/models.py`,
  `gui2/main.py`, `pyproject.toml`
- `execute_sync.py` has NOT run yet — blocked until Stage 2 resolves blockers/discuss items.
- Artifacts written: `prep_report.md`, `prep_manifest.json` (this thread dir).
- Upstream fetched: `e137814c1..be49bffe2` on `upstream/main`.

## Pre-sync fixes applied this session (user-approved)

1. **`tests/kamma` → `tests/kamma_tests` rename** (`git mv`, staged). Root cause: `tests/kamma/`
   was a regular package added ~2026-06-22; any `uv run python3 tests/<script>.py` gets `tests/`
   as `sys.path[0]`, so `import kamma` resolved to `tests/kamma` and blocked the repo-root
   `kamma/` namespace package (`kamma.upstream_sync` unfindable). Atomic Rename Protocol
   followed: single textual reference updated (`tests/kamma_tests/improve/test_precommit_gate.py`),
   zero stale references verified by rg, no registry.json entries referenced the old path.
   Suite re-run: 125 passed, 1 failed — the failure
   (`test_ai_meaning_checker.py::test_get_words_for_comparison_notes_raw_mode_matches_fixture`)
   is PRE-EXISTING data drift (live DB vs frozen fixture, after 2026-07-09 translation batch
   commit `52b83e923`), unrelated to the rename. Belongs to the translate thread, not this sync.
2. **stage1.py lint gate `E999` removal**: modern ruff (0.15.16) removed the `E999` rule id;
   gate now selects `F821` only (syntax errors are always reported by ruff regardless).
3. **stage1.py lint gate archive exclusion**: added `--extend-exclude
   scripts/archive,scripts/dps_archive` (NOT `--exclude`, which would clobber pyproject excludes
   like `tools/writemdict/*`). User-approved policy: `archive/` and `scripts/archive/` are pulled
   from upstream but contents never linted/analyzed; `scripts/dps_archive/` is fork-local and
   outside all sync activity. Registry already encodes this (`skip_sync_patterns` /
   `unique_paths`); no registry change needed.
4. Docs updated to match: `guide.md`, `templates/sync_thread_plan.md`, `archive_improvements.md`
   (#16), this thread's `plan.md`.

All edited Python validated: ruff check/format clean, pyright 0 errors, pyrefly clean,
`test_precommit_gate.py` 5/5 pass.

## Pre-sync entrypoint notes

- `scripts/cl_dps/dpd-kamma-sync` failed twice at `git add` with a transient `.git/index.lock`
  race (an external file watcher reacts to the TSV writes). The backup itself succeeded; the
  remaining entrypoint steps were completed manually with identical commands:
  `git add <4 TSVs>` + `git commit -m "backup dps data"` (landed as `aba32c09a`, only
  `russian.tsv` changed), then `init_sync_thread.py`.

## Last upstream sync

- **Commit / tag**: `518672a65fa3`
- **Full SHA**: `518672a65fa3ea7c36c4c754dc5276bb41f92da7`
- **Date**: `2026-06-12T20:48:06+08:00`
- **Ref**: `upstream/main`

## Completed Work

- Pre-sync entrypoint completed (backup committed as `aba32c09a`, thread initialized).
- Environment blockers fixed (see Pre-sync fixes above).
- Stage 1 chain passed fully: shadow health ✅, lint gate ✅, registry validation ✅,
  `git fetch upstream` ✅, prep analyzer ✅, triage verdict = Stage 2.

## Commands Already Run

- `scripts/cl_dps/dpd-kamma-sync` (twice; git add failed both times on index.lock race)
- `git add db/backup_tsv/{russian,sbs,tamil,ru_roots}.tsv && git commit -m "backup dps data"` → `aba32c09a`
- `uv run python3 kamma/upstream_sync/scripts/init_sync_thread.py`
- `git mv tests/kamma tests/kamma_tests`
- `uv run pytest <all 9 tests/kamma_tests files>` → 125 passed, 1 pre-existing failure (see above)
- `uv run python3 kamma/upstream_sync/scripts/stage1.py <thread_dir>` → exit 0 through prep
  analyzer; triage verdict Stage 2 (exit 1 by design while blockers/discuss remain)
- Full validation suite on edited files (ruff/format/pyright/pyrefly) — all clean

## Files Changed

- `tests/kamma/**` → `tests/kamma_tests/**` (git mv, staged; + path fix and ruff format in
  `tests/kamma_tests/improve/test_precommit_gate.py`)
- `kamma/upstream_sync/scripts/stage1.py` (lint gate: F821-only + archive extend-exclude)
- `kamma/upstream_sync/guide.md` (lint gate command + archive policy line)
- `kamma/upstream_sync/templates/sync_thread_plan.md` (lint gate command)
- `kamma/upstream_sync/archive_improvements.md` (#16 lint gate command + archive note)
- `kamma/threads/20260709_upstream_sync/` (thread artifacts: plan/spec/handoff/prep_report/prep_manifest)

## Open Decisions

- User approval of the `#pre-sync` commit (message prepared, see Next Action).
- Stage 2: resolve 8 `blocker_paths` + 6 `discuss_paths` (see Stage 1 verdict).

## Errors, Issues, And Repeated Mistakes

- Transient `.git/index.lock` race when scripts `git add` right after bulk file writes — retry
  or run the git step manually.
- `ruff --exclude` on the CLI REPLACES pyproject excludes; always use `--extend-exclude`.
- Dirty `resources/*` submodules in the working tree — NOT part of this sync's commit scope;
  report separately, never stage.

## Retrospective candidates (for Stage 4)

- landed: E999 removal + archive extend-exclude in stage1.py lint gate; tests/kamma rename.
- promote: "never name a tests/ subpackage after a top-level repo package" (shadows imports for
  tests-rooted script runs); note `tests/exporter/` still shadows root `exporter/` the same way
  (pre-existing, not currently blocking — candidate for the same rename treatment).

## Next Model

ADVANCED (fresh session) — Stage 2a Impact assessment.

## Next Action

1. User reviews/approves commit:
   `#pre-sync: fix tests/kamma shadowing and stage1 lint gate, 2026-07-09`
   Scope: staged rename + the files listed in Files Changed (exclude `resources/*` submodules).
2. Then start a fresh session for Stage 2a: read `prep_report.md` + `prep_manifest.json`,
   classify every changed path in `dynamic_plan.md` (2a), resolve discuss items with the user
   one at a time (2b), author the literal plan (2c), approval gate (2d).

## Restart Prompt

```text
Continue upstream sync thread: kamma/threads/20260709_upstream_sync.
Stage 1 is COMPLETE; Stage 2a is next. Read handoff.md, then prep_report.md and
prep_manifest.json in the thread dir. Classify every changed path (port / mirror /
preserve / discuss / inspired / skip / docs) into dynamic_plan.md per guide.md
Stage 2. Do not run execute_sync.py until blockers and discuss items are resolved.
```

Do not continue in this session.
