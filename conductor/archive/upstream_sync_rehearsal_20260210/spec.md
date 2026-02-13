# Specification: Upstream Sync Rehearsal (Standard Monthly)

## Overview
A reusable rehearsal track to validate and execute the upstream synchronization workflow for the DPS fork (`sbs-ru` branch). This process ensures that the fork stays up-to-date with the main DPD repository while preserving all DPS-specific customizations (Russian localization, SBS data, unique GUI views, and specialized logic).

## Goals
1. **Tooling Validation:** Confirm that `scripts/cl_dps/dpd-sync-folders` correctly utilizes the `dps_sync_registry.json` for exclusions.
2. **Synchronize Branches:** Execute a selective pull from `as_upstream` to `sbs-ru`, ensuring that modified upstream files are correctly restored to their local state.
3. **Manual Logic Integration:** Review changes in `modified_upstream_files` and port relevant upstream bug fixes or features to the localized versions in `sbs-ru`.
4. **Shadow Copy Maintenance:** Update localized "shadow" copies (`*_ru.py`, `*_sbs.py`, etc.) if their original sources have received significant updates.
5. **Documentation Parity:** Ensure all new English documentation has corresponding entries in the Russian documentation folder.
6. **Verify Integrity:** Validate that the system remains functional after synchronization (e.g., fonts are scaled, UI loads correctly).

## Functional Requirements
- Execution of `scripts/cl_dps/dpd-sync-folders` (Option 2: Selective Sync).
- Manual merge of all files listed in `modified_upstream_files` (Registry).
- Logic porting for `russian_copies` and `sbs_copies`.
- Parity check and placeholder creation for new `docs/` files in `docs_rus/`.
- Automated test execution to verify module imports, logic, and exporter flows.

## Acceptance Criteria
- `dpd-sync-folders` completes without errors and performs a "selective update" commit.
- `sbs-ru` is updated with `as_upstream` content (excluding registered paths).
- Manual merges for all files in `modified_upstream_files` are performed according to the `guide.md`.
- All shadow copies are updated to reflect relevant logic in original sources.
- Verification tests (`tests/test_dps_imports.py`, `tests/test_dps_logic.py`, `tests/test_dps_exporters_functional.py`, `tests/test_dps_docs_parity.py`) pass.
- The application builds and runs correctly, with fonts scaled and DPS views intact.
- All manual changes are committed with a timestamped message: `sync: manual merge and shadow copy updates (DD-MM)`.

## Out of Scope
- Major architectural refactoring (unless required by upstream breakage).
- New feature development unrelated to synchronization (unless it is relevant to logic in `russian_copies`, `sbs_copies`, and `unique_paths`).
