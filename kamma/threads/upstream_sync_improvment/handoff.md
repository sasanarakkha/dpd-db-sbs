# Upstream Sync Improvement Handoff

This file is intentionally short. Keep it as future-session context, not as a
session transcript. Record what changed, why it matters, current state, and
mistakes to avoid.

## Purpose

Improve `kamma/upstream_sync` so upstream syncs are safer, restartable,
model-boundary aware, and better validated for RU/SBS/DPS/Tamil localized files.

## Core Design Decisions

- The workflow is a 5-stage upstream-sync process with explicit FAST/ADVANCED
  responsibility boundaries.
- FAST owns mechanical command execution and evidence generation.
- ADVANCED owns analysis, planning, acceptance decisions, and reading evidence.
- If either model crosses its responsibility boundary, stop and write a
  restartable handoff.
- `prep_manifest.json` is the central sync contract. Execution and finalization
  must verify it before changing sync state.
- `prep_manifest.json.discuss_paths` is a hard stop before `execute_sync.py`.
- `prep_manifest.json.blocker_paths` is a hard stop before `execute_sync.py`.
  It is used for paths that need classification or policy resolution before an
  automated upstream pull.
- `execute_sync.py` must use a thread directory and pin `as_upstream` directly
  to the verified manifest target SHA with `git update-ref`, not via branch
  checkout plus `reset --hard`, and never from an unchecked moving ref.
- `finalize_accepted_sync.py` must verify the manifest against current accepted
  sync state before advancing `accepted_sync.json`; it writes the full target
  SHA and uses Stage 5 acceptance wording.
- Autonomous agent commits remain prohibited. The reviewed DPS wrapper backup
  behavior is the only known scripted commit exception, with exact message:
  `backup dps data`.
- `dps_copies` is the single category for mixed/shared fork shadows. Do not list
  one local path in multiple locale categories.
- SMD `Category` must exactly match the path's category in
  `kamma/upstream_sync/registry.json`.

## Completed Improvements

- Workflow docs now describe the 5-stage FAST/ADVANCED model, Stage 1 API health
  checks, Stage 4 docs parity, restartable handoffs, and current sync scope.
- Runtime gates now fail fast on unsafe branch/state, invalid or stale manifests,
  unresolved `discuss_paths`, and failed post-sync assertions.
- Metadata parsing is centralized and typed through `sync_schema.py`; registry,
  SMD, manifest, mapped actions, and accepted sync state are validated more
  strictly.
- Prep analysis now handles deleted upstream sources, rename facts, and
  `local_target_path` for mapped actions without removing `local_path`.
- Docs parity now uses the thread manifest range when available, keeps fallback
  standalone behavior, reports stale-doc diffs, and handles report dirs outside
  the repo.
- Registry/SMD tooling now includes Tamil coverage, correct DPS/Tamil scaffold
  categories, SMD category alignment checks, and the single-category DPS shadow
  policy.
- Local rules now require every new or changed shadow file to update both
  `registry.json` and the matching `kamma/upstream_sync/smd/*.md`.
- DPS wrapper backup behavior was added to `scripts/cl_dps/dpd-kamma-sync`.
- Stage 1 now writes `prep_manifest.json.blocker_paths` and a
  `prep_report.md` blocker section. New unmapped upstream additions and deleted
  upstream paths block `execute_sync.py` until resolved.
- `execute_sync.py` now pins `as_upstream` with
  `git update-ref refs/heads/as_upstream <verified_sha>` while staying on
  `sbs-ru`; it no longer checks out `as_upstream` or runs `reset --hard`.
- `finalize_accepted_sync.py` now resolves the accepted target to a full SHA
  before writing `accepted_sync.json`, and its default notes say Stage 5.
- Workflow docs, stage checklist, and thread template now document the
  `blocker_paths` gate and direct `as_upstream` pinning.
- Shadow modification checking now uses the latest `#sync: upstream pull`
  commit as its baseline, not any older `sync:` commit.
- `kamma/upstream_sync/reviewed_shadow_noops.json` now records explicit,
  reviewed decisions not to port specific upstream shadow changes. Entries must
  match sync commit, source, shadow, changed paths, and reason exactly.
- Stage 5 documentation now tells ADVANCED to write FAST handoff instructions
  for `finalize_accepted_sync.py`, not to run finalization directly.
- `unique_paths` is documented as cleanup inventory outside the sync process,
  and obsolete `unique_local` SMD entries were removed from
  `kamma/upstream_sync/smd/scripts.md`.
- `tests/smoke_test_sync.py` now isolates config writes to
  `temp/smoke_config.ini`; it no longer mutates `config.ini`.
