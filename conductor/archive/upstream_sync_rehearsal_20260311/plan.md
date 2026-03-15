# Plan: Upstream Sync Rehearsal (Standard Monthly)

## Phase 1: Automated Synchronization (Auto)
- [x] Task: Pre-Sync Branch Check
    - [x] Verify there are no uncommitted changes in the `sbs-ru` branch.
- [x] Task: Execute Sync Script
    - [x] Run `bash scripts/bash/full_sync.sh`.
    - [x] Select **Option 2 (Selective Sync)**.
    - [x] **Update Submodules**: Run `git submodule init && git submodule update`.
    - [x] **AUTO-COMMIT (COMMIT 1/3)**: The sync script performs an automated commit here.
- [x] Task: Post-Bash Sync Verification
    - [x] Review raw file diffs, DB schema breaks, and missing dependencies.
- [x] Task: Conductor - User Manual Verification 'Automated Synchronization'

## Phase 2: Analysis & Dynamic Planning (PRO)
- [x] Task: Semantic Analysis & Create Dynamic Spec
    - [x] Intersected latest commit's modified files with all mapped source files and directories.
    - [x] Wrote `dynamic_sync_plan.md`.

## Phase 3: Implementation (Auto)
- [x] Task: Execute Dynamic Plan
    - [x] Ported upstream changes to shadow copies (Jinja2 migration, etc.).
- [x] Task: Update Shadow Copies & Parity
    - [x] Verified render parity, imports, and new upstream templates.
- [x] Task: Documentation Parity
    - [x] Synced `docs/` and `docs_rus/`.

## Phase 4: Final Logic Audit (PRO)
- [x] Task: PRO Logic Audit & DB Rebuild Verification
    - [x] Manually audited all shadow copies against upstream originals.

## Phase 5: Pre-Cleanup Testing & Second Commit (Auto)
- [x] Task: Pre-Commit 2 Verification (Automated Tests)
    - [x] Ran structural, logic, and parity tests.
- [x] Task: Manual Verification
    - [x] User verified GoldenDict, Kindle, and Webapp exports.
    - [x] Verified GUI2 functionality.
- [x] Task: **🛑 USER APPROVAL GATE FOR COMMIT 2**
    - [x] Obtained explicit approval to proceed.
- [x] Task: **SECOND MANUAL COMMIT (COMMIT 2/3)**
    - [x] Committed manual merges and shadow updates (`ccc08358`).

## Phase 6: Cleanup & Deprecation (Auto)
- [x] Task: Systematic Orphan Identification & Archiving
    - [x] Ran `tests/test_shadow_cleanup.py` folder-by-folder.
    - [x] Archived 1,236 unused orphans.
- [x] Task: Registry Update
    - [x] Updated `dps_sync_registry.json` with promotions and re-mappings.

## Phase 7: Finalization & Third Commit (Auto)
- [x] Task: Pre-Commit 3 Verification (Automated Tests)
    - [x] Ran all 140+ tests again; all passed.
- [x] Task: Conductor - Final History Audit & Improvement Documentation
    - [x] Created `conductor/templates/upstream_sync_rehearsal/improvements_fresh.md` with exhaustive detail.
- [x] Task: **🛑 FINAL USER APPROVAL GATE FOR COMMIT 3**
    - [x] Obtained explicit approval: "Proceed with final commit".
- [x] Task: **FINAL MANUAL COMMIT (COMMIT 3/3)**
    - [x] Committed cleanup actions and improvement documentation (`49bb27a5`).
- [x] **Task: Final Confirmation**
    - [x] Track is complete.
