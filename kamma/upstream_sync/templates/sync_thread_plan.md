# Plan: Upstream Sync <DATE>

> **Executing model**: Follow sequentially. Mark tasks `[~]` before starting, `[x]` on
> completion. Do NOT skip steps or invent shortcuts.

---

## ⛔ IRON RULE — READ THIS BEFORE EVERY FILE CHANGE

**When a shadow file breaks after sync, the ONLY permitted fix is:**
1. Open the upstream source file.
2. See exactly how upstream implements the broken functionality.
3. Copy that exact solution into the shadow.
4. Re-apply ONLY the local changes listed in `kamma/upstream_sync/smd.md` for that file.

**FORBIDDEN:**
- Workarounds not present in upstream.
- Alternative libraries or imports not in the upstream source.
- `try/except` papering over the real issue.
- Restructuring that differs from upstream structure.

**The upstream sources are correct and carefully tested.
If something is broken, the sync is incomplete or inaccurate — not the source.**

---

## Discussion Flag Protocol

Before touching ANY file in Phase 3, check its `discuss` field in `registry.json`.

If `discuss: true`:
1. **STOP.** Do not modify the file.
2. Run `git diff as_upstream -- <path>` and present the full diff to the user.
3. State the `discuss_reason` from the registry entry.
4. Wait for explicit **"Approved: [decision]"** from the user.
5. Log the decision in `dynamic_plan.md`.

Do NOT proceed past this gate without explicit user approval.

---

## Phase 0: Pre-flight

- [ ] **0.1** `git status` — must be clean. If dirty, document state in `handoff.md` and STOP.
- [ ] **0.2** Verify `git branch -a | grep as_upstream` — the `as_upstream` tracking branch must exist.
- [ ] **0.3** Create a backup tag: `git tag pre-sync-<DATE>`.
- [ ] **0.4** `uv run python3 kamma/upstream_sync/validate_registry.py` — must pass.
- [ ] **0.5** `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` — must pass. If any gaps, STOP and fix them before continuing.
- [ ] **0.6** Read `kamma/upstream_sync/smd.md` end-to-end. Confirm every entry has concrete numbered local changes. If any entry is a stub, STOP.
- [ ] **0.7** Read `kamma/upstream_sync/guide.md` to refresh merge strategy definitions.

**Phase 0 complete when:** Worktree clean, `as_upstream` exists, tag created, both validators pass, SMD confirmed complete.

---

## Phase 1: Automated Sync + Commit 1

- [ ] **1.1** Run `echo 2 | bash scripts/bash/full_sync.sh` (selective sync: syncs tracked upstream files, skips `modified_upstream_files` and `no_sync_files`).
- [ ] **1.2** Run `git submodule init && git submodule update`.
- [ ] **1.3** Spot-check: `git diff HEAD -- db/models.py gui2/main.py .gitignore AGENTS.md` — verify these protected files were NOT overwritten.
- [ ] **1.4** Present full `git diff --stat` to user.
- [ ] **1.5** ⛔ **USER APPROVAL GATE** — STOP. Wait for explicit **"Proceed with Commit 1"**.
- [ ] **1.6** Present to user (do NOT run yourself):
  ```
  git add <files>
  git commit -m "sync: automated upstream pull <DATE>"
  ```

**Phase 1 complete when:** User has approved and run Commit 1.

---

## Phase 2: Dynamic Analysis

> ⚡ **MODEL SWITCH**: Ask user to switch to **Higher model** before starting this phase.
> Switch back to Auto after Phase 2 is complete.

- [ ] **2.1** Run `git diff HEAD^` to see what changed in the automated sync.
- [ ] **2.2** For each file in `modified_upstream_files`: run `git diff as_upstream -- <path>` to see the upstream delta since last sync.
- [ ] **2.3** Cross-reference every changed upstream file against `russian_copies` and `sbs_copies` in `registry.json` — list ALL shadow destinations for each changed source.
- [ ] **2.4** **Triple Shadow Checklist** — explicitly check these high-risk files:
  - `tools/paths.py` → `tools/paths_ru.py` AND `tools/paths_dps.py`
  - `exporter/goldendict/templates/` → `ru_components/templates/` AND `sbs_templates/`
  - `exporter/webapp/templates/` → `ru_templates/` AND `sbs_templates/`
  - `exporter/goldendict/export_epd.py` → `export_epd_sbs.py`
  For each, confirm both shadow destinations are in the port list.
- [ ] **2.5** For every `discuss: true` entry that changed: STOP, present `git diff as_upstream -- <path>`, state the `discuss_reason`, wait for decision before including in plan.
- [ ] **2.6** Create `dynamic_plan.md` in THIS thread folder (NOT in `kamma/upstream_sync/`) containing:
  - **Manual Merges**: which `modified_upstream_files` changed, exact code blocks to port.
  - **Shadow Updates**: each shadow file + exactly what to update + SMD sync rule.
  - **Documentation**: new/updated upstream docs to port to `docs_rus/`.

> ⚡ **MODEL SWITCH BACK**: Ask user to switch back to **Lower model**.

**Phase 2 complete when:** `dynamic_plan.md` written and covers every changed upstream file. All `discuss: true` decisions logged.

---

## Phase 3: Execution

> Print Iron Rule again at the start of this phase before touching any file.

- [ ] **3.1** Read `dynamic_plan.md` — execute item by item. Do NOT skip items or reorder.
- [ ] **3.2** For each **shadow update** item:
  1. Read the SMD entry for this file from `kamma/upstream_sync/smd.md`.
  2. Read the upstream source file (`git show as_upstream:<path>` or read the file).
  3. Read the current shadow copy.
  4. Apply upstream changes exactly. Then re-apply ONLY the local changes listed in SMD.
  5. Verify namespace isolation: `ru_` / `sbs_` / `dps_` prefixes are intact on all IDs, CSS classes, and JS variable names.
