# Plan: Improve Upstream Sync Execution

## Phase 1: Setup & Scaffolding
- [x] Create `kamma/threads/20260408_improve_sync_exec/run_exclusions.txt` (empty placeholder)
- [x] Create `kamma/upstream_sync/scripts/execute_sync.py` with basic CLI structure and logging using `tools.printer`.

## Phase 2: Implementation of `execute_sync.py`
- [x] **State Management**: Implement logic to capture current Git state (branch, dirty status) to ensure safe recovery on failure.
- [x] **Ref Discovery**: Implement logic to read the target upstream ref from `accepted_sync.json`.
- [x] **Exclusion Logic**: 
    - [x] Merge permanent exclusions from `registry.json`.
    - [x] Add support for reading run-specific exclusions from the thread's `run_exclusions.txt`.
- [x] **Git Operations**: Implement the selective sync sequence using `subprocess` calls:
    - [x] Update `as_upstream`.
    - [x] Switch to `sbs-ru`.
    - [x] Checkout files from `as_upstream`.
    - [x] Restore excluded files (batching where possible).
- [x] **Error Handling**: Wrap Git operations in try/except blocks to auto-restore the repository state on error.

## Phase 3: Verification & Cleanup
- [x] Create `tests/test_execute_sync.py` to verify:
    - [x] Correct merging of exclusions.
    - [x] Successful sync state (dry-run or mock repo).
    - [x] Failure recovery.
- [x] Run the new script in a dry-run/test mode.
- [x] Update `scripts/bash/full_sync.sh` to either wrap the new Python script or be archived.
- [x] Update `kamma/upstream_sync/guide.md` and `infrastructure.md` to reflect the change.

## Phase 4: Finalization
- [x] Run `kamma/upstream_sync/scripts/finalize_accepted_sync.py` (if applicable for a test sync).
- [x] Stage all changes and prepare commit message.
