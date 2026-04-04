# Plan: Implement `/update-upstream` Skill

> **Executing model**: Follow sequentially. Mark tasks `[~]` before starting, `[x]` on
> completion. Do NOT skip steps or invent shortcuts.

---

## Phase 0: Pre-Conditions Check

**Objective:** Verify that all infrastructure from `prepare_update_skill` is in place.

- [ ] **0.1** Verify `kamma/upstream_sync/registry.json` exists and every
  `modified_upstream_files` entry is an object with `path`, `discuss`, `discuss_reason`.
- [ ] **0.2** Run: `uv run python3 kamma/upstream_sync/validate_registry.py` — must pass.
- [ ] **0.3** Run: `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` — must pass.
- [ ] **0.4** Read `kamma/upstream_sync/smd.md` end-to-end. Confirm every registry path
  has a concrete entry with sync rule and numbered local changes.
- [ ] **0.5** Read `kamma/upstream_sync/guide.md` — understand the process reference.

**Phase 0 complete when:** All validators pass and SMD is confirmed complete.

---

## Phase 1: Draft Skill File In-Repo

**Objective:** Write the complete skill as `kamma/upstream_sync/update-upstream.md` for
review before installation.

### 1.1 Header and Iron Rule

- [ ] **1.1.1** Create `kamma/upstream_sync/update-upstream.md` with YAML frontmatter:
  ```yaml
  ---
  description: Run upstream sync — 7 phases, 3 commits, Iron Rule enforced
  ---
  ```
- [ ] **1.1.2** Write the Iron Rule block immediately after frontmatter (bold, unmissable):
  ```
  **🛑 IRON RULE — READ THIS BEFORE EVERY FILE CHANGE**
  When a shadow file breaks after sync, the ONLY fix is:
  1. Open the upstream source
  2. See exactly how upstream solves it
  3. Copy that exact solution
  4. Re-apply ONLY the local changes from kamma/upstream_sync/smd.md

  FORBIDDEN: workarounds, alternative libraries, try/except papering,
  restructuring differently from upstream.
  ```

### 1.2 Phase 0: Pre-flight

- [ ] **1.2.1** Write Phase 0 instructions:
  - Read `kamma/upstream_sync/smd.md` fully — STOP if any entry is incomplete.
  - Read `kamma/upstream_sync/registry.json` fully.
  - Run `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` — STOP if any gaps.
  - Run `uv run python3 kamma/upstream_sync/validate_registry.py` — STOP if any errors.
  - Verify `sbs-ru` branch is clean: `git status` — STOP if dirty, document state.
  - Verify `as_upstream` branch exists: `git branch -a | grep as_upstream`.
  - Create backup tag: `git tag pre-sync-$(date +%Y%m%d)`.

### 1.3 Phase 1: Automated Sync + Commit 1

- [ ] **1.3.1** Write Phase 1 instructions:
  - Run `echo 2 | bash scripts/bash/full_sync.sh` (selective sync mode — syncs tracked
    files, skips `modified_upstream_files` and `no_sync_files`).
  - Run `git submodule init && git submodule update`.
  - Spot-check: run `git diff HEAD -- db/models.py gui2/main.py .gitignore` to verify
    protected files were NOT overwritten.
  - Present full `git diff --stat` to user.
  - **USER APPROVAL GATE**: Wait for explicit "Proceed with Commit 1".
  - Prepare commit message: `sync: automated upstream pull YYYY-MM-DD`
  - Present `git add` + `git commit -m "..."` to user. NEVER run commit yourself.

### 1.4 Phase 2: Dynamic Analysis (PRO Model)

