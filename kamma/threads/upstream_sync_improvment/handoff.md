Session 1

## Scope

Analyzed `kamma/upstream_sync` as a standalone workflow and implemented the approved documentation-only improvement:
- Strictly separate FAST and ADVANCED model responsibilities.
- Require hard stops whenever either model crosses its responsibility boundary.
- Require every hard stop to be restartable from a fresh session with `handoff.md` as the source of truth.
- Align quick-start docs, stage contracts, and sync thread templates with the 5-stage model-split workflow.

No Python scripts, tests, registry entries, shadow files, sync behavior, `.env`, or `.ini` files were changed in this session.

## Files Changed

- `kamma/upstream_sync/guide.md`
  - Added `Session Management` rules for fresh-session hard stops.
  - Added required hard-stop artifacts and required `handoff.md` fields.
  - Added restart prompt template.
  - Replaced weak model switch guidance with a strict `Model Responsibility Contract`.
  - Marked Stage 1 and Stage 3 as FAST-owned.
  - Marked Stage 2, Stage 4.A, and Stage 5 acceptance as ADVANCED-owned.
  - Added stop conditions for FAST and ADVANCED boundary violations.
- `kamma/upstream_sync/README.md`
  - Replaced old 3-stage quick start with the 5-stage model-split workflow.
  - Documented that FAST performs mechanical work and ADVANCED performs analysis/planning.
- `kamma/upstream_sync/infrastructure.md`
  - Updated guide description from 3-stage workflow to 5-stage workflow with model responsibilities.
  - Added a model responsibility table.
- `kamma/upstream_sync/templates/sync_thread_plan.md`
  - Rewritten around FAST/ADVANCED ownership.
  - Added hard-stop handoff checklist and restart prompt for each stage.
  - Removed old higher/lower model language.
- `kamma/upstream_sync/templates/sync_thread_spec.md`
  - Added success criteria for model-boundary compliance and fresh-session handoffs.
  - Added model boundary table and handoff requirements.
  - Updated key references for the 5-stage workflow.
- `kamma/upstream_sync/stages/prep.md`
  - Rewritten as Stage 1 FAST prep contract.
  - Added stop conditions and handoff requirements.
- `kamma/upstream_sync/stages/analysis.md`
  - Rewritten as Stage 2 ADVANCED analysis contract.
  - Added plan quality gate, stop conditions, and handoff requirements.
- `kamma/upstream_sync/stages/execution.md`
  - Rewritten as Stage 3 FAST execution contract.
  - Added evidence requirements, stop conditions, and handoff requirements.

## Test Evidence

Documentation-only verification passed:
- `rg -n "3-stage|3-Stage|Higher model|Lower model|PRO model|Auto / PRO|full_sync\\.sh|as_upstream|any model" kamma/upstream_sync/README.md kamma/upstream_sync/infrastructure.md kamma/upstream_sync/guide.md kamma/upstream_sync/templates kamma/upstream_sync/stages` — no matches.
- `git diff --check -- kamma/upstream_sync/guide.md kamma/upstream_sync/README.md kamma/upstream_sync/infrastructure.md kamma/upstream_sync/templates/sync_thread_plan.md kamma/upstream_sync/templates/sync_thread_spec.md kamma/upstream_sync/stages/prep.md kamma/upstream_sync/stages/analysis.md kamma/upstream_sync/stages/execution.md` — passed.

Python validation was not run because this session only changed Markdown documentation.

## Errors, Issues, and Repeated Mistakes

- Initial review found real non-doc issues, but they were deliberately left out of Session 1 scope:
  - `validate_registry.py` failed due to `exporter/sutta_central/sc_dict.json` being both under a skipped folder and listed as unique.
  - The sync pytest set failed on `db/families/family_idiom_ru.py` parity.
  - Tamil was documented as in scope but not first-class in some helper/test paths.
- Session 1 intentionally did not fix those issues because the approved request was the model-boundary and fresh-session workflow documentation.
- No commits were made.

## Current State

Session 1 documentation work is complete. Review the changed Markdown before using the workflow for the next upstream sync.

Suggested commit message for Session 1:

```text
#sync workflow: clarify fast/advanced handoffs
```


Session 2

