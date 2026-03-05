# Specification: Improve Upstream Sync Rehearsal Template

## Overview
The goal of this track is to completely revamp the `conductor/templates/upstream_sync_rehearsal` template. The current template frequently encounters errors during execution and misses important synchronization steps. By introducing robust testing scripts and strict manual checkpoints, we aim to make the planning and execution levels of the monthly manual sync highly reliable.

## Functional Requirements
- **Address Common Errors:**
  - Introduce specific checks and workflows to handle **Shadow copy conflicts** (e.g., `*_ru.py`, `*_sbs.py`).
  - Add database schema validation to prevent **DB Schema breaks** when upstream models change.
  - Implement dependency auditing to catch **Missing dependencies** (e.g., new module imports or template files).

- **Implementation of Strict Verification Checkpoints:**
  The plan template must integrate hard stops and manual verifications at the following critical stages:
  1. **Post-Bash Sync:** Verify the raw file diffs immediately after running the bash sync script.
  2. **Post-DB Rebuild:** Verify database models, relationships, and data integrity after integrating upstream schema changes.
  3. **Post-Shadow Update:** Validate data flow and structural parity after the shadow copies are updated.
  4. **Pre-Final Commit:** Run a comprehensive suite of exporter and application tests before finalizing the sync.

- **Testing Strategy (Mixed Approach):**
  - **Bash Assertions:** Utilize bash scripts for fast, immediate file-level checks (e.g., existence, diff summaries) during the initial sync phase.
  - **Python Pytests:** Develop and utilize robust pytest suites for logic parity, template structure verification, and data integrity testing during the post-shadow and pre-commit phases.

## Non-Functional Requirements
- The revamped template must remain clear, readable, and easy to follow for the developer conducting the sync.
- The workflow should cleanly separate "Auto" agent phases from "PRO" manual/audit phases to optimize the process.

## Acceptance Criteria
- [ ] A new, detailed `plan.md` is created in `conductor/templates/upstream_sync_rehearsal`.
- [ ] The plan explicitly includes all four identified verification checkpoints.
- [ ] Testing scripts (both Bash and Pytest) are defined or referenced within the template steps.
- [ ] Guidelines for handling shadow copy conflicts, missing dependencies, and DB schema changes are codified in the new template or its companion `guide.md`.