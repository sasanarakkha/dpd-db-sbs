# Plan: Upstream Sync Rehearsal (Standard Monthly)

## Phase 1: Automated Synchronization
- [ ] Task: Pre-Sync Branch Check
    - [ ] Verify there are no uncommitted changes in the `sbs-ru` branch.
    - [ ] If changes exist, inform the user and request a commit before proceeding.
- [ ] Task: Execute Sync Script
    - [ ] Run `bash scripts/cl_dps/dpd-sync-folders` from the project root.
    - [ ] Select **Option 2 (Selective Sync)** when prompted.
    - [ ] Verification: Confirm the script completes and performs a "selective update" commit.
- [ ] Task: Verify Post-Sync Hooks
    - [ ] Ensure `gui2/font_scaling_helper.py` was executed as part of the script.
    - [ ] Verification: Open the GUI and check that font sizes in the Search and Pass2Add views are correctly scaled.
- [ ] Task: Commit Phase 1 Results
    - [ ] **AWAIT USER APPROVAL** before committing.
    - [ ] Commit all sync updates.
- [ ] Task: Conductor - User Manual Verification 'Automated Synchronization' (Protocol in workflow.md)

## Phase 2: Manual Merge & Logic Porting
- [ ] Task: Integrate Upstream Updates into Modified Files
    - [ ] Compare `sbs-ru` versions against `as_upstream` for all files in `modified_upstream_files`.
    - [ ] Manually port relevant bug fixes or new features.
    - [ ] **AWAIT USER APPROVAL** for the merged state of these files.
- [ ] Task: Update Shadow Copies
    - [ ] For each entry in `russian_copies` and `sbs_copies`:
        - [ ] Compare shadow copy with its source and port necessary logic.
    - [ ] **AWAIT USER APPROVAL** for the updated shadow copies.
- [ ] Task: Validate Removed Upstream Files
    - [ ] Identify files in `folders_to_check` removed from upstream.
    - [ ] Clean up unused orphans or preserve required logic in `unique_paths`.
    - [ ] **AWAIT USER APPROVAL** for the cleanup/preservation strategy.
- [ ] Task: Documentation Parity Check
    - [ ] Check `docs/` for new English documentation and create counterparts in `docs_rus/`.
    - [ ] **AWAIT USER APPROVAL** for the documentation updates.
- [ ] Task: Update Rehearsal Templates
    - [ ] Based on the changes made, update `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json` and `guide.md` to reflect the new state and any new shadow copies or modified files identified.
- [ ] Task: Commit Phase 2 Results
    - [ ] Commit all manual merge resolutions and template updates.
- [ ] Task: Conductor - User Manual Verification 'Manual Merge & Logic Porting' (Protocol in workflow.md)

## Phase 3: Final Validation & Checkpoint
- [ ] Task: Run Baseline Verification Tests
    - [ ] Run `uv run pytest tests/test_dps_imports.py`
    - [ ] Run `uv run pytest tests/test_dps_logic.py`
    - [ ] Run `uv run pytest tests/test_dps_exporters_functional.py`
    - [ ] Run `uv run pytest tests/test_dps_docs_parity.py`
- [ ] Task: Expand Test Suite
    - [ ] Analyze upstream changes and identify areas requiring new tests to prevent future regressions.
    - [ ] Implement new tests in the `tests/` directory.
- [ ] Task: Comprehensive System Check
    - [ ] Run `uv run pytest`.
    - [ ] Manually verify that DPS-specific features (DpsView, SBS examples in GoldenDict) are still functional.
- [ ] Task: Final Commit
    - [ ] Commit any new tests.
    - [ ] Suggested message: `sync: final validation and expanded testing (DD-MM)`.
- [ ] Task: Conductor - User Manual Verification 'Final Validation & Checkpoint' (Protocol in workflow.md)
