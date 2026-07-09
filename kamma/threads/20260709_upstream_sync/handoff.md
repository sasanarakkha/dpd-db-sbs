# Handoff: Upstream Sync 2026-07-09

## Status

**Stage 1.5 pull DONE + verified; Commit 1 LANDED (`699c10cd1`).** Next: a **fresh Opus session**
runs Stage 3 (ADVANCED orchestrator dispatching `haiku` sync-fast subagents). Stage 2 was
COMPLETE + APPROVED in a prior session. Tree is clean at Commit 1; three redundant session stashes
remain to drop (see below).

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

## COMMIT 1 — LANDED (`699c10cd1`)

`#sync: upstream pull 518672a6..be49bffe, 363 files, 2026-07-09` (255 add/modify + 108 delete,
excluding `resources/*`; kamma bookkeeping folded in). Committed with **`--no-verify` (user-approved)**
— see Future-Sync Improvements #4. Pristine index committed; ruff worktree-noise stashed off.

**THREE redundant session stashes to drop** (all safe — hold now-committed upstream files or hook
noise): `ruff-worktree-noise-20260709`, `sync-rerun2-20260709`, `sync-rerun-20260709`.
`git stash drop` each. **The other `stash@{...}` WIP entries belong to the USER — DO NOT touch.**
(Left undropped this session because tree-wide/stash destructive ops need explicit user naming.)

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

## ⭐ FUTURE-SYNC IMPROVEMENTS (from this session — MUST be actioned in Stage 4 retrospective)

Everything below was surfaced this run. Each is a concrete improvement to the sync **tooling**,
**guide**, or **process**. Promote accepted items to `archive_improvements.md` at Stage 4.

### 1. `execute_sync.py` no-overlay restore DELETED all local files (CRITICAL — fixed `7c2ea4035`)
- **Problem:** step 5 used `git restore --source as_upstream --worktree -- .`. The no-overlay
  default DELETES every tracked file absent from upstream → wiped ~2780 local-only files (shadows,
  `unique_paths`, `inspired_by`, all local data TSVs, `russian_words_user_dict.txt`). Regression
  introduced at `33ed53d34` (2026-06-11, `git checkout as_upstream -- .` → `git restore …`); never
  caught because the last sync (2026-06-13) was driven manually in batches, so the automated
  `restore` path's first real execution was THIS run.
- **Fix applied:** `git restore --overlay …` (preserves local-only files, still updates/creates
  upstream paths, still worktree-only/unstaged). Verified in an isolated repo.
- **Still to do (Stage 4):** add a **regression test** — build a tiny repo with a local-only tracked
  file, run the restore step, assert the local file survives AND an upstream-changed file updates
  AND changes stay unstaged. Consider a `smoke_test_sync.py`-level check that exercises
  `execute_sync.py` end-to-end against a fixture so any future restore/overlay regression fails CI.

### 2. `execute_sync.py` has NO worktree rollback on partial failure (HIGH)
- **Problem:** when step 5 wiped the tree, the `except` block only calls
  `context.restore_original_state()` which restores the **branch**, not the **worktree**. The
  destroyed worktree was left in place; recovery was manual (`git checkout HEAD -- .`). Only luck
  (changes are worktree-only, never committed/staged, HEAD intact) made recovery possible.
- **Improvement:** wrap the mutating steps (5–6b) so that ANY failure restores the worktree to the
  pre-run `sbs_ru_original_sha` (e.g. snapshot via a temp stash/commit, or `git checkout
  <original_sha> -- .` on failure). The unstaged/worktree-only design is GOOD and must be preserved
  — but failure must auto-rollback, not leave a half-wiped tree.

### 3. Upstream advancing MID-SYNC has no clean documented procedure (MEDIUM)
- **Problem:** `execute_sync.py` runs `git fetch upstream` internally and re-resolves the MOVING ref
  `upstream/main`. Between Stage-2 approval and the pull, upstream added 2 commits, so the target
  drifted past the approved/analyzed SHA. The manifest gate correctly blocked, but pinning required
  hand-editing **two** files (`accepted_sync.json.last_accepted_upstream_ref` AND
  `prep_manifest.json.target_upstream_ref`) PLUS remembering a Stage-4 reset (finalize derives the
  next ref from `manifest.target_upstream_ref`). Fragile and undocumented.
