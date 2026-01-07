# Plan: Upstream Sync Rehearsal

## Phase 1: Automated Synchronization
- [ ] Task: Execute Sync Script
    - [ ] Run `bash scripts/cl_dps/dpd-sync-folders` from the project root.
    - [ ] Select **Option 2 (Selective Sync)** when prompted.
    - [ ] Verification: Confirm the script completes and performs a "selective update" commit.
- [ ] Task: Verify Post-Sync Hooks
    - [ ] Ensure `gui2/font_scaling_helper.py` was executed as part of the script.
    - [ ] Verification: Open the GUI and check that font sizes in the Search and Pass2Add views are correctly scaled (e.g., 17px/15px).

## Phase 2: Manual Merge & Logic Porting
- [ ] Task: Integrate Upstream Updates into Modified Files
    - [ ] Following the `conductor/templates/upstream_sync_rehearsal/guide.md`, compare `sbs-ru` versions against `as_upstream` for all files in `modified_upstream_files`.
    - [ ] Manually port relevant bug fixes or new features.
    - [ ] **Priority:** All files in the `modified_upstream_files` category must be treated with equal importance and manually merged if needed.
- [ ] Task: Update Shadow Copies
    - [ ] For each entry in `russian_copies` and `sbs_copies` in the registry:
        - [ ] Compare the **shadow copy (the 'key')** with its **source (the 'value')**.
        - [ ] Port necessary logic while preserving `RuPaths`, `DPSPaths`, and translation/SBS logic.
- [ ] Task: Validate Removed Upstream Files
    - [ ] Identify files in `folders_to_check` that were removed from upstream.
    - [ ] Verify that no remaining local code depends on these deleted files.
    - [ ] Clean up any unused orphans.
- [ ] Task: Documentation Parity Check
    - [ ] Check `docs/` for any new English documentation files.
    - [ ] Create corresponding placeholders or translations in `docs_rus/`.

## Phase 3: Final Validation & Checkpoint
- [ ] Task: Verification Tests
    - [ ] Run `uv run pytest tests/test_dps_imports.py` to ensure all DPS modules are importable.
    - [ ] Run `uv run pytest tests/test_dps_logic.py` to verify family generation logic.
    - [ ] Run `uv run pytest tests/test_dps_exporters_functional.py` to verify exporter control flows.
    - [ ] Run `uv run pytest tests/test_dps_docs_parity.py` to ensure documentation parity.
- [ ] Task: Comprehensive System Check
    - [ ] Run project-specific tests: `uv run pytest`.
    - [ ] Manually verify that DPS-specific features (DpsView, SBS examples in GoldenDict) are still functional.
- [ ] Task: Final Commit
    - [ ] Commit all manual merge resolutions and documentation updates.
    - [ ] Suggested message: `sync: manual merge and shadow copy updates (DD-MM)`.
- [ ] Task: Conductor - User Manual Verification 'Phase Completion' (Protocol in workflow.md)
