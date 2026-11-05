# Spec: Apply upstream-sync lessons §24–§29

Source: `kamma/upstream_sync/archive_improvements.md` §24–§29, harvested in
`kamma/archive/20261105_upstream_sync/retrospective.md` (sync `be49bffe2c2c..ee38f7a84`, closed 2026-11-05).
Type: chore (tooling fixes + process-doc rules).

## Overview
The 2026-11-05 sync recorded six lessons as recommendations only. None were applied.
This thread fixes the sync scripts that misbehaved (§24, §25), writes the process rules
into the guide and the sync-fast agent (§26–§29), and tightens the Stage 4 "promote"
step so future lessons get implemented, not only archived.

## What it should do

### A. `kamma/upstream_sync/scripts/execute_sync.py` (§24)
Current: `propagate_upstream_deletions` (lines ~109–167) runs
`git diff --no-renames --name-only --diff-filter=D A..B` without `-z` and calls
`Path.unlink()` on every candidate.
Bugs: (1) non-ASCII paths come back C-quoted, so `target.exists()` is False and they are
silently skipped; (2) a deleted submodule (gitlink, mode 160000) is a directory, so
`unlink()` raises EPERM and the run crashes mid-P0.
Required:
1. Use `git diff -z --raw --no-renames --diff-filter=D A..B` and parse NUL-separated
   records. This gives the old mode (to detect `160000`) and unquoted UTF-8 paths.
2. Gitlink candidates are **not removed**. Print an amber warning per gitlink
   ("upstream removed submodule <path> — remove manually with git rm after reviewing
   its uncommitted work") and count them separately. Reason: this sync's submodule
   dir held uncommitted user work; automatic deletion would destroy it.
3. `execute_sync(..., dry_run=True)` must not fail on a dirty tree. Today the
   `context.is_dirty` check (line ~242) runs before the dry-run return, so the dry run
   can't verify anything before the pre-pull commit. The dry run only fetches, verifies
   the manifest and lists exclusions, so it doesn't need a clean tree.

### B. `tests/test_shadow_cleanup.py` (orphan scanner script, §25)
Current: candidates come from `git ls-tree -r HEAD --name-only <folder>` (line 126),
so files deleted in the index but not yet committed are reported as orphans (126 of 137
hits were noise this sync). Exclusions merge `no_sync_files` + `unique_paths` + the four
`*_copies` maps, but ignore `inspired_by_upstream` (26 entries) and `skip_sync_patterns`
(30 entries, e.g. `scripts/archive/`).
Required:
1. Read candidates from the index: `git ls-files -- <folder>`.
2. Treat `inspired_by_upstream` keys like shadow keys (exact match, or a key ending in
   `/` as a prefix). Add `skip_sync_patterns` to the exclusion list (`is_excluded`
   already handles `/` prefixes and globs).
3. Move the orphan-selection loop into a pure function
   `find_orphans(current_files, upstream_files, registry) -> list[str]` so it can be
   unit-tested. CLI behaviour is otherwise unchanged.

### C. `kamma/upstream_sync/scripts/sync_status.py` (§25)
Current: `derive_stage` infers the stage from which artifacts exist. When
`dynamic_plan.md` exists it says "Stage 3", even during 2b–2d. With `retrospective.md`
present it keeps saying "Stage 4 … finalize" even after finalize ran (it said that on
2026-11-05).
Required (still artifact-based, no handoff parsing):
1. `dynamic_plan.md` present and `execute_sync_done.json` absent → Stage 2
   (sub-stages 2a–2d; `execute_sync.py` runs in Stage 3 A3 on the non-fast path, as it
   did this sync). `dynamic_plan.md` + `execute_sync_done.json` → Stage 3 as today.
2. `retrospective.md` present and `kamma/upstream_sync/accepted_sync.json`
   `last_accepted_upstream_sha` == manifest `to_upstream_sha` → new closed descriptor,
   e.g. stage `"Stage 4: Closed (sync accepted)"`, next command "none — start a new
   sync thread". The stage string must keep a `Stage 4` token (drift guard
   `test_stage_names_match_guide_headers`). `derive_stage` gets an optional
   `accepted_sync_path` parameter so tests can use `tmp_path`.

### D. `kamma/upstream_sync/scripts/validate_registry.py` (§25)
Current: with `repo_root` set, a `*_copies` or `inspired_by_upstream` upstream path that
is not in the working tree is an error (lines ~169–177, ~266). Before the pull, an
upstream path that was repointed this sync only exists in the upstream ref, so the
standalone validator fails (it did this sync).
Required: when the working-tree check fails, fall back to
`git cat-file -e upstream/main:<path>` (`upstream/main` = `last_accepted_upstream_ref`
in `accepted_sync.json`; strip a trailing `/` for directories). Error only if both fail.
If git or the ref is unavailable, behaviour stays as today (error), so the existing
`test_inspired_by_upstream_missing_upstream_target_path` (tmp_path, not a git repo)
keeps passing.