## Scope

Approved and implemented the full upstream-sync improvement set identified in the review:
- Fix contradictory `exporter/sutta_central/` registry categorization.
- Include Tamil strict shadows in upstream-sync helper mappings and checks.
- Make `execute_sync.py` fail fast on unsafe preflight state.
- Use a real manifest generation timestamp.
- Fix stale prep-analyzer test expectations.
- Add a guard against autonomous commit wording in sync docs.

## Files Changed

- `kamma/upstream_sync/registry.json`
  - Removed `exporter/sutta_central/sc_dict.json` from `unique_paths` because the parent folder is upstream-owned and accepted wholesale.
- `kamma/upstream_sync/README.md`
- `kamma/upstream_sync/guide.md`
- `kamma/upstream_sync/infrastructure.md`
  - Clarified that `skip_sync_patterns` excludes paths from Stage 1 analysis only; paths are still synced unless also listed in `no_sync_files`.
  - Reworded Stage 4.B from "then commit" to "then prepare the commit message".
- `kamma/upstream_sync/scripts/registry_helper.py`
  - Added `get_string_mapping()`.
  - Included `tamil_copies` in `get_strict_shadow_mappings()`.
  - Included `tamil_copy` in `get_shadow_mappings_by_category()`.
- `kamma/upstream_sync/scripts/prep_analyzer.py`
  - Changed `generated_at` to actual current local ISO timestamp instead of `accepted_sync.json` date.
- `kamma/upstream_sync/scripts/execute_sync.py`
  - Removed `Optional`.
  - Added hard failures for dirty working tree, non-`sbs-ru` starting branch, and invalid/missing prep manifest.
- `tests/check_shadow_modifications.py`
  - Added Tamil label for `tamil_copy`.
- `tests/test_execute_sync.py`
  - Added preflight failure tests for dirty tree, invalid manifest, and wrong branch.
- `tests/test_prep_analyzer.py`
  - Added Tamil mapping case.
  - Corrected stale category expectation for `exporter/webapp/main.py` from `dps_copy` to `russian_copy`.
  - Asserted `generated_at` is no longer copied from accepted-sync date.
- `tests/test_shadow_parity.py`
  - Included `tamil_copies` in Python parity pairs.
  - Added typed whitelist helper.
  - Added SMD-backed whitelist entries for intentional RU idiom and Tamil lookup divergences.
- `tests/test_verify_smd_coverage.py`
  - Added Tamil SMD coverage test and type annotations.
- `tests/test_upstream_sync_docs_policy.py`
  - New guard test ensuring `guide.md` does not authorize "then commit" wording.

## Test Evidence

Passed:
- `uv run ruff check --fix kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/execute_sync.py tests/check_shadow_modifications.py tests/test_shadow_parity.py tests/test_execute_sync.py tests/test_prep_analyzer.py tests/test_verify_smd_coverage.py tests/test_upstream_sync_docs_policy.py`
- `uv run ruff format kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/execute_sync.py tests/check_shadow_modifications.py tests/test_shadow_parity.py tests/test_execute_sync.py tests/test_prep_analyzer.py tests/test_verify_smd_coverage.py tests/test_upstream_sync_docs_policy.py`
- `uv run pyright kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/execute_sync.py tests/check_shadow_modifications.py tests/test_shadow_parity.py tests/test_execute_sync.py tests/test_prep_analyzer.py tests/test_verify_smd_coverage.py tests/test_upstream_sync_docs_policy.py`
- `uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/execute_sync.py tests/check_shadow_modifications.py tests/test_shadow_parity.py tests/test_execute_sync.py tests/test_prep_analyzer.py tests/test_verify_smd_coverage.py tests/test_upstream_sync_docs_policy.py`
- `uv run pytest tests/test_prep_analyzer.py tests/test_verify_smd_coverage.py tests/test_execute_sync.py tests/test_upstream_sync_docs_policy.py tests/test_shadow_parity.py -v` — 47 passed.
- `uv run python3 kamma/upstream_sync/scripts/validate_registry.py`
- `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py`
- `uv run python3 tests/check_shadow_modifications.py`
- `uv run pytest tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py -v` — 205 passed, 1 skipped.

## Errors, Issues, and Repeated Mistakes

