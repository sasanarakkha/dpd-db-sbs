# Important Future-Use Summary Only

This handoff intentionally keeps only the important summary needed for a future upstream-sync improvement session. It omits detailed session logs, repeated command output, and implementation narration that is not needed for future improvement work.

## Thread Purpose

Improve the `kamma/upstream_sync` workflow so upstream syncs are safer, restartable, model-boundary aware, and better validated for RU/SBS/DPS/Tamil localized files.

## Main Outcomes So Far

- Reworked upstream-sync docs from the old broad workflow into a 5-stage FAST/ADVANCED responsibility model.
- Added hard-stop handoffs so model switches and fresh sessions can restart from `handoff.md`.
- Strengthened registry and SMD validation, including Tamil coverage.
- Made sync execution fail fast on unsafe state:
  - dirty working tree;
  - wrong branch;
  - missing/invalid/stale `prep_manifest.json`;
  - non-empty `discuss_paths`;
  - failing post-sync assertions.
- Made `finalize_accepted_sync.py` verify the prep manifest before advancing `accepted_sync.json`.
- Added docs parity checks for unexpected local-only `docs_rus/` files.
- Added deleted-upstream-source handling so mapped RU/SBS/DPS/Tamil/inspired local paths are still reported in Stage 1 manifests.
- Added DPS backup behavior to `scripts/cl_dps/dpd-kamma-sync`.
- Reviewed the whole `kamma/upstream_sync` skill separately for simplicity, elegance, safety, and security. No major redesign was recommended; the current registry + manifest + FAST/ADVANCED hard-stop design remains the simplest safe architecture.
- Fixed a low-severity `check_docs_parity.py` reporting bug where writing a report to a thread directory outside the repo crashed while formatting the displayed path.
- Clarified the upstream-sync docs wording: the workflow is still 5 stages, with Stage 4 split into two model-bound substages.

## Important Design Decisions

- FAST owns mechanical command execution and evidence generation.
- ADVANCED owns analysis, planning, acceptance decisions, and reading FAST-produced evidence.
- If either model crosses its responsibility boundary, stop and write a restartable handoff.
- `prep_manifest.json.discuss_paths` is a hard stop before `execute_sync.py`.
- `execute_sync.py` must receive a thread directory; manifest verification cannot be skipped.
- `execute_sync.py` resets `as_upstream` to the verified manifest target SHA, not an unchecked moving ref.
- `finalize_accepted_sync.py` must verify the manifest before writing accepted sync state.
- Autonomous agent commits remain prohibited. The DPS wrapper script may run its reviewed, explicit backup commit behavior.
- The DPS backup wrapper commit message is exactly:

```text
backup dps data
```

## Key Files Changed

- `kamma/upstream_sync/guide.md`
- `kamma/upstream_sync/README.md`
- `kamma/upstream_sync/infrastructure.md`
- `kamma/upstream_sync/templates/sync_thread_plan.md`
- `kamma/upstream_sync/templates/sync_thread_spec.md`
- `kamma/upstream_sync/stages/prep.md`
- `kamma/upstream_sync/stages/analysis.md`
- `kamma/upstream_sync/stages/execution.md`
- `kamma/upstream_sync/registry.json`
- `kamma/upstream_sync/scripts/registry_helper.py`
- `kamma/upstream_sync/scripts/prep_analyzer.py`
- `kamma/upstream_sync/scripts/sync_runtime.py`
- `kamma/upstream_sync/scripts/execute_sync.py`
- `kamma/upstream_sync/scripts/finalize_accepted_sync.py`
- `kamma/upstream_sync/scripts/validate_registry.py`
- `kamma/upstream_sync/scripts/check_docs_parity.py`
- `scripts/cl_dps/dpd-kamma-sync`
- Relevant tests under `tests/test_*`.
- `tests/test_check_docs_parity.py`

## Validation Commands Used

Use these as the minimum reference set for future related work, adjusted to touched files:

```fish
uv run ruff check --fix <changed-files>
uv run ruff format <changed-files>
uv run pyright <changed-files>
uv run --with pyrefly pyrefly check --min-severity warn <changed-files>
uv run pytest tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_sync_state.py tests/test_upstream_sync_docs_policy.py tests/test_prep_analyzer.py tests/test_validate_registry.py tests/test_check_docs_parity.py tests/test_verify_smd_coverage.py -v
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py
uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py
git diff --check -- <changed-files>
```

Previously observed passing focused totals:

- Session 2 focused pytest set: 47 passed.
- Session 3 focused pytest set: 50 passed.
- Session 4 focused pytest set: 31 passed.
- Session 5 focused pytest set: 57 passed.
- Separate review follow-up focused pytest set: 6 passed.

## Known Issues, Errors, and Repeated Mistakes

