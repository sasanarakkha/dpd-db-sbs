# Handoff: Upstream Sync 2026-06-01

## Status

**Stage 3 — Phase A DONE (committed). Phase B.1 DONE. Phase B.2 staged, awaiting USER commit.**

- Phase A: complete, committed (all 6 steps).
- Phase B.1: `execute_sync._check_if_dirty` patched with `--ignore-submodules=dirty`. ruff/pyright/pyrefly clean. `rg` verify: 2 matches ✓
- Phase B.2: all 10 files staged. Pre-sync commit message prepared. Waiting for USER to run commit.

## Current Stage / Next Model

**FAST** — USER must first run the pre-sync commit (see B.2 below), then FAST continues
Phase C → D → E → F. Do NOT re-analyze the blocker; all decisions locked.

## Upstream Range
- From: `44a8a00556cce9bd3874a94efb5dfaceaaf20a66`
- To:   `40083765d770a68b93bfc5e7227b5973e3faf414` (upstream/main, tag v0.4.20260531)

---

## Phase A — DONE (all 6 steps, staged)

1. **A.1 Registry edits** — `kamma/upstream_sync/registry.json`: added `tools/ai_models.json`
   to `no_sync_files`; added 7 dir + 13 file patterns to `skip_sync_patterns`. Side fix:
   removed `db_tests/sbs_consistency_tests.py` from `unique_paths` (the new `db_tests/` dir
   pattern superseded it; fixed a validate_registry overlap error).
2. **A.2 registry_helper.py** — added `get_no_sync_files()`.
3. **A.3 prep_analyzer.py** — imported `get_no_sync_files`; added `self.no_sync_files`;
   `is_skipped()` now checks `no_sync_files` before `skip_patterns`.
4. **A.4** — ruff/pyright/pyrefly clean; `validate_registry.py` PASS; `verify_smd_coverage.py` PASS.
5. **A.5** — prep rerun: `blocker_paths: []` ✓
6. **A.6** — manually set `discuss_paths: []` ✓

### Files staged (ready for pre-sync commit)
- `kamma/threads/20260601_upstream_sync/` (all 6 thread files)
- `kamma/upstream_sync/registry.json`
- `kamma/upstream_sync/scripts/registry_helper.py`
- `kamma/upstream_sync/scripts/prep_analyzer.py`
- `kamma/upstream_sync/scripts/execute_sync.py` (B.1 patch)

---

## Phase B.1 BLOCKER — RESOLVED (ADVANCED, 2026-06-01)

### Diagnosis (verified this session)
- `git status --porcelain --ignore-submodules=dirty` → shows ONLY the staged kamma files;
  zero `resources/*` lines.
- `git submodule status` → NO `+` prefix on any submodule; recorded gitlinks are correct.
- The `" M"` entries are purely submodule-INTERNAL worktree dirt:
  - `resources/bw2`: untracked temp artifact `home/.!69916!engsearch.html`.
  - `resources/sc-data`: many modified tracked files + a deleted `.DS_Store`.
- A superproject commit CANNOT clean this (committing the parent does not commit inside
  submodules) → the original B.2 "porcelain empty" verify was unachievable, and the old
  `_check_if_dirty` (plain `git status --porcelain`) would block `execute_sync` indefinitely.

### Decision: Option 2 — patch `execute_sync._check_if_dirty` with `--ignore-submodules=dirty`
- **Correct by design:** the dirty check protects uncommitted edits to upstream-tracked
  files; submodule internals are opaque to the sync (`git checkout as_upstream -- .` never
  touches submodule worktrees). `--ignore-submodules=dirty` still reports gitlink drift, so
  no real protection is lost.
- **Durable & local:** `execute_sync.py` is under `kamma/` (never synced) → not clobbered.
  (Rejected Option 1 `.gitmodules ignore=dirty` — upstream-tracked, overwritten next sync.)
- **Non-destructive:** does NOT touch the unknown `sc-data` modifications (rejected Option 3
  manual cleaning — risky, out of scope). Option 4 (re-staging gitlinks) is a no-op.
- Literal edit is written in `dynamic_plan.md` → Phase B.1.

---

