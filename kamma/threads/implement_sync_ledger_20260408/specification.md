# Specification: Sync Ledger / Manifest Workflow

## Problem

The sync process had accuracy issues:
1. Prep used `as_upstream..HEAD` which could be noisy/contaminated
2. `dps_copies` was partially supported
3. Parity failures printed but didn't fail tests
4. `full_sync.sh` used inline Python and hard-coded refs
5. No explicit way to advance sync state after Stage 3

## Solution

Implement **Approach 3** (lightweight sync ledger):

1. Track last accepted upstream SHA in `accepted_sync.json`
2. Prep diffs explicit upstream range
3. Generate machine-readable manifest alongside report
4. Execution can advance sync state
5. Shell automation reads from sync state

## Constraints

- **Must** keep 3-stage workflow
- **Must not** touch `docs/` (upstream-only)
- **Must** stay lightweight
- **Must** make `dps_copies` first-class
- **Must** fail on parity mismatches

## Files Changed

### New Files
- `kamma/upstream_sync/accepted_sync.json`
- `kamma/upstream_sync/scripts/finalize_accepted_sync.py`
- `kamma/upstream_sync/scripts/sync_runtime.py`
- `tests/test_sync_state.py`
- `tests/test_check_shadow_modifications.py`

### Modified Files
- `kamma/upstream_sync/scripts/prep_analyzer.py`
- `kamma/upstream_sync/scripts/registry_helper.py`
- `kamma/upstream_sync/scripts/validate_registry.py`
- `kamma/upstream_sync/scripts/verify_smd_coverage.py`
- `scripts/bash/full_sync.sh`
- `tests/test_shadow_parity.py`
- `tests/test_prep_analyzer.py`
- `tests/test_validate_registry.py`
- `tests/test_verify_smd_coverage.py`
- `tests/check_shadow_modifications.py`
- Plus docs in `kamma/upstream_sync/`

## Success Criteria

1. Accepted sync state persisted in JSON
2. Prep produces both report AND manifest
3. Stage 3 can advance sync state
4. Shell scripts read from sync state (not hard-coded)
5. All existing tests pass
6. `dps_copies` supported everywhere
7. Parity failures fail tests