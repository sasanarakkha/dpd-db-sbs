# Stage 1: FAST Prep

## Contract
- **Owner**: FAST only.
- **Input**: `accepted_sync.json`, `registry.json`, SMD files, and target upstream ref.
- **Output**: `prep_report.md`, `prep_manifest.json`, automated pull evidence, and updated `handoff.md`.
- **Boundary**: FAST records facts and command outputs. FAST does not classify strategy or resolve policy questions.

## Required Report Sections
- **Modified Tracked Files**: Direct divergences (`modified_upstream_files`).
- **Shadow/Inspired Sources**: Upstream files that drive local copies.
- **Untracked Changes**: New upstream files not yet in the registry.
- **Sync Range**: explicit `from -> to` upstream SHAs.
- **Validation Status**: Results of registry and SMD validators.

## Checklist
- [ ] `git fetch upstream` completed.
- [ ] `uv run python3 tests/check_shadow_modifications.py` passes.
- [ ] `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` passes.
- [ ] `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` passes.
- [ ] `accepted_sync.json` reviewed and bootstrapped.
- [ ] `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py <thread_dir>` executed.
- [ ] `uv run python3 kamma/upstream_sync/scripts/execute_sync.py <thread_dir>` executed.
- [ ] Commit 1 message prepared for manual review.

## Stop Conditions
FAST must stop and request ADVANCED if:
- Registry validation fails in a way that requires policy interpretation.
- A changed path has `discuss: true`.
- A new upstream file needs classification.
- Command output is ambiguous.
- FAST cannot decide whether a path is local, upstream-only, skipped, unique, shadow, or inspired.

## Handoff Required
Update `<thread_dir>/handoff.md` with commands run, exact failures, files changed, open issues,
errors/issues/repeated mistakes, next model (`ADVANCED`), and the exact fresh-session restart prompt.
Then stop.
