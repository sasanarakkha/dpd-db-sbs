# Plan: Upstream Sync Rehearsal (Standard Monthly)

## Phase 1: Automated Synchronization
- [ ] Task: Pre-Sync Branch Check
    - [ ] Verify there are no uncommitted changes in the `sbs-ru` branch.
- [ ] Task: Execute Sync Script
    - [ ] Run `bash scripts/cl_dps/dpd-sync-folders`.
    - [ ] Select **Option 2 (Selective Sync)**.
    - [ ] **Update Submodules**: Run `git submodule init && git submodule update`.
    - [ ] **AUTO-COMMIT (COMMIT 1/2)**: The sync script performs an automated commit here.
- [ ] Task: Conductor - User Manual Verification 'Automated Synchronization'

## Phase 2: Manual Merge & Shadow Porting
- [ ] **🛑 NO COMMITS ALLOWED IN THIS PHASE.** All changes must be staged.
- [ ] Task: Integrate Upstream Updates into Modified Files
    - [ ] Run `git diff as_upstream <file>` for all `modified_upstream_files`.
    - [ ] Port relevant bug fixes or new features.
- [ ] Task: Update Shadow Copies
    - [ ] For each entry in `russian_copies` and `sbs_copies`:
        - [ ] Port logic from source to shadow.
- [ ] Task: Documentation Parity
    - [ ] Ensure documentation parity between docs/ and docs_rus/.
- [ ] Task: Update Rehearsal Templates
    - [ ] Sync `dps_sync_registry.json` and `guide.md` with the new state.

## Phase 3: Final Logic Audit & Validation
- [ ] **🛑 NO COMMITS ALLOWED UNTIL FINAL APPROVAL.**
- [ ] **MANDATORY MODEL SWITCH**: Ask user to switch to **PRO model** via `/model`.
- [ ] Task: PRO Logic Audit
    - [ ] **AGENT ACTION**: Use PRO model to manually audit EVERY modified file and shadow copy against upstream originals.
- [ ] **MANDATORY SWITCH BACK**: Ask user to switch back to **Auto** via `/model`.
- [ ] Task: Run All Tests
    - [ ] Run imports, exporters, docs parity, and new feature tests.
- [ ] Task: **🛑 FINAL USER APPROVAL GATE**
    - [ ] **HARD STOP**: Agent presents a summary of all changes.
    - [ ] **AWAIT SIGNAL**: "Phase 3 is complete" or "Proceed with final commit".
- [ ] Task: **FINAL MANUAL COMMIT (COMMIT 2/2)**
    - [ ] Perform ONE consolidated commit for all manual work.
    - [ ] Message: `sync: manual merge resolutions and comprehensive validation (DD-MM)`.
- [ ] **Task: Comprehensive Summary**
    - [ ] Agent provides a detailed summary of all technical changes, protocol updates, and test results for the entire session.

## Phase 4: Manual User Verification
- [ ] **Task: Exporter Verification**
    - [ ] Verify GoldenDict SBS/Ru exports manually.
    - [ ] Verify Kindle Ru export manually.
    - [ ] Verify Webapp (Ru/SBS) manually.
- [ ] **Task: GUI Verification**
    - [ ] Verify GUI2 functionality (DpsView, Fonts, Tabs, Hotkeys).
- [ ] **Task: Final Confirmation**
    - [ ] User provides final confirmation: "Track is complete".