- Accepted sync and prep manifest SHA fields now require full 40-character
  lowercase git SHAs; `BOOTSTRAP_REQUIRED` remains allowed only for accepted
  sync bootstrap state. `accepted_sync.json` was updated from `44a8a005` to
  `44a8a00556cce9bd3874a94efb5dfaceaaf20a66`.
- SMD coverage now fails on SMD entries not backed by sync-relevant registry
  paths. Obsolete SMD entries for `no_sync_files` and `unique_paths` inventory
  were removed so coverage is exactly 67 registry-backed entries.
- `execute_sync.py` now rejects absolute, parent-traversal, backslash, blank,
  and whitespace-padded exclusion paths before they can be restored or removed.
- `check_docs_parity.py <thread_dir>` now reports missing or invalid
  `prep_manifest.json` cleanly instead of tracebacking.

## Main Files

- Docs/templates/stages under `kamma/upstream_sync/`.
- Registry/SMD: `kamma/upstream_sync/registry.json`,
  `kamma/upstream_sync/smd/*.md`.
- Reviewed no-op ledger:
  `kamma/upstream_sync/reviewed_shadow_noops.json`.
- Scripts: `prep_analyzer.py`, `execute_sync.py`, `finalize_accepted_sync.py`,
  `sync_runtime.py`, `sync_state.py`, `sync_schema.py`, `validate_registry.py`,
  `verify_smd_coverage.py`, `check_docs_parity.py`, `gen_smd_scaffold.py`.
- Tests: focused upstream-sync, registry, SMD, prep analyzer, docs parity, and
  docs policy tests under `tests/`.

## Validation Baseline

For future related changes, run the targeted tests for touched behavior plus:

```fish
uv run ruff check --fix <changed-files>
uv run ruff format <changed-files>
uv run pyright <changed-files>
uv run --with pyrefly pyrefly check --min-severity warn <changed-files>
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py
uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py
git diff --check -- <changed-files>
```

Recent broad upstream-sync suites passed in previous sessions, including 77,
103, and 107 test focused runs. Do not reuse these as current proof; rerun the
relevant tests after any new change.

Most recent validation for blocker/ref-pinning hardening:

```fish
uv run ruff check --fix kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/sync_runtime.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/finalize_accepted_sync.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py
uv run ruff format kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/sync_runtime.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/finalize_accepted_sync.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py
uv run pyright kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/sync_runtime.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/finalize_accepted_sync.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py
uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/sync_runtime.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/finalize_accepted_sync.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py
uv run pytest tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_gen_smd_scaffold.py tests/test_upstream_sync_docs_policy.py tests/test_registry_category_naming.py -v
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py
git diff --check -- kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/sync_runtime.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/finalize_accepted_sync.py kamma/upstream_sync/guide.md kamma/upstream_sync/templates/sync_thread_plan.md kamma/upstream_sync/stages/prep.md tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_upstream_sync_docs_policy.py
```

Result: all passed. The focused upstream-sync suite reported 118 passed.

Most recent validation for shadow no-op ledger, unique-path cleanup, Stage 5
wording, and smoke-test config isolation:

```fish
uv run ruff check --fix tests/check_shadow_modifications.py tests/test_check_shadow_modifications.py tests/test_upstream_sync_docs_policy.py tests/test_verify_smd_coverage.py tests/test_smoke_test_sync.py tests/smoke_test_sync.py
uv run ruff format tests/check_shadow_modifications.py tests/test_check_shadow_modifications.py tests/test_upstream_sync_docs_policy.py tests/test_verify_smd_coverage.py tests/test_smoke_test_sync.py tests/smoke_test_sync.py
uv run pyright tests/check_shadow_modifications.py tests/test_check_shadow_modifications.py tests/test_upstream_sync_docs_policy.py tests/test_verify_smd_coverage.py tests/test_smoke_test_sync.py tests/smoke_test_sync.py
uv run --with pyrefly pyrefly check --min-severity warn tests/check_shadow_modifications.py tests/test_check_shadow_modifications.py tests/test_upstream_sync_docs_policy.py tests/test_verify_smd_coverage.py tests/test_smoke_test_sync.py tests/smoke_test_sync.py
uv run pytest tests/test_check_shadow_modifications.py tests/test_upstream_sync_docs_policy.py tests/test_verify_smd_coverage.py tests/test_smoke_test_sync.py -q
uv run pytest tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_upstream_sync_docs_policy.py tests/test_registry_category_naming.py tests/test_check_shadow_modifications.py tests/test_smoke_test_sync.py -q
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py
uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py
git diff --check -- kamma/upstream_sync/README.md kamma/upstream_sync/guide.md kamma/upstream_sync/infrastructure.md kamma/upstream_sync/smd/scripts.md kamma/upstream_sync/stages/prep.md kamma/upstream_sync/templates/sync_thread_plan.md kamma/upstream_sync/templates/sync_thread_spec.md kamma/upstream_sync/reviewed_shadow_noops.json tests/check_shadow_modifications.py tests/smoke_test_sync.py tests/test_check_shadow_modifications.py tests/test_upstream_sync_docs_policy.py tests/test_verify_smd_coverage.py tests/test_smoke_test_sync.py
```

