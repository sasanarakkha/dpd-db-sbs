# Plan: Design Upstream Sync Process

## Phase 1: Preparation & Consolidation
- [x] Task: Create new directory structure
    - [x] Create `conductor/templates/upstream_sync_rehearsal/`
    - [x] Move `conductor/dps_sync_registry.json` to `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json`
- [x] Task: Update references to registry
    - [x] Update `scripts/cl_dps/dpd-sync-folders` to point to the new registry path
    - [x] Verify no other files reference the old path (grep search)
- [~] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Shadow Copy Identification (Scanning)
- [ ] Task: Scan for shadow copies (Gemini Flash)
    - [ ] Use `glob` or `find` to list all files in target directories: `.github/workflows`, `db`, `docs`, `docs_rus`, `exporter`, `gui2`, `scripts`, `tools`, and root.
    - [ ] Filter for filenames containing `ru`, `sbs`, or `dps` separated by `-` or `_`.
    - [ ] Update `conductor/templates/upstream_sync_rehearsal/dps_sync_registry.json` with the new list under `russian_copies` (or new categories if needed).
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Deep Analysis & Guide Creation (Reasoning)
- [ ] Task: Analyze "Modified Upstream Files"
    - [ ] For each entry in `modified_upstream_files` from `dps_sync_registry.json`:
        - [ ] Compare `sbs-ru` version against `as_upstream` version.
        - [ ] Identify and document key local logic that must be preserved during sync.
- [ ] Task: Analyze Shadow Copies (Russian & SBS)
    - [ ] For each key-value pair in `russian_copies` and `sbs_copies` from the registry:
        - [ ] Compare the local shadow copy (key) with its original source (value) within the `sbs-ru` branch.
        - [ ] Identify the specific local customizations and logic that must be maintained.
- [ ] Task: Create Sync Guide
    - [ ] Draft `conductor/templates/upstream_sync_rehearsal/guide.md`.
    - [ ] Document the logic for `dps_sync_registry.json` exclusions.
    - [ ] Create a step-by-step manual merge checklist for complex files based on the analysis.
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Rehearsal Track Artifacts
- [ ] Task: Create Rehearsal Track Spec Template
    - [ ] Draft `conductor/templates/upstream_sync_rehearsal/spec.md`.
    - [ ] Ensure it references the new guide and registry.
- [ ] Task: Create Rehearsal Track Plan Template
    - [ ] Draft `conductor/templates/upstream_sync_rehearsal/plan.md`.
    - [ ] Include tasks for executing the sync script, validating fonts, and manual merging based on the guide.
- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)