- `~/agents/protocol-fix.md` was referenced by project instructions but does not exist locally, so it could not be followed.
- Initial upstream-sync review found `validate_registry.py` failing because `exporter/sutta_central/sc_dict.json` was both under a skipped folder and listed as unique.
- Initial focused tests had a stale failure: `tests/test_prep_analyzer.py` expected `exporter/webapp/main.py` to be `dps_copy`; actual mapping is `russian_copy`.
- After Tamil parity was enabled, `tests/test_shadow_parity.py` exposed two intentional SMD-documented divergences:
  - `db/families/family_idiom_ru.py` intentionally omits upstream `update_db_cache()`.
  - `db/tpd/tpd_to_lookup.py` intentionally omits root-processing helpers from `db/epd/epd_to_lookup.py`.
  These were added to the test whitelist, not ported into production code.
- `pyrefly` initially reported type warnings in touched tests/helper code. Annotations were tightened until `pyrefly --min-severity warn` passed.
- Existing unrelated dirty/untracked resources remain untouched: `resources/*` entries and this thread folder.

## Current State

Implementation and validation are complete. No git commit was made.

Recommended commit message:

```text
#sync tooling: enforce tamil coverage and preflight gates
```


Session 3

## Scope

Reviewed the upstream sync workflow separately after the previous improvement sessions, then implemented the approved high-value safeguards:
- Prevent `execute_sync.py` from running against stale `prep_manifest.json` data.
- Enforce `discuss_paths` as a hard stop before automated pull execution.
- Strengthen registry validation for strict-shadow mapping shape and upstream source existence.
- Make docs parity fail on unexpected `docs_rus/` local-only files.
- Remove duplicate cross-section overlap reporting in `validate_registry.py`.

Also resolved the stale external fix-protocol question:
- The old instruction referenced `~/agents/protocol-fix.md`.
- The actual file path is now `~/.agents/protocol-fix.md`.
- Decision: do not keep or replace the external protocol reference. The global TDD rules and local `AGENTS.md` rules are already explicit enough; the external reference is redundant and creates stale-path risk.

## Files Changed

- `kamma/upstream_sync/scripts/sync_runtime.py`
  - Extended `verify_manifest()` with optional accepted-sync state validation, target SHA validation, and `allow_discuss`.
  - When `allow_discuss=False`, any non-empty `discuss_paths` now exits with failure before automated pull.
- `kamma/upstream_sync/scripts/execute_sync.py`
  - Fetches and resolves the target upstream ref before manifest validation.
  - Validates `prep_manifest.json` against the current accepted sync state and resolved target SHA.
  - Resets `as_upstream` to the verified manifest target SHA instead of a moving ref.
- `kamma/upstream_sync/scripts/validate_registry.py`
  - Added strict-shadow mapping schema validation for `russian_copies`, `sbs_copies`, `dps_copies`, and `tamil_copies`.
  - Validates mapped upstream source paths exist when a repo root is provided.
  - Removed duplicated overlap reporting in CLI output.
- `kamma/upstream_sync/scripts/check_docs_parity.py`
  - Added unexpected local-only docs detection.
  - Returns nonzero if `docs_rus/` contains a file with no `docs/` counterpart and no `EXPECTED_LOCAL_ONLY` entry.
- `tests/test_execute_sync.py`
  - Added coverage for manifest-target SHA execution and updated manifest verification expectations.
- `tests/test_sync_state.py`
  - Added tests for rejecting discuss paths, accepted-state mismatch, and target SHA mismatch.
- `tests/test_validate_registry.py`
  - Added tests for invalid strict-shadow mapping shape, non-string source path, and missing upstream source path.
- `tests/test_check_docs_parity.py`
  - New focused test for unexpected docs local-only classification.

## Test Evidence

Initial RED phase:
- `uv run pytest tests/test_execute_sync.py tests/test_sync_state.py tests/test_validate_registry.py tests/test_check_docs_parity.py -v`
  - Failed during collection because the new expected APIs did not exist yet:
    - `validate_shadow_mapping`
    - `find_unexpected_local_files`

