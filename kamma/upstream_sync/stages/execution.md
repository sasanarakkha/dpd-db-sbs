# Stage 3: Execution & Verification

## Contract
- **Input**: `dynamic_plan.md` and `prep_manifest.json`.
- **Output**: Clean `git status`, passing tests, and updated `accepted_sync.json`.

## Required Report Sections
- **Implementation Logs**: Summary of changes made.
- **Test Summary**: `pytest` results and coverage confirmation.
- **Manual Verification Proof**: User confirmation of GoldenDict/webapp functionality.
- **Orphan Report**: Files archived or promoted to `unique_paths`.
- **Sync State Update**: `accepted_sync.json` advanced to the accepted target SHA.

## Checklist
- [ ] **Iron Rule** followed for all shadow updates.
- [ ] `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py -v` passes (all sync-related suites).
- [ ] Namespace isolation verified.
- [ ] Template syntax verified.
- [ ] `uv run python3 kamma/upstream_sync/scripts/finalize_accepted_sync.py <thread_dir>` updates `accepted_sync.json`.
- [ ] **Commit 2 Gate**: Implementation sync performed and approved.
- [ ] **Commit 3 Gate**: Cleanup sync performed and approved.
