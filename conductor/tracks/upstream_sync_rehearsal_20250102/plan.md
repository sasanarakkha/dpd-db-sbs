# Upstream Sync Rehearsal

## Phase 1: Execution & Post-Processing

- [ ] Task: Run Sync Script
  - [ ] Action: Run `scripts/cl/dpd-sync-folders` interactively (User must do this).
  - [ ] Action: Select "Selective Sync" (Option 2).
  - [ ] Verification: Check that `as_upstream` was pulled and `sbs-ru` updated.
  - [ ] Verification: Check that `python gui2/font_scaling_helper.py` to re-apply font scaling to the freshly synced `gui2/` files.
  - [ ] Verification: Check that `git commit` was run properly.

## Phase 2: Merge & Shadow Update (The "Rehearsal")

- [ ] Task: Check "Modified Upstream Files" for conflicts
  - [ ] Action: Diff `db/models.py` against `as_upstream` version to ensure no upstream schema changes were missed or overwrote local tables.
  - [ ] Action: Same for other files from "modified_upstream_files".

- [ ] Task: Update "Russian Copies"
  - [ ] Action: For each key-value pair in `conductor/dps_sync_registry.json` ("russian_copies"):
    - [ ] Compare upstream file (value) with local copy (key).
    - [ ] If upstream has significant functional changes (new features, bug fixes), manually port them to the localized copy.
    - [ ] Example: Check `exporter/goldendict/export_dpd.py` (upstream) vs `exporter/goldendict/export_dpd_ru.py` (local).
    - [ ] Asking user to confirm: User knows what localised versions are doing, so feel free to ask questions if something is unclear.

- [ ] Task: Update "SBS Copies"
  - [ ] Action: For each key-value pair in `conductor/dps_sync_registry.json` ("sbs_copies"):
    - [ ] Compare upstream file (value) with local copy (key).
    - [ ] If upstream has significant functional changes (new features, bug fixes), manually port them to the localized copy.
    - [ ] Example: Check `exporter/goldendict/export_dpd.py` (upstream) vs `exporter/goldendict/export_dpd_ru.py` (local).
    - [ ] Asking user to confirm: User knows what localised versions are doing, so feel free to ask questions if something is unclear.

- [ ] Task: Final Commit
  - [ ] Action: Commit all merge resolutions and updates.
  - [ ] Verification: Check that all files from "russian_copies" and "sbs_copies" are up to date.
