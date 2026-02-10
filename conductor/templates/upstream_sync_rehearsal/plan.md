# Plan: Upstream Sync Rehearsal

## Phase 1: Automated Synchronization
- [ ] Task: Execute Sync Script
    - [ ] Run `bash scripts/cl_dps/dpd-sync-folders` from the project root.
    - [ ] Select **Option 2 (Selective Sync)** when prompted.
    - [ ] Verification: Confirm the script completes and performs a "selective update" commit.
- [ ] Task: Verify Post-Sync Hooks
    - [ ] Ensure `gui2/font_scaling_helper.py` was executed as part of the script.
    - [ ] Verification: Open the GUI and check that font sizes in the Search and Pass2Add views are correctly scaled (e.g., 17px/15px).
- [ ] Task: Commit Phase 1 Results
    - [ ] **AWAIT EXPLICIT USER APPROVAL** (e.g., "Phase 1 is complete").
    - [ ] Commit all sync updates.
- [ ] Task: Conductor - User Manual Verification 'Automated Synchronization' (Protocol in workflow.md)

## Phase 2: Manual Merge & Logic Porting
- [ ] Task: Integrate Upstream Updates into Modified Files **(Requires PRO Model)**
    - [ ] Following the `conductor/templates/upstream_sync_rehearsal/guide.md`, compare `sbs-ru` versions against `as_upstream` for all files in `modified_upstream_files`.
    - [ ] Manually port relevant bug fixes or new features.
    - [ ] **AWAIT USER APPROVAL** for the merged state of these files.
- [ ] Task: Update Shadow Copies **(Requires PRO Model)**
    - [ ] **PROTOCOL: Systematic Shadow Verification**
        - [ ] Identify all files modified in the latest sync commit (e.g., `git diff-tree --no-commit-id --name-only -r <commit_id>`).
        - [ ] Cross-reference this list with all "sources" (values) in the `russian_copies` and `sbs_copies` sections of `dps_sync_registry.json`.
        - [ ] For every source file that changed:
            - [ ] Run `diff <source> <shadow>` to identify functional logic updates in the upstream source.
            - [ ] Port necessary functional logic to the shadow copy.
            - [ ] **STRICT PRESERVATION:** Ensure `RuPaths`, `DPSPaths`, and translation/SBS logic are NOT overwritten.
        - [ ] **AWAIT USER APPROVAL** for the updated shadow copies after EACH significant set of related files.
- [ ] Task: Validate Removed Upstream Files
    - [ ] Identify files in `folders_to_check` that were removed from upstream.
    - [ ] Clean up unused orphans or preserve required logic in `unique_paths`.
    - [ ] **AWAIT USER APPROVAL** for the cleanup/preservation strategy.
- [ ] Task: Documentation Parity Check
    - [ ] Check `docs/` for any new English documentation files.
    - [ ] Create corresponding placeholders or translations in `docs_rus/`.
    - [ ] Update `mkdocs_ru.yaml` navigation to match any additions in `mkdocs.yaml`.
- [ ] Task: Final Phase 2 Review
    - [ ] **AWAIT USER APPROVAL** for the documentation updates.
    - [ ] **HARD STOP:** Present a summary of ALL manual changes made in Phase 2.
    - [ ] **AWAIT EXPLICIT SIGNAL:** "Phase 2 is complete".

- [ ] Task: Conductor - User Manual Verification 'Manual Merge & Logic Porting' (Protocol in workflow.md)
- [ ] Task: Verification Tests
    - [ ] Run `uv run pytest tests/test_dps_imports.py` to ensure all DPS modules are importable.
    - [ ] Run `uv run pytest tests/test_dps_logic.py` to verify family generation logic.
    - [ ] Run `uv run pytest tests/test_dps_exporters_functional.py` to verify exporter control flows.
    - [ ] Run `uv run pytest tests/test_dps_docs_parity.py` to ensure documentation parity.
- [ ] Task: Expand Test Suite **(Requires PRO Model)**
    - [ ] Analyze upstream changes and identify areas requiring new tests to prevent future regressions.
    - [ ] Implement new tests in the `tests/` directory.
- [ ] Task: Comprehensive System Check
    - [ ] Run project-specific tests: `uv run pytest`.
    - [ ] Manually verify that DPS-specific features (DpsView, SBS examples in GoldenDict) are still functional.
- [ ] Task: Final Review & Commit
    - [ ] **AWAIT EXPLICIT USER APPROVAL** (e.g., "Phase 3 is complete").
    - [ ] Commit all manual merge resolutions and documentation updates.
    - [ ] Suggested message: `sync: manual merge and shadow copy updates (DD-MM)`.
- [ ] Task: Conductor - User Manual Verification 'Phase Completion' (Protocol in workflow.md)
