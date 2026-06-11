# Spec: Historical Sweep of Upstream-Deleted Leftovers

## Thread Type
Chore (one-time cleanup + doc alignment). Follow-up proposed in
`kamma/threads/20260610_sync_skill_improvements/review.md` ("Recommended Follow-up").

## Overview
Before thread 20260610, `execute_sync.py` used `git checkout`, which never propagated
upstream file deletions to the local worktree. Every sync since the fork's creation may
therefore have left behind files that upstream deleted but that still exist (and are
git-tracked) locally. Now that `execute_sync.py` uses `git restore --worktree` and
deletions propagate automatically, a **one-time historical sweep** is needed to find and
remove the accumulated leftovers, plus a docs-only pass to retire any remaining manual
"verify-then-remove" cleanup instructions from the sync docs.

A planning probe already sized the problem: comparing local tracked files against the
upstream tree at the last accepted sync SHA (`0ea58833`, from
`kamma/upstream_sync/accepted_sync.json`) and upstream's deletion history yields
**97 raw candidates** — files upstream once had, later deleted, still tracked locally.
Many are legitimate fork files (e.g. `exporter/goldendict/ru_components/*`,
`exporter/webapp/ru_templates/*` — upstream deleted Russian content when it moved to a
separate repo). These must be filtered out via `kamma/upstream_sync/registry.json`.

## What it should do
1. **Sweep script (throwaway, `temp/upstream_deletion_sweep/`)** that computes:
   - `upstream_tree` = `git ls-tree -r --name-only <accepted_sha>`
   - `ever_deleted_upstream` = `git log --diff-filter=D --name-only <accepted_sha>`
   - `local_tracked` = `git ls-files`
   - candidates = `local_tracked ∩ ever_deleted_upstream − upstream_tree`
   - then subtract every path registered in **any** `registry.json` category
     (`russian_copies`, `sbs_copies`, `dps_copies`, `tamil_copies`,
     `inspired_by_upstream`, `unique_paths`, `no_sync_files`,
     `modified_upstream_files`), reusing `registry_helper.py` for loading.
2. **Classification** of each remaining candidate:
   - Referenced in the active codebase (`rg` for filename/import, excluding archives) →
     **keep** and register in `registry.json` `unique_paths` (no SMD entry required).
   - Unreferenced → **delete** (plain filesystem delete of the tracked file, left as an
     *unstaged* deletion for user review; no commit).
3. **Sweep report** written to the thread folder: every candidate, its classification,
   the evidence (reference hits or "none"), and the action taken.
4. **Docs-only retirement**: sweep `kamma/upstream_sync/guide.md`, `README.md`, and
   `templates/` for any remaining instruction implying a manual verify-then-remove pass
   for upstream-deleted files; remove or align with the "deletions propagate" reality
   (guide.md already has the propagation note at line 216 — keep it).
5. **Validation**: `validate_registry.py` and `verify_smd_coverage.py` pass; ruff/pyright
   clean on the temp script while it exists; temp folder deleted before thread close.

## Assumptions & uncertainties
- **Baseline is the accepted sync SHA** (`0ea58833`), not `upstream/main` HEAD — the
  sweep must not pre-empt the next sync's deletions.
- Only **git-tracked** local files are in scope; untracked/ignored files are not
  upstream leftovers by definition.
- Registry filtering is by exact path and directory-prefix match (registry stores both).
- `rg`-based reference checking can miss dynamically-loaded data files (e.g.
  `gui2/data/*.json` built at runtime). Classification errs toward **keep + register**
  when uncertain; every deletion is individually listed in the report and recoverable
  via `git restore` before commit.
- The deletion-blocker + `run_acknowledged_blockers.txt` gate in `prep_analyzer.py` /
  `sync_runtime.py` stays **unchanged** (user decision: docs-only scope).

## Constraints
- No behavior changes to any `kamma/upstream_sync/scripts/*.py`.
- No commits, no staging — deletions stay unstaged for user review.
- Clean Root Protocol: sweep script lives in `temp/upstream_deletion_sweep/`, deleted
  before the final report.
- `docs/` is upstream-only — any leftover found inside `docs/` is always a delete
  candidate, never registered as local.

## How we'll know it's done
- Sweep report in the thread folder covers all 97 raw candidates (filtered + classified).
- Unreferenced leftovers show as unstaged deletions in `git status`; keepers appear in
  `registry.json` `unique_paths`.
- `validate_registry.py` and `verify_smd_coverage.py` exit 0.
- No remaining manual deletion-cleanup wording in `guide.md` / `README.md` / `templates/`.
- `temp/` contains no sweep artifacts; `git status --short` shows no new root-level files.

## What's not included
- Relaxing deletion blockers in `prep_analyzer.py` (explicitly deferred by user).
- Archiving deleted files (straight `git rm`-style deletion; history preserves content).
- Running an actual upstream sync; anything ahead of SHA `0ea58833`.
- Committing or pushing — user handles the commit after review.
