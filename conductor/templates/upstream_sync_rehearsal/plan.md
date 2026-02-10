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
- [ ] Task: Documentation & Cleanup
    - [ ] Ensure documentation parity and remove orphaned files.
- [ ] Task: Update Rehearsal Templates
    - [ ] Sync `dps_sync_registry.json` and `guide.md` with the new state.

## Phase 3: Final Logic Audit & Validation
- [ ] **🛑 NO COMMITS ALLOWED UNTIL FINAL APPROVAL.**
- [ ] Task: PRO Logic Audit
    - [ ] **AGENT ACTION**: Use PRO model to manually audit EVERY modified file and shadow copy against upstream originals.
    - [ ] Verify that no structural improvements were missed during Phase 2.
- [ ] Task: Run All Tests
    - [ ] Run imports, exporters, docs parity, and new feature tests.
- [ ] Task: Final Manual System Check
    - [ ] Confirm DPS-specific UI features are intact.
- [ ] Task: **🛑 FINAL USER APPROVAL GATE**
    - [ ] **HARD STOP**: Agent presents a summary of all changes.
    - [ ] **AWAIT SIGNAL**: "Phase 3 is complete" or "Proceed with final commit".
- [ ] Task: **FINAL MANUAL COMMIT (COMMIT 2/2)**
    - [ ] Perform ONE consolidated commit for all manual work.
    - [ ] Message: `sync: manual merge resolutions and comprehensive validation (DD-MM)`.
- [ ] Task: Conductor - User Manual Verification 'Final Validation & Checkpoint'