# Plan: Upstream Sync Rehearsal (Standard Monthly)

## Phase 1: Automated Synchronization
- [x] Task: Pre-Sync Branch Check
    - [x] Verify there are no uncommitted changes in the `sbs-ru` branch.
    - [x] If changes exist, inform the user and request a commit before proceeding.
- [x] Task: Execute Sync Script
    - [x] Run `bash scripts/cl_dps/dpd-sync-folders` from the project root.
    - [x] Select **Option 2 (Selective Sync)** when prompted.
    - [x] Verification: Confirm the script completes and performs a "selective update" commit.
- [x] Task: Verify Post-Sync Hooks
    - [x] Ensure `gui2/font_scaling_helper.py` was executed as part of the script.
    - [x] Verification: Open the GUI and check that font sizes in the Search and Pass2Add views are correctly scaled.
- [x] Task: Commit Phase 1 Results
    - [x] **AWAIT USER APPROVAL** before committing.
    - [x] Commit all sync updates.
- [x] Task: Conductor - User Manual Verification 'Automated Synchronization' (Protocol in workflow.md)

## Phase 2: Manual Merge & Logic Porting
- [x] Task: Integrate Upstream Updates into Modified Files
    - [x] Compare `sbs-ru` versions against `as_upstream` for all files in `modified_upstream_files`.
    - [x] Manually port relevant bug fixes or new features.
    - [x] **AWAIT USER APPROVAL** for the merged state of these files.
- [x] Task: Update Shadow Copies
    - [x] For each entry in `russian_copies` and `sbs_copies`:
        - [x] Compare shadow copy with its source and port necessary logic.
    - [x] **AWAIT USER APPROVAL** for the updated shadow copies.
- [x] Task: Validate Removed Upstream Files
    - [x] Identify files in `folders_to_check` removed from upstream.
    - [x] Clean up unused orphans or preserve required logic in `unique_paths`.
    - [x] **AWAIT USER APPROVAL** for the cleanup/preservation strategy.
- [x] Task: Documentation Parity Check
    - [x] Check `docs/` for new English documentation and create counterparts in `docs_rus/`.
    - [x] **AWAIT USER APPROVAL** for the documentation updates.
- [x] Task: Update Rehearsal Templates
    - [x] Based on the changes made, update `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json` and `guide.md` to reflect the new state and any new shadow copies or modified files identified.
- [x] Task: Commit Phase 2 Results
    - [x] Commit all manual merge resolutions and template updates.
- [x] Task: Conductor - User Manual Verification 'Manual Merge & Logic Porting' (Protocol in workflow.md)

## Phase 3: Final Validation & Checkpoint
- [x] Task: Run Baseline Verification Tests
    - [x] Run `uv run pytest tests/test_dps_imports.py`
    - [x] Run `uv run pytest tests/test_dps_logic.py`
    - [x] Run `uv run pytest tests/test_dps_exporters_functional.py`
    - [x] Run `uv run pytest tests/test_dps_docs_parity.py`
- [x] Task: Expand Test Suite
    - [x] Analyze upstream changes and identify areas requiring new tests to prevent future regressions.
    - [x] Implement new tests in the `tests/` directory.
- [x] Task: Comprehensive System Check
    - [x] Run `uv run pytest`.
    - [x] Manually verify that DPS-specific features (DpsView, SBS examples in GoldenDict) are still functional.
- [x] Task: Final Commit
    - [x] Commit any new tests.
    - [x] Suggested message: `sync: final validation and expanded testing (DD-MM)`.
- [x] Task: Conductor - User Manual Verification 'Final Validation & Checkpoint' (Protocol in workflow.md)