## Decisions (all LOCKED, do NOT re-ask)
- A1 db/models.py → PORT (D.1). A2 .gitignore → MERGE (D.2). A3 AGENTS.md → SKIP.
- Prep blocker_paths → no_sync_files code fix (Phase A) — DONE.
- Dirty-submodule blocker → Option 2 (`--ignore-submodules=dirty` in execute_sync) — B.1.
- C tools/ai_models.json → no_sync_files — DONE.
- pass2_add_view.py → PORT (D.10). D.11 export_dpd exitcode → YES (apply).
- Skips (prose only, no ledger): home.html RSS, paths_ru/dps attrs, mkdocs_ru custom_dir +
  Anki nav (Stage 4), ru_static.yml RSS + uv modernization.

## Files changed this session (FAST B.1)
- `kamma/upstream_sync/scripts/execute_sync.py` — B.1 patch (`--ignore-submodules=dirty`)
- `kamma/threads/20260601_upstream_sync/handoff.md` — this update

## Files changed prior sessions (staged, included in B.2 commit)
- `kamma/upstream_sync/registry.json` — A.1
- `kamma/upstream_sync/scripts/registry_helper.py` — A.2
- `kamma/upstream_sync/scripts/prep_analyzer.py` — A.3
- `kamma/threads/20260601_upstream_sync/prep_manifest.json` — A.6
- `kamma/threads/20260601_upstream_sync/dynamic_plan.md` — ADVANCED corrections

## Errors, Issues, and Repeated Mistakes
- **Prior handoff A1 anchors were WRONG** (sc_link/dv_exists neighbors). Corrected Stage 2.
- `ruff --select E999` removed in current ruff; plan task 1.1 references `F821,E999` — drop E999.
- `resources/fdg_dpd` submodule fetch fails (remote not found) — pre-existing, not a blocker.
- Manifest `mapped_actions[].local_target_path` wrong for renamed goldendict shadows — D.6 uses real paths.
- execute_sync has no discuss-acknowledge flag — manual `discuss_paths:[]` edit required.
- A.1 registry edit caused validate_registry overlap (`db_tests/` vs the specific unique_path
  entry); fixed by removing the specific entry. Not in original plan.
- **Dirty submodule blocker** (NOW RESOLVED): `git submodule update --init --recursive` does
  not clean submodule internal worktree dirt; the parent commit cannot either. Fixed by
  `--ignore-submodules=dirty` in `execute_sync._check_if_dirty` (B.1). Submodule dirt is
  pre-existing and intentionally left untouched.

## Open items for next session (FAST)
1. **B.2 USER COMMIT (first thing):** confirm the user has run:
   `git commit -m "#pre-sync: clear sync blockers, ack discuss, 2026-06-01"`
   Then verify: branch is `sbs-ru` and `git status --porcelain --ignore-submodules=dirty` is EMPTY.
   (Bare `git status --porcelain` will still list ` M resources/*` — that is expected submodule dirt, ignore it.)
2. **Phase C:** `uv run python3 kamma/upstream_sync/scripts/execute_sync.py kamma/threads/20260601_upstream_sync` → C.2 git rm 3 files → C.3 stage + USER commit.
3. **Phase D:** manual ports D.1–D.11, item by item per dynamic_plan.md.
4. **Phase E:** verification suite.
5. **Phase F:** `git add .` + USER commit `#sync: manual merge resolutions 2026-06-01`.

## Next Model
**FAST.**

## Restart Prompt
```text
Start a fresh session.

Continue upstream sync thread: kamma/threads/20260601_upstream_sync.

First read:
1. kamma/threads/20260601_upstream_sync/handoff.md
2. kamma/threads/20260601_upstream_sync/dynamic_plan.md

Phase A is DONE (committed). Phase B.1 is DONE (execute_sync.py patched). Phase B.2 files
are staged — the USER still needs to run the pre-sync commit. Ask the user to confirm they
have run:

  git commit -m "#pre-sync: clear sync blockers, ack discuss, 2026-06-01"

Then verify branch=sbs-ru and git status --porcelain --ignore-submodules=dirty is empty.
Then proceed Phase C → D → E → F literally, item by item from dynamic_plan.md. All commits
are USER-RUN. Stop and ask only if a plan anchor is missing or a test fails in a way the
plan does not cover.
```

Do not continue in this session.