Result: all passed. Focused no-op/doc/smoke tests reported 29 passed. Broader
focused upstream-sync suite reported 127 passed. The live command
`uv run python3 tests/check_shadow_modifications.py` intentionally still fails
until the two prior-sync warnings listed under Current State are either ported
or recorded in the reviewed no-op ledger.

Most recent validation for full-SHA, SMD stale-entry, exclusion-path, and docs
manifest-error hardening:

```fish
uv run ruff check --fix kamma/upstream_sync/scripts/check_docs_parity.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_prep_analyzer.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_verify_smd_coverage.py
uv run ruff format kamma/upstream_sync/scripts/check_docs_parity.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_prep_analyzer.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_verify_smd_coverage.py
uv run pyright kamma/upstream_sync/scripts/check_docs_parity.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_prep_analyzer.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_verify_smd_coverage.py
uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/check_docs_parity.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_prep_analyzer.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_verify_smd_coverage.py
uv run pytest tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_upstream_sync_docs_policy.py tests/test_registry_category_naming.py tests/test_check_shadow_modifications.py -q
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py
uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py
git diff --check -- kamma/upstream_sync/accepted_sync.json kamma/upstream_sync/scripts/check_docs_parity.py kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/verify_smd_coverage.py kamma/upstream_sync/smd/root.md kamma/upstream_sync/smd/scripts.md tests/test_check_docs_parity.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_prep_analyzer.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_verify_smd_coverage.py
```

Result: all passed. The focused upstream-sync suite reported 135 passed.
Standalone docs parity passed. `verify_smd_coverage.py` now reports 67
registry paths and 67 SMD entries, with no unregistered SMD entries.

## Mistakes To Avoid

- Do not preserve stale external protocol paths. The old `~/agents/...` path was
  wrong; project/global rules already cover the needed behavior.
- Do not list one local path in more than one registry category.
- Do not let SMD `Category` drift from `registry.json`.
- Use `dps_copies` for mixed/shared fork shadows; do not classify them as
  locale-specific copies.
- Keep Tamil in helper and test coverage; do not assume it is automatic.
- Do not reintroduce the old contradiction where
  `exporter/sutta_central/sc_dict.json` was both skipped and unique.
- `exporter/webapp/main.py` maps as `russian_copy`, not `dps_copy`.
- Some parity divergences are intentional and SMD-documented; do not port them
  without review. Known examples: `db/families/family_idiom_ru.py` omits
  upstream `update_db_cache()`, and `db/tpd/tpd_to_lookup.py` omits root helpers
  from `db/epd/epd_to_lookup.py`.
- Keep manifest and runtime typing explicit; `pyright` and `pyrefly` previously
  caught real weaknesses here.
- In tests, mock assertion-script presence and execution deliberately. A past
  success-path `execute_sync` test accidentally ran the real assertion script.
- The replacement of `checkout as_upstream` plus `reset --hard` is now
  implemented and covered by `tests/test_execute_sync.py`. Do not reintroduce
  branch switching unless there is a specific failure with direct ref pinning.
- Do not rely only on `discuss_paths` as the pre-execution hard stop.
  `blocker_paths` must also be empty before `execute_sync.py` runs.
- `check_docs_parity.py` must handle report dirs outside the repo.
- Accepted sync and prep manifest SHAs must stay full-length 40-character
  lowercase SHAs. Do not reintroduce short SHA fixtures in sync-state tests.
- Do not add SMD entries for paths outside sync-relevant registry categories.
  `unique_paths` and `no_sync_files` are intentionally not SMD-covered.
- Keep `execute_sync.py` exclusion paths repo-relative; never allow absolute
  paths or `..` traversal in `run_exclusions.txt` or registry exclusions.
- `check_docs_parity.py <thread_dir>` should fail cleanly if the thread
  manifest is missing or malformed; do not let the traceback return.
- Do not add reviewed no-op ledger entries without inspecting the upstream diff
  and getting an explicit acceptance decision. If the user says no action is
  needed but gives no specific reason, use this exact reason:
  `User reviewed and confirmed this upstream change does not need to be ported to the shadow.`
- Do not use `unique_paths` for shadow no-op decisions. `unique_paths` is only
  cleanup inventory and is outside the monthly shadow sync process.
- Do not mark the current two shadow warnings reviewed without reviewing their
  upstream diffs; the checker exposed prior-sync decisions that were not yet
  recorded.
