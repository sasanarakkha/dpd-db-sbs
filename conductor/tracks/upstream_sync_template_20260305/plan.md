# Plan: Improve Upstream Sync Rehearsal Template

## Phase 1: Research and Script Analysis
- [ ] Task: Review Existing Sync Scripts
    - [ ] Analyze `bash scripts/cl_dps/dpd-sync-folders` to identify injection points for bash assertions.
    - [ ] Review current Python test suites (e.g., `tests/test_template_structure.py`) to determine coverage gaps for shadow copies and dependencies.
- [ ] Task: Conductor - User Manual Verification 'Research and Script Analysis' (Protocol in workflow.md)

## Phase 2: Develop Bash Assertions (Post-Bash Sync & Post-DB Rebuild)
- [x] Task: Write Tests for Bash Assertions
    - [x] Write failing test cases or define expected failure scenarios for file diff summaries and DB schema checks.
- [x] Task: Implement Bash Assertions
    - [x] Modify or create bash scripts to add fast file-level checks (e.g., checking for new upstream templates, checking for DB schema changes).
    - [x] Integrate a raw file diff summary output post-sync.
- [x] Task: Conductor - User Manual Verification 'Develop Bash Assertions (Post-Bash Sync & Post-DB Rebuild)' (Protocol in workflow.md)

## Phase 3: Develop Python Pytests (Post-Shadow Update & Pre-Final Commit)
- [x] Task: Write Tests for Parity and Dependencies
    - [x] Create failing pytest scripts to verify data flow, structural parity between upstream and shadow copies (e.g., `*_ru.py`, `*_sbs.py`).
    - [x] Create failing pytest scripts to audit missing dependencies/imports.
- [x] Task: Implement Pytests
    - [x] Implement the logic in the pytest scripts to parse, compare, and validate shadow copies against their upstream counterparts.
    - [x] Ensure tests accurately fail when a dependency or schema break is introduced.
- [x] Task: Conductor - User Manual Verification 'Develop Python Pytests (Post-Shadow Update & Pre-Final Commit)' (Protocol in workflow.md)

## Phase 4: Revamp Sync Template (plan.md and guide.md)
- [x] Task: Write Tests for Sync Template Structure
    - [x] Since templates are documentation, manual verification is sufficient.
- [x] Task: Implement `plan.md` Updates
    - [x] Redesign `conductor/templates/upstream_sync_rehearsal/plan.md` to cleanly separate Auto/PRO phases.
    - [x] Inject the four strict verification checkpoints (Post-Bash Sync, Post-DB Rebuild, Post-Shadow Update, Pre-Final Commit) into the template.
    - [x] Reference the newly created bash and pytest scripts in the appropriate template steps.
- [x] Task: Update `guide.md`
    - [x] Document guidelines for handling shadow copy conflicts, missing dependencies, and DB schema changes in `conductor/templates/upstream_sync_rehearsal/guide.md`.
- [x] Task: Conductor - User Manual Verification 'Revamp Sync Template (plan.md and guide.md)' (Protocol in workflow.md)