- [ ] **1.4.1** Write Phase 2 instructions:
  - **MODEL SWITCH**: Instruct user to switch to PRO model before starting this phase.
  - Run `git diff HEAD^` to see what changed in the automated sync.
  - For each file in `modified_upstream_files` registry entries: run
    `git diff as_upstream -- <path>` to see what upstream has changed.
  - Cross-reference every changed upstream file against `russian_copies` and
    `sbs_copies` in registry — list ALL shadow destinations.
  - **Triple Shadow Checklist**: Explicitly check `tools/paths.py`,
    `exporter/goldendict/templates/`, `exporter/webapp/templates/`,
    `exporter/goldendict/export_epd.py`. For each, list both shadow destinations.
  - Check `discuss` flags: for every `discuss: true` file, STOP and present
    `git diff as_upstream -- <path>` to user, state the `discuss_reason`, wait for
    decision before including in plan.
  - Output: Create `dynamic_plan.md` in the active thread folder (NOT in
    `kamma/upstream_sync/`) with:
    - Manual Merges: which `modified_upstream_files` changed, what code blocks to port
    - Shadow Updates: each shadow file + exactly what to update + SMD sync rule
    - Documentation: new/updated upstream docs to port to `docs_rus/`
  - **MODEL SWITCH BACK**: Instruct user to switch back to Auto model.

### 1.5 Phase 3: Execution (Auto Model)

- [ ] **1.5.1** Write Phase 3 instructions:
  - Print Iron Rule at start of this phase.
  - Read `dynamic_plan.md` — execute item by item.
  - For each shadow update:
    1. Read the SMD entry for this file from `kamma/upstream_sync/smd.md`.
    2. Read the upstream source file.
    3. Read the current shadow copy.
    4. Apply upstream changes while preserving ONLY the local changes listed in SMD.
    5. Verify namespace isolation (`ru_`, `sbs_`, `dps_` prefixes intact).
  - For each modified upstream file:
    1. Run `git diff as_upstream -- <path>` to see upstream delta.
    2. Manually integrate new upstream features while preserving local elements per SMD.
    3. If `discuss: true`, confirm user already approved in Phase 2.
  - **Dual-Shadow Parity Rule**: When updating one shadow, immediately check if a
    sibling shadow exists (e.g., updating `paths_ru.py` → also check `paths_dps.py`).
    Both must be updated in the same step.
  - Run `uv run pytest tests/test_shadow_parity.py --tb=short -q` after every batch of
    shadow updates.

### 1.6 Phase 4: Logic Audit (PRO Model)

- [ ] **1.6.1** Write Phase 4 instructions:
  - **MODEL SWITCH**: Instruct user to switch to PRO model.
  - For each `modified_upstream_files` entry: compare final state against `as_upstream`
    — verify local changes match SMD exactly, nothing extra introduced.
  - For each updated shadow copy: compare against upstream source — verify structural
    parity.
  - Check all `discuss: true` files got explicit user approval in Phase 2.
  - Verify Iron Rule compliance: no workarounds, no novel solutions, no alternative
    libraries not in upstream.
  - **MODEL SWITCH BACK**: Instruct user to switch back to Auto model.

### 1.7 Phase 5: Testing + Commit 2

- [ ] **1.7.1** Write Phase 5 instructions:
  - Run: `uv run pytest --tb=short -q` (full suite).
  - Run specifically: `uv run pytest tests/test_shadow_parity.py --tb=short -q`.
  - Run: `uv run python3 tests/check_shadow_modifications.py` (standalone script).
  - Run: `uv run ruff check . && uv run ruff format .`
  - Present test results summary to user.
  - **USER MANUAL VERIFICATION**: Ask user to open GoldenDict/webapp and verify
    dictionaries load correctly.
  - **USER APPROVAL GATE**: Wait for explicit "Proceed with Commit 2".
  - Prepare commit message: `sync: manual merge resolutions YYYY-MM-DD`
  - Present `git add` + `git commit -m "..."` to user.

### 1.8 Phase 6: Cleanup + Orphan Archiving

- [ ] **1.8.1** Write Phase 6 instructions:
  - Run `uv run python3 tests/test_shadow_cleanup.py` for each path in
    `folders_to_check` from registry.
  - Identify orphans: files present locally but missing upstream source in `as_upstream`.
  - For each orphan:
    - Still referenced in codebase? → Promote to `unique_paths` in registry.
    - Unused? → Archive: scripts → `scripts/dps_archive/`, other → `archive/dps/`.
  - Update `kamma/upstream_sync/registry.json` with any changes.
  - Root directory audit: `ls -F` on project root — remove any temp artifacts.
  - Update `kamma/upstream_sync/smd.md` if files were added or removed.