- Patch against current file text. A past patch failed because docs wording had
  already diverged.
- Avoid complex multiline `rg` regexes for verification; use simple literal
  searches when possible.
- Preserve unrelated dirty/untracked `resources/*` entries unless the user
  explicitly asks to handle them.

## Current State

- Previous upstream-sync improvement sessions were implemented and validated.
- A separate review found no major redesign needed; the current
  registry + SMD + manifest + FAST/ADVANCED hard-stop architecture remains the
  recommended design.
- The separate review's recommended hardening was implemented: manifest
  `blocker_paths`, direct `as_upstream` pinning, full-SHA finalization, and
  Stage 5 finalization wording.
- The later standalone review hardening was implemented except for the two live
  shadow warnings: full-SHA schema enforcement, stale SMD entry rejection,
  repo-relative sync exclusion validation, and clean docs manifest errors.
- The typed-hardening thread was finalized and archived at
  `kamma/archive/20260531_upstream_sync_typed_hardening`.
- This legacy thread directory currently exists as a compact handoff location.
  Do not assume `spec.md` or `plan.md` exist here; inspect the directory first.
- `reviewed_shadow_noops.json` exists and is intentionally empty until a human
  reviewed no-port decision is recorded.
- The live shadow modification check currently fails on two prior-sync warnings:
  `exporter/kindle/epub/` to `exporter/kindle/ru_components/epub/` for
  `exporter/kindle/epub/OEBPS/Text/titlepage.xhtml`, and
  `db/backup_tsv/backup_dpd_headwords_and_roots.py` to
  `scripts/backup/backup_dps.py` for
  `db/backup_tsv/backup_dpd_headwords_and_roots.py`.
- These warnings are linked in `registry.json`; they are not unique-path cleanup
  items. Resolve them by porting the upstream change or adding exact reviewed
  no-op entries after review.
- The smoke sync test now uses temporary config isolation. Do not reintroduce
  writes to `config.ini`.
- No agent-side git commit was made.
- User manual review may still be needed for any uncommitted working-tree
  changes.
- Current uncommitted working-tree changes from this improvement touch
  `kamma/upstream_sync/accepted_sync.json`, four upstream-sync scripts, two SMD
  files, and focused tests for sync schema/state, prep analyzer, execute sync,
  finalize accepted sync, SMD coverage, and docs parity.

## Errors, Issues, and Repeated Mistakes

- Red phase was confirmed: the new docs-policy test failed before guide/template
  wording was added.
- Real `execute_sync.py` was not run because it mutates git state; behavior was
  validated through focused unit tests and static checks.
- The corrected latest-sync baseline exposed two existing shadow warnings from
  the previous upstream sync. They were not fixed in this scope because the user
  asked for the no-op recording mechanism and handoff update, not porting those
  changes.
- The live shadow check failure is expected while
  `reviewed_shadow_noops.json` is empty and the two warnings remain unported.
- Red phase was confirmed for this hardening: new tests initially failed on
  missing `check_unregistered_smd_entries` and `validate_repo_relative_paths`.
- Stricter SMD validation exposed 12 obsolete SMD entries for non-sync targets;
  those entries were removed, not reclassified into the registry.
- `tests/test_sync_state.py` also needed full-SHA fixtures after schema
  enforcement; otherwise the broader focused suite would fail.
- Existing untracked/dirty `resources/*` entries remain unrelated and were not
  touched.
- Keep future handoff updates short. This file is summary context, not a
  transcript.

## Recent Recommended Commit Messages

```text
#sync tooling: harden sync metadata validators
#sync tooling: add reviewed shadow noop ledger
#sync docs: clarify unique cleanup inventory
#sync tooling: block unsafe prep paths and pin upstream ref
#sync docs: enforce single dps shadow category
fix(upstream-sync): pin docs parity to manifest range
refactor(upstream-sync): harden typed metadata validation
```

Older messages if history reconstruction is needed:

```text
#sync docs: clarify stage wording and parity report path
#sync tooling: tighten sync finalization gates
#sync workflow: clarify fast/advanced handoffs
#sync tooling: enforce tamil coverage and preflight gates
#sync tooling: block stale manifests and discuss pulls
#sync tooling: strengthen pre-sync backup and manifests
```

## Restart Prompt

```text
Continue upstream sync improvement work. First read:
1. kamma/threads/upstream_sync_improvment/handoff.md
2. kamma/upstream_sync/guide.md
3. kamma/upstream_sync/registry.json
4. kamma/upstream_sync/reviewed_shadow_noops.json
5. tests/check_shadow_modifications.py
6. the specific upstream-sync script/docs/tests relevant to the requested task

Do not broaden scope. Preserve unrelated resources/* dirty state. Rerun targeted
tests and validation commands for any touched files before reporting completion.
```
