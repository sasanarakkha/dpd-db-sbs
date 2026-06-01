# Stage 3: FAST Execution & Verification

## Contract
- **Owner**: FAST only.
- **Input**: approved `dynamic_plan.md`, `prep_manifest.json`, and `handoff.md`.
- **Output**: implemented plan items, command/test evidence, and updated `handoff.md`.
- **Boundary**: FAST executes the approved plan literally. FAST does not redesign, infer missing strategy, or repair incomplete plan items.

## Required Evidence
- **Implementation Logs**: Item-by-item status from `dynamic_plan.md`.
- **Test Summary**: Exact commands run and pass/fail results.
- **Failure Summary**: Any failed command, missing anchor, unexpected diff, or incomplete plan item.
- **Files Changed**: Paths changed during execution.
- **Manual Verification Request**: Prepared for ADVANCED to decide and ask the user.

## Checklist
- [ ] Every started item marked in `dynamic_plan.md`.
- [ ] Iron Rule followed for all shadow updates.
- [ ] Split session after every 5 implementation items.
- [ ] `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py -v` run.
- [ ] `uv run python3 tests/check_shadow_modifications.py` run.
- [ ] `uv run python tests/smoke_test_sync.py` run if required by `dynamic_plan.md`.
- [ ] Commit 2 message prepared for manual review.

## Stop Conditions
FAST must stop and request ADVANCED if:
- An expected anchor or exact replacement is missing.
- A plan item is incomplete.
- A merge conflict requires judgment.
- A test failure is not explicitly covered by the plan.
- FAST believes a different implementation would be better.
- Cleanup requires a registry/SMD policy decision.

## Handoff Required
Update `<thread_dir>/handoff.md` with completed items, failed items, commands run, outputs/failures,
files changed, errors/issues/repeated mistakes, next model (`ADVANCED`), and the exact fresh-session
restart prompt. Then stop.