- **Improvement options:** (a) `verify_manifest`/`execute_sync` should target
  `manifest.to_upstream_sha` (the analyzed pinned SHA) directly rather than re-`rev-parse` the moving
  ref — the analysis pinned a SHA, the pull should honor it; (b) add a documented `--pin` helper or a
  guide recipe for "upstream advanced mid-sync"; (c) surface the Stage-4 ref-reset automatically so it
  can't be forgotten. See PIN NOTE above for the exact two-file edit used this run.

### 4. Pre-commit hooks BLOCK Commit 1 (verbatim upstream) — `--no-verify` needed but undocumented (MEDIUM)
- **Problem:** Commit 1 is by design the **verbatim upstream pull**, but the fork's pre-commit
  `ruff`/`pyright`/`pyrefly` hooks lint that raw code: `ruff check --fix` auto-modified **202**
  upstream files in the worktree and reported **21** unfixable errors → commit aborted. Letting the
  hooks run corrupts the pristine baseline Stage 3 must diff against. Resolved by `--no-verify`
  (user-approved) committing the pristine index, then stashing off the ruff worktree-noise.
- **Conflict:** the project rule "**never `--no-verify`**" targets normal fork work, but the
  raw-upstream Commit 1 is a legitimate exception. This is NOT documented anywhere.
- **Improvement:** document in `guide.md` that **Commit 1 uses `--no-verify`** (raw upstream is
  accepted verbatim; lint/type standards apply to fork/shadow code in Stage 3, not the raw drop).
  Better: a pre-commit config that **skips hooks for the sync-pull commit** (e.g. env guard or a
  dedicated commit path) so `--no-verify` isn't a manual step. Note the guide already says
  `archive/`/`scripts/archive/` are "never linted" — extend that principle to the whole Commit-1 drop.

### 5. `execute_sync.py` dirty-guard + `git stash -u` interaction (MEDIUM)
- **Problem A:** the dirty-guard counts **untracked** files, so leftovers from a failed pull block
  the re-run. Recovering from a partial failure requires manually clearing untracked upstream files
  before retrying — awkward and error-prone (a naive tree-wide `rm`/`clean` risks pre-existing local
  data).
- **Problem B:** `git stash --include-untracked` also **swallows uncommitted tracked changes** — this
  silently stashed the in-flight `--overlay` fix, so two pulls ran the OLD code. Root lesson: **any
  tooling fix must be COMMITTED before running the pull** (the guard demands a clean tree, so the fix
  can't ride along uncommitted).
- **Improvement:** (a) make `execute_sync.py` **idempotent/resumable** — on a clean-but-for-its-own-
  prior-additions tree, clean up its own untracked upstream additions rather than blocking; (b) the
  guard could ignore untracked (it exists to protect uncommitted tracked edits, per its docstring);
  (c) guide note: commit tooling fixes first; use `git stash push -- <path>` scoped, not bare
  `stash -u`, when a fix is in flight.

### 6. Operational lessons (process, not tooling)
- `git checkout <stash> --` with an EMPTY pathspec **detaches HEAD** to the stash commit. Never run
  ambiguous `checkout <ref> --`; reattach with `git checkout sbs-ru`.
- The auto-mode classifier blocks tree-wide destructive ops (`rm -rf` loops, `git checkout -- .`,
  `git clean -fd`). Use **reversible** cleanup (`git stash push`) instead of hard deletes; it clears
  the guard AND is recoverable. (This is why 3 redundant stashes remain — dropping them also needs
  explicit user naming.)
- Dirty `resources/*` submodules are NOT commit scope unless a gitlink (recorded SHA) actually
  changed — verify with `git diff HEAD -- resources/ | grep 'Subproject commit'` (SHA change vs
  mere `-dirty` suffix). This run: no gitlink change, all excluded.
- **What saved every near-miss:** `execute_sync.py` leaves changes worktree-only/unstaged and never
  touches HEAD. Preserve this invariant at all costs — it's the entire recovery margin.

### 7. Carried retrospective candidates (from prior handoff)
- stage1 lint gate fixes; `tests/kamma` rename; "never name a `tests/` subpackage after a top-level
  repo package" (`tests/exporter/` still shadows root `exporter/`).
- prep_analyzer local-commit sweep caught unregistered locally-modified upstream files
  (`ai_models.json`, example_bolding fix) the registry missed — consider folding the sweep into
  `prep_analyzer.py`.
- `skill_scope_improvement.md` — guide/skill fixes surfaced during 2b scope correction; apply as a
  SEPARATE post-sync task (do NOT act during this sync).

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
