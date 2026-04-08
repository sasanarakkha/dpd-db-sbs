# Stage 3: Execution & Verification

## Contract
- **Input**: `dynamic_plan.md`.
- **Output**: Clean `git status` and passing tests.

## Required Report Sections
- **Implementation Logs**: Summary of changes made.
- **Test Summary**: `pytest` results and coverage confirmation.
- **Manual Verification Proof**: User confirmation of GoldenDict/webapp functionality.
- **Orphan Report**: Files archived or promoted to `unique_paths`.

## Checklist
- [ ] **Iron Rule** followed for all shadow updates.
- [ ] `uv run pytest` passes (all suites).
- [ ] Namespace isolation verified.
- [ ] Template syntax verified.
- [ ] **Commit 2 Gate**: Implementation sync performed and approved.
- [ ] **Commit 3 Gate**: Cleanup sync performed and approved.
