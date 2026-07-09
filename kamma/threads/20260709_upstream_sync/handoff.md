# Handoff: Upstream Sync 2026-07-09

## Status

**Stage 1.5 pull DONE and verified.** At the **Commit 1 gate** (USER commits), then a **fresh
session** runs Stage 3 FAST. Stage 2 was COMPLETE + APPROVED in a prior session.

## What happened this session (pull + a tooling-bug detour)

1. **Setup-commit gate** was already clear (prior `e7005ac39`).
2. **Upstream advanced mid-sync (+2 CI-only commits):** `git fetch upstream` moved `upstream/main`
   from the analyzed `be49bffe` to `820113551` (2 commits, one new file
   `.github/workflows/deconstructor_ci_test.yml`, no localization impact). Per USER decision
   (Option A) we **pinned** to `be49bffe` and deferred the 2 commits to next sync:
   - `accepted_sync.json.last_accepted_upstream_ref` → `"be49bffe…"` (was `"upstream/main"`)
   - `prep_manifest.json.target_upstream_ref` → `"be49bffe…"` (was `"upstream/main"`)
   - Committed as `4f420da28`.
   - **STAGE-4 TODO:** `finalize_accepted_sync.py` derives the next accepted ref from
     `manifest.target_upstream_ref`, so it will write the SHA. **After finalize, reset
     `accepted_sync.json.last_accepted_upstream_ref` back to `"upstream/main"`.**
3. **TOOLING BUG found + fixed (committed `7c2ea4035`):** `execute_sync.py` step 5 used
   `git restore --source as_upstream --worktree -- .` — no-overlay default **DELETES** every
   tracked file absent from upstream. First two pulls wiped ~2780 local-only files (shadows,
   unique_paths, `russian_words_user_dict.txt`, `russian/sbs/tamil.tsv`, etc.). Fixed to
   `git restore --overlay …` (verified in isolation: updates/creates upstream paths, preserves
   local-only files, stays unstaged). Regression from `33ed53d34` (checkout→restore). The last
   sync (2026-06-13) was driven manually in batches, so the automated `restore` path's first real
   run was this one. **HEAD was never lost**; recovered each time with `git checkout HEAD -- .`.
   - **Gotcha learned:** the fix is a tracked change, but `execute_sync.py` requires a clean tree,
     and `git stash -u` swallows uncommitted tracked changes → the fix MUST be committed before the
     pull. That is why `7c2ea4035` lands before Commit 1.
4. **Corrected pull (3rd attempt) SUCCEEDED.** 314 files changed: **200 M, 108 D, 53 A**. All 108
   deletions verified upstream-deleted (matches expected ~108 P0). All local-only files preserved.
   `cst_source_sutta_example.py` correctly removed (S10). `as_upstream` → `be49bffe2`.

## COMMIT 1 GATE (next action — USER commits)