### 1.9 Phase 7: Final Verification + Commit 3

- [ ] **1.9.1** Write Phase 7 instructions:
  - Re-run: `uv run pytest --tb=short -q`.
  - Re-run: `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py --tb=short -q`.
  - Run: `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` — must pass.
  - Run: `uv run python3 kamma/upstream_sync/validate_registry.py` — must pass.
  - Run: `uv run ruff check . && uv run ruff format .`
  - Write `kamma/upstream_sync/new_improvements.md` with lessons from this run.
  - Delete `dynamic_plan.md` from the active thread folder (temp artifact).
  - **USER APPROVAL GATE**: Wait for explicit "Proceed with Commit 3".
  - Prepare commit message: `sync: cleanup and finalization YYYY-MM-DD`
  - Present `git add` + `git commit -m "..."` to user.

### 1.10 Discussion flag protocol section

- [ ] **1.10.1** Add a dedicated "Discussion Flag Protocol" section after the Iron Rule:
  - Before touching ANY file in Phase 3, check its `discuss` field in `registry.json`.
  - If `discuss: true`:
    1. STOP. Do not modify the file.
    2. Run `git diff as_upstream -- <path>` and present to user.
    3. State the `discuss_reason` from registry.
    4. Wait for explicit "Approved: [decision]" from user.
    5. Log the decision in `dynamic_plan.md`.
  - Do NOT proceed until user provides explicit instruction.

### 1.11 End-to-end review of draft

- [ ] **1.11.1** Read the complete `kamma/upstream_sync/update-upstream.md` end-to-end.
  Verify:
  - Iron Rule appears at top AND is referenced in Phases 3 and 4.
  - All 3 commit gates have explicit user-approval stops.
  - Discussion flags are enforced before file modification.
  - Triple Shadow Checklist is in Phase 2.
  - `smd.md` is read in Phase 0 and referenced in Phase 3.
  - Model switch instructions are clear in Phases 2 and 4.
  - `dynamic_plan.md` is always placed in the active thread folder, never in `kamma/upstream_sync/`.

**Phase 1 complete when:** `kamma/upstream_sync/update-upstream.md` is complete,
internally consistent, and covers all 7 phases.

---

## Phase 2: Review & Installation

**Objective:** Get explicit user approval for the skill content, then install.

- [ ] **2.1** Present the full draft to user for review. Ask:
  "Does this skill file reflect the workflow you want? Confirm with 'Approved' or provide
  specific feedback."
- [ ] **2.2** PAUSE. Wait for user feedback. Do NOT install without "Approved".
- [ ] **2.3** After approval: copy to `~/.claude/commands/update-upstream.md`.
  - Verify installation: `ls ~/.claude/commands/update-upstream.md`
- [ ] **2.4** Run a quick sanity check: `head -20 ~/.claude/commands/update-upstream.md`
  — confirm Iron Rule is at the top.

**Phase 2 complete when:** Skill installed and Iron Rule confirmed at top of installed file.

---

## Phase 3: Final Handoff

- [ ] **3.1** Run: `uv run python3 kamma/upstream_sync/validate_registry.py` (final check).
- [ ] **3.2** Run: `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` (final check).
- [ ] **3.3** Stage new files:
  ```
  git add kamma/upstream_sync/update-upstream.md kamma/threads.md
  ```
- [ ] **3.4** Present commit message to user:
  ```
  #sync kamma: add /update-upstream skill file
  ```
- [ ] **3.5** Update `kamma/threads.md` — mark this thread `[x]` when complete.

**Phase 3 complete when:** Skill installed, validators pass, commit staged, thread closed.

---

## Files Created/Modified Summary

### New files:
- `kamma/upstream_sync/update-upstream.md` — in-repo skill draft
- `~/.claude/commands/update-upstream.md` — installed skill (after approval)

### Modified files:
- `kamma/threads.md` — thread status update