- [ ] **3.3** For each **modified upstream file** item:
  1. Run `git diff as_upstream -- <path>` to isolate the upstream delta.
  2. Integrate new upstream features while preserving local elements listed in SMD.
  3. If `discuss: true`, confirm user approval was logged in `dynamic_plan.md` before touching the file.
- [ ] **3.4** **Dual-Shadow Parity Rule**: whenever a shadow is updated, immediately check if a sibling exists (e.g., `paths_ru.py` → also check `paths_dps.py`). Both must be updated in the same step.
- [ ] **3.5** After each batch of shadow updates: `uv run pytest tests/test_shadow_parity.py --tb=short -q` — keep green throughout.

**Phase 3 complete when:** All `dynamic_plan.md` items executed. Shadow parity tests green.

---

## Phase 4: Logic Audit

> ⚡ **MODEL SWITCH**: Ask user to switch to **Higher model** before starting this phase.
> Switch back to Auto after Phase 4 is complete.

- [ ] **4.1** For each `modified_upstream_files` entry updated: compare final state against `as_upstream` — verify local changes match SMD exactly and nothing extra was introduced.
- [ ] **4.2** For each updated shadow copy: compare against upstream source — verify structural parity (same function order, same logic flow, only listed SMD additions present).
- [ ] **4.3** Check all `discuss: true` files — confirm explicit user approval was logged in Phase 2.
- [ ] **4.4** Iron Rule compliance check: no workarounds, no novel solutions, no alternative libraries not in upstream.

> ⚡ **MODEL SWITCH BACK**: Ask user to switch back to **Lower model**.

**Phase 4 complete when:** Audit complete. All deviations from upstream are SMD-listed local changes only.

---

## Phase 5: Testing + Manual Verification + Commit 2

### Automated tests first

- [ ] **5.1** `uv run pytest --tb=short -q` — full suite must pass.
- [ ] **5.2** `uv run pytest tests/test_shadow_parity.py --tb=short -q` — must pass.
- [ ] **5.3** `uv run python3 tests/check_shadow_modifications.py` — must succeed.
- [ ] **5.4** `uv run ruff check . && uv run ruff format .` — zero errors.
- [ ] **5.5** Present test results summary to user.

### Manual verification gate

- [ ] **5.6** ⛔ **MANUAL VERIFICATION GATE** — STOP completely. Ask user to:
  - Open GoldenDict / webapp and verify dictionaries load correctly.
  - Check one Russian entry and one SBS entry for correct data display.
  - Report any errors or anomalies.

> **When errors are reported by the user:**
> 1. **DO NOT invent a new solution.**
> 2. Open the upstream source file for the broken functionality.
> 3. Read exactly how upstream implements it.
> 4. Port that exact implementation to the shadow.
> 5. Re-apply ONLY the SMD-listed local changes.
> 6. Re-run automated tests.
> 7. Present results — do NOT assume fixed without confirmation.
> Repeat until the user explicitly confirms the issue is resolved.

- [ ] **5.7** ⛔ **USER APPROVAL GATE** — Wait for explicit **"Proceed with Commit 2"**.
- [ ] **5.8** Present to user (do NOT run yourself):
  ```
  git add <files>
  git commit -m "sync: manual merge resolutions <DATE>"
  ```

**Phase 5 complete when:** All automated tests pass, user confirmed manual verification, user has run Commit 2.

---

## Phase 6: Cleanup + Orphan Archiving

- [ ] **6.1** `uv run python3 tests/test_shadow_cleanup.py --dry-run` — review all orphans.
- [ ] **6.2** For each orphan identified:
  - Still referenced in codebase? → Promote to `unique_paths` in `registry.json`.
  - Unused? → Archive: scripts → `scripts/dps_archive/`, other files → `archive/dps/`.
- [ ] **6.3** `ls -F` on project root — remove any temp artifacts.
- [ ] **6.4** Update `kamma/upstream_sync/registry.json` with any promotions or removals from 6.2.
- [ ] **6.5** Update `kamma/upstream_sync/smd.md` if any files were added or removed during cleanup.

**Phase 6 complete when:** No unresolved orphans. Registry and SMD reflect current state.

---

## Phase 7: Final Verification + Improvements + Commit 3

- [ ] **7.1** `uv run pytest --tb=short -q` — full suite.
- [ ] **7.2** `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py --tb=short -q`.
- [ ] **7.3** `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` — 0 gaps.
- [ ] **7.4** `uv run python3 kamma/upstream_sync/validate_registry.py` — passes.
- [ ] **7.5** `uv run ruff check . && uv run ruff format .` — zero errors.
- [ ] **7.6** Write `kamma/upstream_sync/new_improvements.md`:
  - New pitfalls encountered not in `archive_improvements.md`.
  - SMD corrections discovered (also update `smd.md` directly).
  - Patterns that should change the sync process itself.
  If nothing new: write a brief "no new learnings — sync went cleanly" note.
- [ ] **7.7** Delete `dynamic_plan.md` from this thread folder (temp artifact — do NOT commit it).
- [ ] **7.8** ⛔ **USER APPROVAL GATE** — Wait for explicit **"Proceed with Commit 3"**.
- [ ] **7.9** Present to user (do NOT run yourself):
  ```
  git add <files>
  git commit -m "sync: cleanup and finalization <DATE>"
  ```

**Phase 7 complete when:** All validators pass. `new_improvements.md` written. Commit 3 staged and presented.