**Message:** `#sync: upstream pull 518672a6..be49bffe, 363 files, 2026-07-09`
(363 = 255 add/modify + 108 delete, excluding resources/*; kamma bookkeeping folded in.)

**Scope:** stage the sync content (M/D/A upstream files) + kamma bookkeeping
(`execute_sync_done.json` marker, `plan.md`, this `handoff.md`).
**EXCLUDE `resources/*`** — all 7 are dirty content only, **no gitlink (recorded SHA) change** was
pulled (verified: SHAs identical, only `-dirty` suffix). Suggested staging that excludes them:
`git add -A -- . ':(exclude)resources'` then commit.

**Redundant session stashes to drop after Commit 1:** `sync-rerun-20260709` and
`sync-rerun2-20260709` (they hold now-regenerated upstream files). `git stash drop` each. The other
`stash@{...}` WIP entries belong to the USER — DO NOT touch.

## After Commit 1 — forward plan (Stage 3 FAST, fresh session)

- Dispatch `sync-fast` (sequential batches) to execute `dynamic_plan.md` §9 recipes (D1–D8/D13
  manual merges, S1–S13 shadow ports, I1–I15 inspired backports, D7 rename fan-out, D11 removals,
  D12 explicit `git rm`), then the §8 verification battery, then Commit 2 gate (message only:
  `#sync: manual merge resolutions 2026-07-09`).
- Dispatch prompt = embed `uv run python3 kamma/upstream_sync/scripts/sync_status.py <thread_dir>
  --instructions` output. Verify subagent work from files, not self-report.
- **Note for Stage 3:** `scripts/archive/` still has 19 files (local-only or D11/D12 explicit-`git
  rm` targets). Confirm classification during Stage 3; P0 correctly left them (they were not in the
  upstream-deletion diff).

## Highest-risk Stage 3 items (from §9)

- **I1/I2** (largest): port `export_dpd.py` ProcessPoolExecutor rewrite into `export_dpd_ru.py` /
  `export_dpd_sbs.py`, re-layering RU/SBS joinedloads + locale flags.
- **S4/S6/S7**: pulled `data_classes.py` constructor signatures change → shadow subclasses MUST adapt
  (S4 eliminates the `DeconstructorData_ru` subclass; header-once) or they crash at runtime.
- **S10**: switch `cst_source_sutta_example` import → `cst_source` (old module deleted by P0) or ImportError.
- **S12+I14+I15**: bz2→xz fan-out (server script, release workflows, docs).
- Verified N/A: I4/I5 `zip[1:]` bibliography bug ABSENT in RU/SBS copies; I6 RU has no `see` builder.

## Last upstream sync range

- **From SHA**: `518672a65fa3ea7c36c4c754dc5276bb41f92da7` (2026-06-12)
- **To (PINNED)**: `be49bffe2c2c85971784337d4e09915ad1f42800` (2026-07-09).
  `upstream/main` is actually at `820113551…` (+2 CI-only commits, deferred).

## Errors, Issues, And Repeated Mistakes (this run)

- **execute_sync.py no-overlay restore wiped the tree** — fixed with `--overlay` (`7c2ea4035`).
  Add a regression test as a Stage-4 retrospective item.
- **`git stash -u` swallows uncommitted tracked changes** — commit tooling fixes before any pull.
- **`git checkout <stash> --` with empty pathspec DETACHES HEAD** — reattach with `git checkout sbs-ru`.
- `execute_sync.py` dirty-guard counts UNTRACKED files → tree must be free of untracked before pull.
- Dirty `resources/*` submodules: NOT commit scope unless a gitlink SHA actually changed.

## Retrospective candidates (for Stage 4)

- **NEW (high priority):** `execute_sync.py` `--overlay` regression — add a regression test that
  asserts a local-only tracked file survives a pull; consider CI coverage of the sync entrypoint.
- (carried) stage1 lint gate fixes; tests/kamma rename; "never name a tests/ subpackage after a
  top-level repo package".
- Local-commit sweep caught unregistered locally-modified upstream files — consider adding to prep_analyzer.
- `skill_scope_improvement.md` — guide/skill fixes; apply as a SEPARATE post-sync task.

## Next Model

USER (Commit 1), then **fresh session, ADVANCED orchestrator** dispatches `sync-fast` for Stage 3.

## Restart Prompt

```text
Continue upstream sync thread: kamma/threads/20260709_upstream_sync.
Stage 1.5 pull is DONE + verified (314 files: 200 M, 108 D, 53 A; all local files preserved).
A tooling bug in execute_sync.py (no-overlay restore wiping local files) was fixed + committed
(7c2ea4035) before the pull. Target is PINNED to be49bffe (upstream advanced +2 CI-only commits,
deferred; see STAGE-4 TODO to reset accepted_sync ref to "upstream/main" after finalize).
If Commit 1 is not yet committed: present the Commit 1 gate — stage sync content + kamma
bookkeeping, EXCLUDE resources/* (no gitlink change), message
"#sync: upstream pull 518672a6..be49bffe, 363 files, 2026-07-09"; drop the two redundant
sync-rerun* stashes after. Then dispatch sync-fast for Stage 3 §9 recipes + §8 battery + Commit 2.
```
