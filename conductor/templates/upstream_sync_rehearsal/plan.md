# Plan: Upstream Sync Rehearsal (Standard Monthly)

## Phase 1: Automated Synchronization (Auto)
- [ ] Task: Pre-Sync Branch Check
    - [ ] Verify there are no uncommitted changes in the `sbs-ru` branch.
- [ ] Task: Execute Sync Script
    - [ ] Run `bash scripts/cl_dps/dpd-sync-folders`.
    - [ ] Select **Option 2 (Selective Sync)**.
    - [ ] **Update Submodules**: Run `git submodule init && git submodule update`.
    - [ ] **AUTO-COMMIT (COMMIT 1/2)**: The sync script performs an automated commit here.
- [ ] Task: Conductor - User Manual Verification 'Automated Synchronization'

## Phase 2: Analysis & Dynamic Planning (PRO)
- [ ] **🛑 MANDATORY MODEL SWITCH: PRO** (Ask user to switch).
- [ ] Task: Semantic Analysis
    - [ ] Analyze `git diff HEAD^` and `modified_upstream_files`.
    - [ ] Check upstream sources for all shadow copies.
- [ ] Task: Create Dynamic Spec
    - [ ] Write `dynamic_sync_plan.md` with precise instructions for the Auto model.
- [ ] **🛑 MANDATORY MODEL SWITCH: AUTO** (Ask user to switch back).

## Phase 3: Implementation (Auto)
- [ ] **🛑 NO COMMITS ALLOWED IN THIS PHASE.**
- [ ] Task: Execute Dynamic Plan
    - [ ] Follow instructions in `dynamic_sync_plan.md`.
- [ ] Task: Update Shadow Copies
    - [ ] **Check Render Parity**: Verify all variables passed to `render()` in upstream match the shadow copies.
    - [ ] **Check Import Parity**: Verify new upstream imports are present in shadow copies.
    - [ ] **Check Kindle/OPF Metadata**: Verify `content.opf` structure matches upstream requirements.
    - [ ] **Check for New Upstream Files**: Run `git ls-files exporter/goldendict/templates/` (and other source dirs) to catch new templates that need Russian/SBS counterparts.
- [ ] Task: Documentation Parity
    - [ ] Ensure documentation parity between docs/ and docs_rus/.
- [ ] Task: Update Rehearsal Templates
    - [ ] Sync `dps_sync_registry.json` and `guide.md` with the new state.

## Phase 4: Final Logic Audit (PRO)
- [ ] **🛑 MANDATORY MODEL SWITCH: PRO** (Ask user to switch).
- [ ] Task: PRO Logic Audit
    - [ ] **AGENT ACTION**: Use PRO model to manually audit EVERY modified file and shadow copy against upstream originals.
- [ ] **🛑 MANDATORY MODEL SWITCH: AUTO** (Ask user to switch back).

## Phase 5: Finalization & Verification (Auto)
- [ ] Task: Run All Tests
    - [ ] Run imports, exporters, docs parity, and new feature tests.
    - [ ] Run `python3 tests/test_template_structure.py` to verify template structural parity.
- [ ] Task: **🛑 FINAL USER APPROVAL GATE**
    - [ ] **HARD STOP**: Agent presents a summary of all changes.
    - [ ] **AWAIT SIGNAL**: "Phase 5 is complete" or "Proceed with final commit".
- [ ] Task: **FINAL MANUAL COMMIT (COMMIT 2/2)**
    - [ ] Perform ONE consolidated commit for all manual work.
    - [ ] Message: `sync: manual merge resolutions and comprehensive validation (DD-MM)`.
- [ ] **Task: Exporter Verification**
    - [ ] Verify GoldenDict SBS/Ru exports manually.
    - [ ] Verify Kindle Ru export manually.
    - [ ] Verify Webapp (Ru/SBS) manually.
- [ ] **Task: GUI Verification**
    - [ ] Verify GUI2 functionality (DpsView, Fonts, Tabs, Hotkeys).
- [ ] **Task: Final Confirmation**
    - [ ] User provides final confirmation: "Track is complete".