Passed after implementation:
- `uv run ruff check --fix kamma/upstream_sync/scripts/sync_runtime.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/validate_registry.py kamma/upstream_sync/scripts/check_docs_parity.py tests/test_execute_sync.py tests/test_sync_state.py tests/test_validate_registry.py tests/test_check_docs_parity.py`
- `uv run ruff format kamma/upstream_sync/scripts/sync_runtime.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/validate_registry.py kamma/upstream_sync/scripts/check_docs_parity.py tests/test_execute_sync.py tests/test_sync_state.py tests/test_validate_registry.py tests/test_check_docs_parity.py`
- `uv run pyright kamma/upstream_sync/scripts/sync_runtime.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/validate_registry.py kamma/upstream_sync/scripts/check_docs_parity.py tests/test_execute_sync.py tests/test_sync_state.py tests/test_validate_registry.py tests/test_check_docs_parity.py` — 0 errors.
- `uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/sync_runtime.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/validate_registry.py kamma/upstream_sync/scripts/check_docs_parity.py tests/test_execute_sync.py tests/test_sync_state.py tests/test_validate_registry.py tests/test_check_docs_parity.py` — 0 errors.
- `uv run pytest tests/test_execute_sync.py tests/test_sync_state.py tests/test_validate_registry.py tests/test_check_docs_parity.py tests/test_prep_analyzer.py tests/test_verify_smd_coverage.py tests/test_upstream_sync_docs_policy.py -v` — 50 passed.
- `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` — passed.
- `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` — passed.
- `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py` — passed.

## Errors, Issues, and Repeated Mistakes

- The old `~/agents/protocol-fix.md` path was stale. The actual current path is `~/.agents/protocol-fix.md`.
- The external fix protocol is no longer needed if global `AGENTS.md` keeps the existing TDD/testing rules and local project `AGENTS.md` keeps project-specific validation details.
- `pyright` initially caught `discuss_paths` as a generic `object` in `sync_runtime.py`; fixed by runtime type narrowing.
- `pyrefly` initially caught:
  - an old unnecessary `str()` conversion in `validate_registry.py`;
  - an inferred test manifest type that needed `dict[str, object]`.
  Both were fixed.
- Existing unrelated dirty/untracked resources remain untouched:
  - `resources/*`
  - this thread folder
  - pre-existing untracked `tests/test_upstream_sync_docs_policy.py`

## Current State

Session 3 implementation and validation are complete. No git commit was made.

Recommended commit message:

```text
#sync tooling: block stale manifests and discuss pulls
```


Session 4

## Scope

Implemented the approved follow-up upstream-sync improvements after separate review:
- Add pre-sync DPS localization backup to `scripts/cl_dps/dpd-kamma-sync`.
- Auto-commit only the generated DPS backup TSV files from that wrapper.
- Preserve the prohibition on agents committing manually; the commit is now script behavior requested by the user.
- Report mapped shadow/inspired actions for deleted upstream source files in Stage 1 manifests.
- Require `execute_sync.py` to receive a thread directory so `prep_manifest.json` validation cannot be skipped.
- Enforce all required top-level sections in `registry.json`, including `tamil_copies`.
- Remove stale backup TODO from the canonical guide now that the wrapper handles backup.
- Replace stale `grep -r` guide wording with `rg`.

## Files Changed

- `scripts/cl_dps/dpd-kamma-sync`
  - Runs `uv run python3 scripts/backup/backup_dps.py` before initializing the Kamma sync thread.
  - Aborts if staged changes already exist.
  - Stages and commits only:
    - `db/backup_tsv/russian.tsv`
    - `db/backup_tsv/sbs.tsv`
    - `db/backup_tsv/tamil.tsv`
    - `db/backup_tsv/ru_roots.tsv`
  - Uses commit message `backup dps data`.
  - Continues to run `scripts/bash/dpd_init_sync.py` after backup handling.
- `kamma/upstream_sync/scripts/prep_analyzer.py`
  - Deleted upstream paths now still check strict-shadow and inspired mappings.
  - If a deleted upstream source maps to local RU/SBS/DPS/Tamil/inspired paths, the deleted source is included in `mapped_actions`.
- `kamma/upstream_sync/scripts/execute_sync.py`
  - Fails immediately when called without `thread_dir`.
  - Prevents real sync execution without manifest verification.
