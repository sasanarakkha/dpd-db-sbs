# Feature: Upstream Sync Rehearsal

## Overview
A rehearsal track to validate and execute the upstream synchronization workflow for the DPS fork. This involves checking the sync script, running the sync, making sure post-processing happening (fonts, already part of the sync script), and manually merging updates into localized files.

## Goals
1.  **Refine Tooling:** Ensure `dpd-sync-folders` ignores all custom DPS files defined in `dps_sync_registry.json`.
2.  **Execute Sync:** Successfully pull changes from `upstream/main` to `sbs-ru` via `as_upstream`. Excluding the files defined in `dps_sync_registry.json` "modified_upstream_files" and "ignored_files".
3.  **Maintain Extensions:** Identify if upstream files from list "modified_upstream_files" has any significant functional changes (new features, bug fixes), manually port them to the localized copy keeping local functionality.
4.  **Update Shadows:** Identify if upstream logic changes need to be ported to their (`*_ru.`, `*_sbs.` and `*_dps.` and `ru_*.`, `sbs_*.` and `dps_*.`) shadow copies in categories "russian_copies" and "sbs_copies" from `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json`.

## Key Artifacts
-   `scripts/cl/dpd-sync-folders` (The script with 2 options of syncing)
-   `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json` (Source of truth for exclusions)
-   `gui2/font_scaling_helper.py` (Post-sync hook, already part of scripts/cl/dpd-sync-folders)

## Updating Font Scaling
-   `python gui2/font_scaling_helper.py` Make sure that all files in folder gui2/ with font settings are included in the list of files to be scaled. (exception are unique files in gui2/dps_* and exception list in font_scaling_helper.py)

## Success Criteria
-   `dpd-sync-folders` runs without overwriting custom DPS files.
-   `gui2` fonts are scaled correctly after sync.
-   Localized files (`*_ru.`, `*_sbs.` and `*_dps.` and `ru_*.`, `sbs_*.` and `dps_*.`) are reviewed and updated if necessary.
-   All modified local files are received new updates from their original copies.
-   All modified local files are committed.