- `~/agents/protocol-fix.md` was stale. The current path is `~/.agents/protocol-fix.md`, but the external protocol reference was intentionally not retained because project/global rules already cover the needed TDD and validation behavior.
- `exporter/sutta_central/sc_dict.json` was previously contradictory: under a skipped folder and listed as unique. It was removed from `unique_paths`.
- `tests/test_prep_analyzer.py` previously had stale expectations for `exporter/webapp/main.py`; actual mapping is `russian_copy`, not `dps_copy`.
- Tamil was initially missing from some helper/test coverage and is now included in strict-shadow mappings and SMD checks.
- Some RU/Tamil parity divergences are intentional and SMD-documented, so they were whitelisted rather than ported:
  - `db/families/family_idiom_ru.py` intentionally omits upstream `update_db_cache()`.
  - `db/tpd/tpd_to_lookup.py` intentionally omits root-processing helpers from `db/epd/epd_to_lookup.py`.
- `pyright` and `pyrefly` caught several typing weaknesses during implementation. Future changes should keep typed manifests and runtime narrowing explicit.
- A success-path `execute_sync` unit test once accidentally ran the real `scripts/bash/dpd-sync-assertions.sh`; future tests should mock assertion-script presence/absence deliberately.
- The broader idea of replacing `checkout as_upstream` plus `reset --hard` was intentionally not implemented. Treat it as a separate behavioral redesign if revisited.
- `check_docs_parity.py` previously assumed every report path could be made relative to the project root. This failed for external thread/report directories such as `/private/tmp`; it now falls back to an absolute display path.
- Existing unrelated dirty/untracked `resources/*` entries were left untouched.

## Current State

The previous upstream-sync improvement sessions were completed and validated. A separate review session found no need for major redesign and applied only small scoped improvements to docs wording and docs-parity report path handling. No agent-side git commit was made.

Most recent recommended commit message:

```text
#sync docs: clarify stage wording and parity report path
```

Earlier recommended commit messages, if history needs reconstruction:

```text
#sync tooling: tighten sync finalization gates
```

Older recommended commit messages:

```text
#sync workflow: clarify fast/advanced handoffs
#sync tooling: enforce tamil coverage and preflight gates
#sync tooling: block stale manifests and discuss pulls
#sync tooling: strengthen pre-sync backup and manifests
```

## Follow-up Improvement Plan Status

- Completed work:
  - Added Stage 1 pre-sync API health check command to the canonical guide, stage checklist, and sync thread plan template.
  - Fixed `gen_smd_scaffold.py` so DPS and Tamil strict shadows keep their correct scaffold categories.
  - Hardened `finalize_accepted_sync.py` so manifest verification receives the current accepted sync state before `accepted_sync.json` can be advanced.
  - Added additive `local_target_path` values to `prep_manifest.json` mapped actions, preserving `local_path`.
  - Documented `local_target_path` usage in Stage 2 planning docs.
  - Added/updated tests for each behavior.
- Exact commands run:
  - `uv run pytest tests/test_upstream_sync_docs_policy.py -v` red, then green.
  - `uv run pytest tests/test_gen_smd_scaffold.py -v` red, then green.
  - `uv run pytest tests/test_finalize_accepted_sync.py -v` red.
  - `uv run pytest tests/test_finalize_accepted_sync.py tests/test_sync_state.py -v` green.
  - `uv run pytest tests/test_prep_analyzer.py -v` red.
  - `uv run pytest tests/test_prep_analyzer.py tests/test_sync_state.py -v` green.
  - `uv run pytest tests/test_upstream_sync_docs_policy.py tests/test_gen_smd_scaffold.py tests/test_finalize_accepted_sync.py tests/test_sync_state.py tests/test_prep_analyzer.py -v` green: 26 passed.
  - `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` passed.
  - `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` passed.
  - `uv run ruff check --fix kamma/upstream_sync/scripts/gen_smd_scaffold.py kamma/upstream_sync/scripts/finalize_accepted_sync.py kamma/upstream_sync/scripts/prep_analyzer.py tests/test_upstream_sync_docs_policy.py tests/test_gen_smd_scaffold.py tests/test_finalize_accepted_sync.py tests/test_prep_analyzer.py` passed.
  - `uv run ruff format kamma/upstream_sync/scripts/gen_smd_scaffold.py kamma/upstream_sync/scripts/finalize_accepted_sync.py kamma/upstream_sync/scripts/prep_analyzer.py tests/test_upstream_sync_docs_policy.py tests/test_gen_smd_scaffold.py tests/test_finalize_accepted_sync.py tests/test_prep_analyzer.py` reformatted 3 files.
  - `uv run pyright kamma/upstream_sync/scripts/gen_smd_scaffold.py kamma/upstream_sync/scripts/finalize_accepted_sync.py kamma/upstream_sync/scripts/prep_analyzer.py tests/test_upstream_sync_docs_policy.py tests/test_gen_smd_scaffold.py tests/test_finalize_accepted_sync.py tests/test_prep_analyzer.py` passed: 0 errors.
  - `uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/gen_smd_scaffold.py kamma/upstream_sync/scripts/finalize_accepted_sync.py kamma/upstream_sync/scripts/prep_analyzer.py tests/test_upstream_sync_docs_policy.py tests/test_gen_smd_scaffold.py tests/test_finalize_accepted_sync.py tests/test_prep_analyzer.py` passed: 0 errors, 1 suppressed.
  - `git diff --check -- kamma/upstream_sync/guide.md kamma/upstream_sync/scripts/finalize_accepted_sync.py kamma/upstream_sync/scripts/gen_smd_scaffold.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/stages/analysis.md kamma/upstream_sync/stages/prep.md kamma/upstream_sync/templates/sync_thread_plan.md tests/test_finalize_accepted_sync.py tests/test_prep_analyzer.py tests/test_upstream_sync_docs_policy.py` passed.
  - `rg -n "[ \t]+$" kamma/threads/upstream_sync_improvment/spec.md kamma/threads/upstream_sync_improvment/plan.md tests/test_gen_smd_scaffold.py` found no trailing whitespace.
