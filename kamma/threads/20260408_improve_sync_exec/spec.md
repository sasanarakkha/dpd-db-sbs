# Specification: Improve Upstream Sync Execution

## Overview
The previous thread successfully implemented a Sync Ledger and manifest-based workflow (`accepted_sync.json`, `prep_manifest.json`), standardizing Stage 1 (Prep) and Stage 3 (Finalize). However, the actual execution of the sync (the automated pull in Stage 1 and git tree manipulation) still relies on a Bash script (`full_sync.sh`). This script is brittle, hard to test, and can leave the repository in a broken state if interrupted.

Additionally, we currently have no way to skip syncing specific upstream changes once they are in the manifest without permanently modifying `registry.json`.

This thread will migrate the core sync execution logic into a robust Python script and introduce a mechanism for run-specific exclusions.

## What it should do
- Replace `scripts/bash/full_sync.sh` with a Python equivalent (e.g., `kamma/upstream_sync/scripts/execute_sync.py`).
- Maintain the exact same selective sync logic: update from the upstream ref defined in `accepted_sync.json`, apply changes to `sbs-ru`, and restore excluded files based on `registry.json`.
- **Implement Run-Specific Exclusions:** Allow the user to specify temporary exclusions (e.g., in a `run_exclusions.txt` file inside the thread directory) after reviewing the Stage 1 `prep_report.md`. The execution script will merge these temporary exclusions with the permanent ones from the registry, preventing unwanted changes from being synced.
- Implement robust error handling and state recovery (e.g., ensuring we always return to the original branch if the script fails).
- Provide clear, user-friendly console output (using `tools.printer`).

## Constraints
- **Must** not change the fundamental 3-stage workflow or `registry.json` schema.
- **Must** rely on the existing `accepted_sync.json` for the target ref.
- **Must** ensure the final Git state (staged files ready for commit) is correct and predictable.
- **Must not** be overcomplicated (avoid adding external dependencies if standard `subprocess` calls suffice).
- **Run-Specific Exclusions** must only apply to the current sync thread and must not modify `registry.json`.

## How we'll know it's done
- A new Python script exists and successfully executes the sync process.
- The `full_sync.sh` script is removed or archived.
- The user can add paths to a thread-specific exclusions file, and those paths are skipped during execution.
- Automated tests verify the new script's behavior and the run-specific exclusions logic.
- All documentation referencing `full_sync.sh` is updated.

## What's not included
- Changes to how the Prep report or Manifest are generated.
- Changes to the namespace isolation rules or registry validation.
