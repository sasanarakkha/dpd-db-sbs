# Plan: Design Upstream Sync Process

## Phase 1: Preparation & Consolidation
- [x] Task: Create new directory structure
    - [x] Create `conductor/templates/upstream_sync_rehearsal/`
    - [x] Move `conductor/dps_sync_registry.json` to `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json`
- [x] Task: Update references to registry
    - [x] Update `scripts/cl_dps/dpd-sync-folders` to point to the new registry path
    - [x] Verify no other files reference the old path (grep search)
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Shadow Copy Identification (Scanning)
- [x] Task: Scan for shadow copies (Gemini Flash)
    - [x] Use `glob` or `find` to list all files in target directories: `.github/workflows`, `db`, `docs`, `docs_rus`, `exporter`, `gui2`, `scripts`, `tools`, and root.
    - [x] Filter for filenames containing `ru`, `sbs`, or `dps` separated by `-` or `_`.
    - [x] Update `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json` with the new list under `russian_copies` (or new categories if needed).
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Deep Analysis & Guide Creation (Reasoning)
- [x] Task: Analyze "Modified Upstream Files"
    - [x] For each entry in `modified_upstream_files` from `dps_sync_registry.json`:
        - [x] Compare `sbs-ru` version against `as_upstream` version.
        - [x] Identify and document key local logic that must be preserved during sync.
- [x] Task: Analyze Shadow Copies (Russian & SBS)
    - [x] For each key-value pair in `russian_copies` and `sbs_copies` from the registry:
        - [x] Compare the local shadow copy (key) with its original source (value) within the `sbs-ru` branch.
        - [x] Identify the specific local customizations and logic that must be maintained.
- [x] Task: Create Sync Guide
    - [x] Draft `conductor/templates/upstream_sync_rehearsal/guide.md`.
    - [x] Document the logic for `dps_sync_registry.json` exclusions.
    - [x] Create a step-by-step manual merge checklist for complex files based on the analysis.
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Rehearsal Track Artifacts
- [x] Task: Create Rehearsal Track Spec Template
    - [x] Draft `conductor/templates/upstream_sync_rehearsal/spec.md`.
    - [x] Ensure it references the new guide and registry.
- [x] Task: Create Rehearsal Track Plan Template
    - [x] Draft `conductor/templates/upstream_sync_rehearsal/plan.md`.
    - [x] Include tasks for executing the sync script, validating fonts, and manual merging based on the guide.
- [x] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)
