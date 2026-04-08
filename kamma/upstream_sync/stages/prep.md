# Stage 1: Prep

## Contract
- **Input**: `as_upstream` branch pointer.
- **Output**: `prep_report.md` in the thread folder.

## Required Report Sections
- **Modified Tracked Files**: Direct divergences (`modified_upstream_files`).
- **Shadow/Inspired Sources**: Upstream files that drive local copies.
- **Untracked Changes**: New upstream files not yet in the registry.
- **Validation Status**: Results of registry and SMD validators.

## Checklist
- [ ] `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` passes.
- [ ] `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` passes.
- [ ] `scripts/prep_analyzer.py` executed and report reviewed.
- [ ] **Commit 1 Gate**: Automated sync performed and approved.