- `kamma/upstream_sync/scripts/validate_registry.py`
  - Added `REQUIRED_TOP_LEVEL_SECTIONS`.
  - Added validation that every required registry section is explicitly present.
- `kamma/upstream_sync/guide.md`
  - Removed stale hidden DPS backup TODO.
  - Replaced `grep -r` template-audit wording with `rg`.
- `tests/test_prep_analyzer.py`
  - Added coverage for deleted upstream source files with mapped local shadows.
- `tests/test_execute_sync.py`
  - Added coverage that `execute_sync(None)` fails before `GitContext` is created.
- `tests/test_validate_registry.py`
  - Added `tamil_copies` to the base fixture.
  - Added coverage for missing required top-level registry sections.
- `tests/test_upstream_sync_docs_policy.py`
  - Added guard against reintroducing the stale backup TODO or `grep -r` wording.

## Test Evidence

Initial RED phase:
- `uv run pytest tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_validate_registry.py -v`
  - Failed exactly on the missing expected behaviors:
    - deleted mapped source missing from `mapped_actions`;
    - `execute_sync(None)` still created `GitContext`;
    - missing `tamil_copies` was not rejected.

Passed after implementation:
- `uv run pytest tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_validate_registry.py -v` — 29 passed.
- `uv run ruff check --fix kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/validate_registry.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_validate_registry.py tests/test_upstream_sync_docs_policy.py` — passed.
- `uv run ruff format kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/validate_registry.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_validate_registry.py tests/test_upstream_sync_docs_policy.py` — 7 files left unchanged.
- `uv run pyright kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/validate_registry.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_validate_registry.py tests/test_upstream_sync_docs_policy.py` — 0 errors, 0 warnings, 0 informations.
- `uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/validate_registry.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_validate_registry.py tests/test_upstream_sync_docs_policy.py` — 0 errors, 3 suppressed.
- `uv run pytest tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_validate_registry.py tests/test_upstream_sync_docs_policy.py -v` — 31 passed.
- `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` — passed.
- `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` — passed.
- `git diff --check -- scripts/cl_dps/dpd-kamma-sync kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/validate_registry.py kamma/upstream_sync/guide.md tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_validate_registry.py tests/test_upstream_sync_docs_policy.py` — passed.

## Errors, Issues, and Repeated Mistakes

- User clarified that autonomous agent commits remain prohibited, but scripts intentionally developed for user workflows may run `git commit` when their behavior is explicit and reviewed.
- The backup wrapper now commits backup TSV files itself; no agent-side commit was made during this session.
- Existing unrelated dirty/untracked resources remain untouched:
  - `resources/*`
- Existing local change from this session remains unstaged:
  - `scripts/cl_dps/dpd-kamma-sync`
  - `kamma/upstream_sync/guide.md`
  - `kamma/upstream_sync/scripts/prep_analyzer.py`
  - `kamma/upstream_sync/scripts/execute_sync.py`
  - `kamma/upstream_sync/scripts/validate_registry.py`
  - `tests/test_prep_analyzer.py`
  - `tests/test_execute_sync.py`
  - `tests/test_validate_registry.py`
  - `tests/test_upstream_sync_docs_policy.py`
  - `kamma/threads/upstream_sync_improvment/handoff.md`

## Current State

Session 4 implementation and validation are complete. No git commit was made by the agent.

Recommended commit message:

```text
#sync tooling: strengthen pre-sync backup and manifests
```


Session 5

## Scope

Implemented the approved follow-up safeguards from the separate upstream-sync review:
- Keep the DPS backup wrapper commit message as `backup dps data`.
- Make `execute_sync.py` fail if post-sync assertions fail.
- Make `finalize_accepted_sync.py` verify the prep manifest before advancing `accepted_sync.json`.
- Clarify that Stage 4.A ADVANCED reads FAST-produced docs parity evidence instead of running commands.
- Clarify that Stage 1 stops before `execute_sync.py` when `prep_manifest.json.discuss_paths` is non-empty.

No git commit was made.

## Files Changed

- `kamma/threads/upstream_sync_improvment/handoff.md`
  - Corrected Session 4 backup wrapper commit message to `backup dps data`.
  - Added this Session 5 handoff.
