# Stage 1: Prep

## Contract
- **Input**: `accepted_sync.json` and target upstream ref.
- **Output**: `prep_report.md` and `prep_manifest.json` in the thread folder.

## Required Report Sections
- **Modified Tracked Files**: Direct divergences (`modified_upstream_files`).
- **Shadow/Inspired Sources**: Upstream files that drive local copies.
- **Untracked Changes**: New upstream files not yet in the registry.
- **Sync Range**: explicit `from -> to` upstream SHAs.
- **Validation Status**: Results of registry and SMD validators.

## Checklist
- [ ] `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` passes.
- [ ] `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` passes.
- [ ] `accepted_sync.json` reviewed and bootstrapped.
- [ ] `scripts/prep_analyzer.py <thread_dir>` executed and outputs reviewed.
- [ ] **Commit 1 Gate**: Automated sync performed and approved.