### E. Classification wording (§25)
`prep_analyzer.py:568` and `guide.md:244` tell Stage 2 to "register" new upstream
additions with no local collision. That contradicts guide "Merge scope vs. verbatim
pull": unregistered paths are pulled verbatim. Reword both: these additions are
mirrored verbatim; register one only if Stage 2 decides it needs a local divergence.

### F. Process rules (§26–§29), doc-only
- `.claude/agents/sync-fast.md`, "What You Do": lint/format commands use literal file
  paths only. No shell variables, no `&&`-chained assignments. Never run
  `ruff check --fix`/`ruff format` without an explicit path (§26).
- `guide.md` Stage 2a bullet: run `git diff --name-status <from>..<to> -- tests/` and
  check local `tests/` for imports of upstream symbols changed in range. Record
  upstream-test watch items in the owning source file's registry `watch_for`, because
  `tests/` is skip_sync and can't hold registry entries (§27).
- `guide.md` Stage 2a bullet: framework major-version migrations need an AST scan of
  the framework's attribute/call usage in local files, plus probes with
  `uv run --no-project --with <pkg>==<ver> python -c ...` (§29).
- `guide.md` Stage 2c bullet: re-verify every 2a/2b factual claim against the files
  before writing a recipe on it; run every recipe `Verify` command once when it's
  written (§28).
- `guide.md`, one line in the general/session rules: zsh `$SHA:path` triggers modifier
  expansion, so write `${SHA}:path`; park draft threads in `kamma/drafts/`, never
  `kamma/threads/` (the spec-gate hook blocks all edits otherwise) (§28, §29).

### G. Close the process gap (Stage 4 step 2), doc-only
`guide.md` Stage 4 step 2 already says promote items should become "a guide rule /
validator / archive entry — do it now". This sync took "archive entry" as sufficient,
so nothing was applied. Reword: a promote item is done only when the rule/code change
is applied, or when it is recorded in `archive_improvements.md` **and** a follow-up
thread is created in `kamma/drafts/` and named in the retrospective's
"Open after finalize". Mirror the same sentence in `templates/retrospective.md`'s
Promote header.

## Assumptions & uncertainties
Verified by reading source (2026-11-05): every current-behaviour claim above, with line
numbers (`execute_sync.py` 109–167 and 240–245, `test_shadow_cleanup.py` 103–140,
`sync_status.py` `derive_stage`, `validate_registry.py` 150–177 and 260–267,
`prep_analyzer.py` 566–569, `guide.md` 244, 268, 380–393, `sync-fast.md`); registry
category sizes; existing tests (`test_sync_deletion_propagation.py`,
`test_execute_sync.py`, `test_sync_status.py`, `test_validate_registry.py`); that no
test or script asserts the "Register them" text.
Assumptions:
- `git diff --raw` reports old mode `160000` for a deleted gitlink (standard git; the
  first task's failing test confirms it).
- `upstream` is the remote name on the user's machine (it is in `accepted_sync.json`).
- `test_execute_sync.py` mocks `GitContext`, so the dry-run/dirty test can follow its
  existing pattern (line 194).

## Decisions made (approved by user 2026-11-05)
1. Gitlinks: warn and skip, never auto-delete (A2).
2. **Dropped from §24:** "stale acknowledged blocker → warning". The rejection in
   `sync_runtime.verify_manifest` is a deliberate safety check, and fixing it cost one
   file edit. Not worth weakening.
3. `sync_status`: artifact rules only; no parsing of the handoff status line.
4. G is included (process gap flagged during the sync close-out).

## Constraints
- Pre-completion gates per CLAUDE.md on every touched `.py` (ruff/pyright/pyrefly;
  `tests/` files need `pyright --project /dev/null`). Targeted pytest only, never bare.
- These are fork-local tools/docs (`kamma/` is `no_sync_files`; `tests/` and `.claude/`
  are `skip_sync_patterns`), so no registry change is expected. Run
  `validate_registry.py` anyway.
- No edits to `docs/`. No `git stash`/`restore`/`reset`.

## How we'll know it's done
- New/updated tests pass: non-ASCII deletion removed, gitlink deletion skipped with a
  warning and no crash, dry run on a dirty tree returns 0, `find_orphans` ignores
  index-deleted files and inspired/skip_sync paths, sync_status gives Stage 2 for
  plan-without-done-marker and "Closed" for an accepted sync, validator accepts a path
  that exists only in `upstream/main`.
- `sync_status.py kamma/archive/20261105_upstream_sync` prints the Closed stage.
- `validate_registry.py` is valid; the sync suites listed in `guide.md:356` pass at
  their current baseline.
- `guide.md`, `sync-fast.md` and `templates/retrospective.md` contain the F/G rules;
  `test_sync_status.py` guide-anchor drift guards still pass.

## What's not included
- Stale-ack downgrade (decision 2).
- Removing the stale `[submodule]` section in `.git/config`.
- Any change to `execute_sync.py` beyond `propagate_upstream_deletions` and the
  dry-run/dirty ordering.
- Archiving the closed sync thread dir.