- `kamma/upstream_sync/scripts/execute_sync.py`
  - Returns failure when `scripts/bash/dpd-sync-assertions.sh` exits nonzero.
- `kamma/upstream_sync/scripts/finalize_accepted_sync.py`
  - Added `finalize_accepted_sync()` helper.
  - Calls `verify_manifest(thread_dir, allow_discuss=False)` before loading the manifest or writing `accepted_sync.json`.
- `kamma/upstream_sync/guide.md`
  - Added explicit Stage 1 stop before `execute_sync.py` if `prep_manifest.json.discuss_paths` is non-empty.
  - Moved Stage 4.A command execution responsibility to FAST and made ADVANCED consume `docs_parity_report.md` and FAST-provided diffs.
- `kamma/upstream_sync/README.md`
  - Updated quick-start Stage 4.A wording to say ADVANCED reads FAST-produced parity output.
- `kamma/upstream_sync/stages/prep.md`
  - Added the discuss-path stop check to the Stage 1 checklist.
- `kamma/upstream_sync/templates/sync_thread_plan.md`
  - Added the discuss-path stop check.
  - Clarified Stage 4.A reads FAST output and requests FAST if diffs are missing.
- `tests/test_execute_sync.py`
  - Added coverage for assertion-script failure returning nonzero.
  - Mocked assertion-script absence in the normal success-path test.
- `tests/test_finalize_accepted_sync.py`
  - New focused test proving finalization refuses invalid manifests and does not write accepted state.
- `tests/test_upstream_sync_docs_policy.py`
  - Added guards for Stage 4.A command ownership and discuss-path stop wording.

## Test Evidence

Initial RED phase:
- `uv run pytest tests/test_execute_sync.py::TestExecuteSync::test_execute_sync_fails_when_assertions_fail tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py::test_guide_keeps_stage_4a_command_execution_with_fast tests/test_upstream_sync_docs_policy.py::test_guide_stops_before_execute_sync_when_discuss_paths_exist -v`
  - Failed during collection because `finalize_accepted_sync()` did not exist yet.

Passed after implementation:
- `uv run pytest tests/test_execute_sync.py::TestExecuteSync::test_execute_sync_fails_when_assertions_fail tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py::test_guide_keeps_stage_4a_command_execution_with_fast tests/test_upstream_sync_docs_policy.py::test_guide_stops_before_execute_sync_when_discuss_paths_exist -v` — 4 passed.
- `uv run pytest tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_sync_state.py tests/test_upstream_sync_docs_policy.py tests/test_prep_analyzer.py tests/test_validate_registry.py tests/test_check_docs_parity.py tests/test_verify_smd_coverage.py -v` — 57 passed.
- `uv run ruff check --fix kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/finalize_accepted_sync.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py` — passed.
- `uv run ruff format kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/finalize_accepted_sync.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py` — 5 files left unchanged.
- `uv run pyright kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/finalize_accepted_sync.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py` — 0 errors, 0 warnings, 0 informations.
- `uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/finalize_accepted_sync.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py` — 0 errors.
- `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` — passed.
- `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` — passed.
- `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py` — passed.
- `git diff --check -- kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/finalize_accepted_sync.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py kamma/upstream_sync/guide.md kamma/upstream_sync/README.md kamma/upstream_sync/stages/prep.md kamma/upstream_sync/templates/sync_thread_plan.md kamma/threads/upstream_sync_improvment/handoff.md` — passed.

## Errors, Issues, and Repeated Mistakes

- Existing success-path `execute_sync` test accidentally ran the real `scripts/bash/dpd-sync-assertions.sh`. After assertion failures became fatal, this surfaced as a test failure. Fixed the test harness by mocking `Path.exists()` to make the assertion script absent in that success-path unit test.
- The larger suggestion to replace `checkout as_upstream` + `reset --hard` was intentionally not implemented because it is a broader behavioral rewrite and not the simplest safe fix for this pass.
- Existing unrelated dirty/untracked resources remain untouched:
  - `resources/*`

## Current State

Session 5 implementation and validation are complete. No git commit was made by the agent.

Recommended commit message:

```text
#sync tooling: tighten sync finalization gates
```