- Exact outputs or failures summarized:
  - Docs-policy red failure: missing API health check command from live docs.
  - SMD scaffold red failure: DPS/Tamil entries emitted as `sbs_copy`.
  - Finalize red failure: `verify_manifest` was called without `accepted_sync_state`.
  - Prep analyzer red failure: mapped actions lacked `local_target_path`.
  - Final focused test pass: 26 passed.
- Files changed:
  - `kamma/threads/upstream_sync_improvment/spec.md`
  - `kamma/threads/upstream_sync_improvment/plan.md`
  - `kamma/threads/upstream_sync_improvment/handoff.md`
  - `kamma/upstream_sync/guide.md`
  - `kamma/upstream_sync/stages/analysis.md`
  - `kamma/upstream_sync/stages/prep.md`
  - `kamma/upstream_sync/templates/sync_thread_plan.md`
  - `kamma/upstream_sync/scripts/gen_smd_scaffold.py`
  - `kamma/upstream_sync/scripts/finalize_accepted_sync.py`
  - `kamma/upstream_sync/scripts/prep_analyzer.py`
  - `tests/test_upstream_sync_docs_policy.py`
  - `tests/test_gen_smd_scaffold.py`
  - `tests/test_finalize_accepted_sync.py`
  - `tests/test_prep_analyzer.py`
- Open decisions:
  - User manual review is still needed.
  - Run `/kamma:3-review` in a fresh session after user confirms behavior is acceptable.
- Errors, issues, and repeated mistakes:
  - The first docs-template patch accidentally indented `- [ ] **1.1 Environmental Check**`; this was caught by diff review and corrected before final validation.
  - Existing unrelated dirty/untracked `resources/*` entries remain untouched.
- Next model to use: Review can run in the user's preferred review model.
- Exact restart prompt:

```text
Continue upstream sync improvement thread: kamma/threads/upstream_sync_improvment.
First read:
1. kamma/threads/upstream_sync_improvment/handoff.md
2. kamma/threads/upstream_sync_improvment/plan.md
3. kamma/threads/upstream_sync_improvment/spec.md
4. kamma/upstream_sync/guide.md

Task: review the completed follow-up implementation and prepare it for finalization. Do not broaden scope. Preserve unrelated resources/* dirty state.
```

## Typed Hardening Thread Finalized

- Thread finalized: `kamma/threads/20260531_upstream_sync_typed_hardening`.
- Archived to: `kamma/archive/20260531_upstream_sync_typed_hardening`.
- Active thread directory removed from `kamma/threads/`.
- No `project.md` or `tech.md` update was needed.
- No GitHub issue reference was found, so no issue comment/close was performed.
- Review verdict was `PASSED`.
- Objective completed: upstream-sync metadata parsing is now hardened with typed stdlib dataclasses and centralized validation while preserving existing JSON formats and CLI behavior.
- Main changes:
  - Added `kamma/upstream_sync/scripts/sync_schema.py`.
  - Routed registry, manifest, mapped action, and accepted sync state validation through typed schema objects.
  - Hardened prep analyzer rename handling so git renames are represented as delete/add facts.
  - Allowed approved intrinsic `rpd` and `tpd` markers in registry category naming checks.
  - Added exact stale-doc diff evidence to docs parity reporting.
  - Updated Stage 4.A docs wording for automatic diff evidence.
  - Added focused test coverage for schema validation, sync state validation, registry validation, rename handling, naming policy, finalize behavior, and docs parity.
- Review test evidence:
  - Focused pytest suite passed: 103 tests.
  - `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` passed.
  - `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` passed.
  - `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py /private/tmp/dpd-db-kamma-review` passed.
  - `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py /private/tmp/dpd-db-kamma-review` passed.
  - `uv run python3 kamma/upstream_sync/scripts/sync_runtime.py verify-manifest /private/tmp/dpd-db-kamma-review` passed.
  - Ruff, pyright, pyrefly, and `git diff --check` passed on the changed upstream-sync files.
- Recommended commit message:

```text
refactor(upstream-sync): harden typed metadata validation
```

- Related dirty entries still intentionally separate:
  - `resources/*`
  - `kamma/threads/upstream_sync_improvment/handoff.md`
