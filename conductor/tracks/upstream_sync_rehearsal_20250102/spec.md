# Feature: Upstream Sync Rehearsal

## Overview
A rehearsal track to validate and execute the upstream synchronization workflow for the DPS fork. This involves refining the sync script, running the sync, applying post-processing (fonts), and manually merging updates into localized files.

## Goals
1.  **Refine Tooling:** Ensure `dpd-sync-folders` ignores all custom DPS files defined in `dps_sync_registry.json`.
2.  **Execute Sync:** Successfully pull changes from `upstream/main` to `sbs-ru` via `as_upstream`.
3.  **Maintain Extensions:** Ensure `Russian` and `SBS` tables in `db/models.py` are intact.
4.  **Update Shadows:** Identify if upstream logic changes (in exporters/tools) need to be ported to their `*_ru.py`, `*_sbs.py` and `*_dps.py` shadow copies.
5.  **Update Font Scaling:** If there are new files in `gui2/`, which has font settings in them, add them to list of files in the `python gui2/font_scaling_helper.py` and re-apply font scaling to the freshly synced `gui2/` files.

## Key Artifacts
-   `scripts/cl/dpd-sync-folders` (The script to be updated)
-   `conductor/dps_sync_registry.json` (Source of truth for exclusions)
-   `gui2/font_scaling_helper.py` (Post-sync hook, already part of scripts/cl/dpd-sync-folders)

## Updating Font Scaling
-   `python gui2/font_scaling_helper.py` Make sure that all files in folder gui2/ with font settings are included in the list of files to be scaled. (exception are unique files in gui2/dps_*)

## Success Criteria
-   `dpd-sync-folders` runs without overwriting custom DPS files.
-   `gui2` fonts are scaled correctly after sync.
-   `db/models.py` retains custom tables + upstream updates.
-   Localized files (`*_ru.py`) are reviewed and updated if necessary.
