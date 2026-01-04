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
  - [ ] Action: Diff all files from category "modified_upstream_files" from dps_sync_registry.json with `as_upstream` version and when needed apply those updates to the local files.
  - [ ] Asking user to confirm: User knows what localised versions are doing, so feel free to ask questions if something is unclear.

- [ ] Task: Update "Russian Copies"
  - [ ] Action: For each key-value pair in `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json` ("russian_copies"):
    - [ ] Compare upstream file (value) with local copy (key).
    - [ ] If upstream has significant functional changes (new features, bug fixes), manually port them to the localized copy.
    - [ ] Example: Check `exporter/goldendict/export_dpd.py` (upstream) vs `exporter/goldendict/export_dpd_ru.py` (local).
    - [ ] Asking user to confirm: User knows what localised versions are doing, so feel free to ask questions if something is unclear.

- [ ] Task: Update "SBS Copies"
  - [ ] Action: For each key-value pair in `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json` ("sbs_copies"):
    - [ ] Compare upstream file (value) with local copy (key).
    - [ ] If upstream has significant functional changes (new features, bug fixes), manually port them to the localized copy.
    - [ ] Example: Check `exporter/goldendict/export_dpd.py` (upstream) vs `exporter/goldendict/export_dpd_ru.py` (local).
    - [ ] Asking user to confirm: User knows what localised versions are doing, so feel free to ask questions if something is unclear.

- [ ] Task: Remove unused files
  - [ ] Action: Go through folders and check if some files are not in the `as_upstream` branch, exclude `dps_`, `sbs_`, `ru_` files. and check if they unused by any local files, remove them, if unclear ask for user input. Idea is to clean thyis fork clean with up stream repo
  - [ ] Action: exclude folders and files from dps_sync_registry.json "unique_paths" and "ignored_files" and "russian_copies" and "sbs_copies" and everything mentioned in .gitignore

- [ ] Task: Russian documentation
  - [ ] Action: Make sure that all documentation in docs/ has russian versions in docs_rus/
  - [ ] Action: If any extra files in docs_rus/ that are not in docs/ remove them

- [ ] Task: Final Commit
  - [ ] Action: Commit all merge resolutions and updates.
  - [ ] Verification: Check that all files from "russian_copies" and "sbs_copies" are up to date.
