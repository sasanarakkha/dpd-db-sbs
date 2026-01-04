# Track: Design Upstream Sync Process

## Overview
This track is dedicated to designing and refining the process for synchronizing the DPS fork (`sbs-ru` branch) with the upstream repository (`as_upstream` branch). The `as_upstream` branch is automatically synced daily with the upstream repository, so all comparisons should be performed locally between `sbs-ru` and `as_upstream`.

This process involves a comprehensive analysis of the codebase, consolidating sync-related artifacts, and creating a robust, repeatable "Upstream Sync Rehearsal" track specification. We will use faster AI models for scanning and high-reasoning models for deep analysis.

## Goals
1.  **Codebase Analysis:**
    -   Systematically review critical directories: `.github/workflows`, `db`, `docs`, `docs_rus`, `exporter`, `gui2` (excluding `data`), `scripts`, `tools`.
    -   Review **files located directly in the root directory** (do not scan unlisted subdirectories).
    -   Identify localized files and logic that must be preserved.
2.  **Consolidate Artifacts:**
    -   Create directory `conductor/templates/upstream_sync_rehearsal/`.
    -   Move `conductor/dps_sync_registry.json` to `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json`.
    -   Update the registry with new findings (exclusions, unique paths, shadow copies).
3.  **Update References:** Update `scripts/cl_dps/dpd-sync-folders` to reference the new registry location.
4.  **Documentation:** Create a detailed "How to Sync" guide at `conductor/templates/upstream_sync_rehearsal/guide.md` using high-reasoning models to explain the logic behind exclusions and manual merge steps.
5.  **Rehearsal Track Creation:** Generate fully specified `spec.md` and `plan.md` templates for the reusable "Upstream Sync Rehearsal" track in `conductor/templates/upstream_sync_rehearsal/`.

## Scope
-   **In Scope:**
    -   **Scanning (Gemini Flash):** Identification of shadow copies. Defined as files containing tokens `ru`, `sbs`, or `dps` anywhere in the filename, separated by `-` or `_` (e.g., `export_dpd_ru.py`, `ru-config.json`).
    -   **Analysis (Gemini Pro/Thinking):** Deep comparison of upstream vs. local files to generate preservation guidelines.
    -   **Target Directories:** `.github/workflows`, `db`, `docs`, `docs_rus`, `exporter`, `gui2`, `scripts`, `tools`.
    -   **Root Directory:** Files only.
    -   **File Types:** `.py`, `.html`, `.js`, `.md`.
    -   **Refactoring:** Updating `scripts/cl_dps/dpd-sync-folders`.
-   **Out of Scope:**
    -   Actual execution of the upstream sync.
    -   Recursive analysis of subdirectories not explicitly listed.
    -   Analysis of files ignored by `.gitignore`.

## Success Criteria
-   All sync-related artifacts are consolidated in `conductor/templates/upstream_sync_rehearsal/`.
-   `scripts/cl_dps/dpd-sync-folders` functions correctly with the new registry path.
-   The registry accurately reflects the current state, including all loosely named shadow copies.
-   A clear guide and reusable track templates are available for the next sync cycle.