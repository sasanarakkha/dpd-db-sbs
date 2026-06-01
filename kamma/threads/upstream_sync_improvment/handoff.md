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
- `execute_sync.py` now also rejects option-like exclusion paths and git
  pathspec metacharacters, preserves raw `run_exclusions.txt` whitespace for
  validation, and passes restored/removed paths after `--`.
- `verify_smd_coverage.py` now rejects unknown SMD `Sync Rule` values.
- The two prior-sync shadow warnings are now exact reviewed no-op entries:
  RU Kindle titlepage update date/time is local-build metadata, and DPS backup
  TSVs intentionally do not mirror upstream chunk splitting because they are
  small localized backups.
- SMD guidance now documents both no-op rules so future syncs do not attempt to
  port those date/time or chunking-only upstream changes.
- Standalone docs-hygiene cleanup was implemented after review: the guide now
  pre-authorizes `rg` instead of `grep`/`find`, `archive_improvements.md` is
  explicitly historical-only, `stages/` is marked legacy Stage 1-3 reference
  material, and the empty `kamma/upstream_sync/suggestions.md` file was deleted.
- Standalone June 2026 review hardening was implemented: SMD `Category` values
  now use exact `registry.json` category keys, the `scripts/cl_dps/` autonomous
  commit exception is explicitly bounded to human-run Bash scripts, registry path
  safety is validated before sync execution, reviewed shadow no-op entries require
  full SHAs and repo-relative paths, and `init_sync_thread.py` prints the exact
  Stage 1 FAST restart prompt.
- Standalone simplification cleanup was implemented after review: no-translate
  docs policy now uses only the existing HTML redirect pattern, symlink references
  were removed from active sync policy/tooling, `init_sync_thread.py` and
  `tests/check_shadow_modifications.py` now use `tools.printer`, and
  `prep_analyzer.py` now reads `git diff --name-status -z` so spaced paths and
  renames are parsed safely.

## Main Files

- Docs/templates/stages under `kamma/upstream_sync/`.
- Registry/SMD: `kamma/upstream_sync/registry.json`,
  `kamma/upstream_sync/smd/*.md`.
- Reviewed no-op ledger:
  `kamma/upstream_sync/reviewed_shadow_noops.json`.
- Scripts: `init_sync_thread.py`, `prep_analyzer.py`, `execute_sync.py`,
  `finalize_accepted_sync.py`, `sync_runtime.py`, `sync_schema.py`,
  `validate_registry.py`, `verify_smd_coverage.py`, `check_docs_parity.py`,
  `gen_smd_scaffold.py`.
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
focused upstream-sync suite reported 127 passed. At that time, the live command
`uv run python3 tests/check_shadow_modifications.py` still failed until the two
prior-sync warnings were either ported or recorded in the reviewed no-op ledger.

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

Most recent validation for exclusion-path/SMD-rule hardening and reviewed
shadow no-op documentation:

```fish
uv run pytest tests/test_execute_sync.py tests/test_verify_smd_coverage.py -q
uv run ruff check --fix kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/test_execute_sync.py tests/test_verify_smd_coverage.py
uv run ruff format kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/test_execute_sync.py tests/test_verify_smd_coverage.py
uv run pyright kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/test_execute_sync.py tests/test_verify_smd_coverage.py
uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/test_execute_sync.py tests/test_verify_smd_coverage.py
uv run pytest tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_upstream_sync_docs_policy.py tests/test_registry_category_naming.py tests/test_check_shadow_modifications.py tests/test_smoke_test_sync.py -q
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py
uv run python3 tests/check_shadow_modifications.py
uv run pytest tests/test_check_shadow_modifications.py tests/test_verify_smd_coverage.py -q
git diff --check -- kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/test_execute_sync.py tests/test_verify_smd_coverage.py kamma/upstream_sync/reviewed_shadow_noops.json kamma/upstream_sync/smd/exporter.md kamma/upstream_sync/smd/scripts.md
```

Result: all passed. Red phase was confirmed first for the new execute-sync and
SMD-rule tests. Focused hardening tests reported 27 passed; broader
upstream-sync suite reported 140 passed with one third-party aksharamukha
deprecation warning. Reviewed no-op/SMD tests reported 17 passed. The live
shadow modification check is now clean.

Most recent validation for standalone docs-hygiene cleanup:

```fish
uv run pytest tests/test_upstream_sync_docs_policy.py -q
uv run ruff check --fix tests/test_upstream_sync_docs_policy.py
uv run ruff format tests/test_upstream_sync_docs_policy.py
uv run pyright tests/test_upstream_sync_docs_policy.py
uv run --with pyrefly pyrefly check --min-severity warn tests/test_upstream_sync_docs_policy.py
uv run pytest tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_upstream_sync_docs_policy.py tests/test_registry_category_naming.py tests/test_check_shadow_modifications.py -q
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py
uv run python3 tests/check_shadow_modifications.py
rg "suggestions\\.md" kamma AGENTS.md
git diff --check -- kamma/upstream_sync tests/test_upstream_sync_docs_policy.py
```

Result: red phase confirmed first with 4 expected docs-policy failures, then all
checks passed. The focused docs-policy test reported 17 passed; the broader
focused upstream-sync suite reported 142 passed. The final `rg` search returned
no active `suggestions.md` references outside the policy test.

Most recent validation for entrypoint cleanup:

```fish
uv run pytest tests/test_execute_sync.py tests/test_upstream_sync_docs_policy.py -q
uv run ruff check --fix kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/init_sync_thread.py tests/test_execute_sync.py tests/test_upstream_sync_docs_policy.py
uv run ruff format kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/init_sync_thread.py tests/test_execute_sync.py tests/test_upstream_sync_docs_policy.py
uv run pyright kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/init_sync_thread.py tests/test_execute_sync.py tests/test_upstream_sync_docs_policy.py
uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/init_sync_thread.py tests/test_execute_sync.py tests/test_upstream_sync_docs_policy.py
uv run pytest tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_upstream_sync_docs_policy.py tests/test_registry_category_naming.py tests/test_check_shadow_modifications.py -q
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py
uv run python3 tests/check_shadow_modifications.py
uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py
git diff --check -- kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/init_sync_thread.py scripts/cl_dps/dpd-kamma-sync scripts/cl_dps/dpd-sync-folders scripts/bash/full_sync.sh scripts/bash/dpd-sync-assertions.sh scripts/bash/test_dpd_sync_assertions.sh scripts/bash/dpd_init_sync.py kamma/upstream_sync/README.md kamma/upstream_sync/guide.md kamma/upstream_sync/infrastructure.md conductor/product-guidelines.md tests/test_execute_sync.py tests/test_upstream_sync_docs_policy.py kamma/threads/upstream_sync_improvment/handoff.md
```

Result: red phase confirmed first, then all checks passed. Focused entrypoint
tests reported 37 passed; the broader upstream-sync suite reported 146 passed.
Registry, SMD coverage, shadow modification, docs parity, pyright, pyrefly,
ruff, and diff whitespace checks passed.

Most recent validation for standalone category/path/no-op/commit-rule hardening:

```fish
uv run pytest tests/test_verify_smd_coverage.py tests/test_check_shadow_modifications.py tests/test_prep_analyzer.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_validate_registry.py tests/test_upstream_sync_docs_policy.py tests/test_gen_smd_scaffold.py -q
uv run ruff check --fix kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/gen_smd_scaffold.py kamma/upstream_sync/scripts/init_sync_thread.py kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/validate_registry.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/check_shadow_modifications.py tests/test_check_shadow_modifications.py tests/test_gen_smd_scaffold.py tests/test_prep_analyzer.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_upstream_sync_docs_policy.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py
uv run ruff format kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/gen_smd_scaffold.py kamma/upstream_sync/scripts/init_sync_thread.py kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/validate_registry.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/check_shadow_modifications.py tests/test_check_shadow_modifications.py tests/test_gen_smd_scaffold.py tests/test_prep_analyzer.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_upstream_sync_docs_policy.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py
uv run pyright kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/gen_smd_scaffold.py kamma/upstream_sync/scripts/init_sync_thread.py kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/validate_registry.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/check_shadow_modifications.py tests/test_check_shadow_modifications.py tests/test_gen_smd_scaffold.py tests/test_prep_analyzer.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_upstream_sync_docs_policy.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py
uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/gen_smd_scaffold.py kamma/upstream_sync/scripts/init_sync_thread.py kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/validate_registry.py kamma/upstream_sync/scripts/verify_smd_coverage.py tests/check_shadow_modifications.py tests/test_check_shadow_modifications.py tests/test_gen_smd_scaffold.py tests/test_prep_analyzer.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_upstream_sync_docs_policy.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py
uv run pytest tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_upstream_sync_docs_policy.py tests/test_registry_category_naming.py tests/test_check_shadow_modifications.py tests/test_smoke_test_sync.py tests/test_gen_smd_scaffold.py -q
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py
uv run python3 tests/check_shadow_modifications.py
uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py
git diff --check -- AGENTS.md kamma/threads/upstream_sync_improvment/handoff.md kamma/upstream_sync/README.md kamma/upstream_sync/guide.md kamma/upstream_sync/infrastructure.md kamma/upstream_sync/scripts/execute_sync.py kamma/upstream_sync/scripts/gen_smd_scaffold.py kamma/upstream_sync/scripts/init_sync_thread.py kamma/upstream_sync/scripts/registry_helper.py kamma/upstream_sync/scripts/sync_schema.py kamma/upstream_sync/scripts/validate_registry.py kamma/upstream_sync/scripts/verify_smd_coverage.py kamma/upstream_sync/smd/db.md kamma/upstream_sync/smd/exporter.md kamma/upstream_sync/smd/gui.md kamma/upstream_sync/smd/root.md kamma/upstream_sync/smd/scripts.md kamma/upstream_sync/smd/tools.md tests/check_shadow_modifications.py tests/test_check_shadow_modifications.py tests/test_gen_smd_scaffold.py tests/test_prep_analyzer.py tests/test_sync_schema.py tests/test_sync_state.py tests/test_upstream_sync_docs_policy.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py
```

Result: red phase confirmed first with 10 expected failures, then all checks
passed. Focused hardening tests reported 123 passed; changed-file execution
suite reported 140 passed; broader upstream-sync suite reported 156 passed with
one third-party aksharamukha deprecation warning. Registry, SMD coverage, shadow
modification, docs parity, pyright, pyrefly, ruff, and diff whitespace checks
passed.

Most recent validation for redirect/printer/NUL parsing cleanup:

```fish
uv run pytest tests/test_upstream_sync_docs_policy.py tests/test_prep_analyzer.py -q
uv run ruff check --fix kamma/upstream_sync/scripts/check_docs_parity.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/init_sync_thread.py tests/check_shadow_modifications.py tests/test_upstream_sync_docs_policy.py tests/test_prep_analyzer.py
uv run ruff format kamma/upstream_sync/scripts/check_docs_parity.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/init_sync_thread.py tests/check_shadow_modifications.py tests/test_upstream_sync_docs_policy.py tests/test_prep_analyzer.py
uv run pyright kamma/upstream_sync/scripts/check_docs_parity.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/init_sync_thread.py tests/check_shadow_modifications.py tests/test_upstream_sync_docs_policy.py tests/test_prep_analyzer.py
uv run --with pyrefly pyrefly check --min-severity warn kamma/upstream_sync/scripts/check_docs_parity.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/init_sync_thread.py tests/check_shadow_modifications.py tests/test_upstream_sync_docs_policy.py tests/test_prep_analyzer.py
uv run pytest tests/test_upstream_sync_docs_policy.py tests/test_prep_analyzer.py tests/test_check_docs_parity.py tests/test_check_shadow_modifications.py -q
uv run pytest tests/test_sync_schema.py tests/test_sync_state.py tests/test_prep_analyzer.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py tests/test_validate_registry.py tests/test_verify_smd_coverage.py tests/test_check_docs_parity.py tests/test_upstream_sync_docs_policy.py tests/test_registry_category_naming.py tests/test_check_shadow_modifications.py tests/test_gen_smd_scaffold.py tests/test_smoke_test_sync.py -q
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py
uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py
uv run python3 tests/check_shadow_modifications.py
git diff --check -- AGENTS.md kamma/upstream_sync/scripts/check_docs_parity.py kamma/upstream_sync/scripts/prep_analyzer.py kamma/upstream_sync/scripts/init_sync_thread.py tests/check_shadow_modifications.py tests/test_upstream_sync_docs_policy.py tests/test_prep_analyzer.py
```

Result: red phase confirmed first with 3 expected failures, then all checks
passed. Affected tests reported 44 passed; broader upstream-sync suite reported
159 passed with one third-party aksharamukha deprecation warning. Registry, SMD
coverage, docs parity, live shadow modification check, pyright, pyrefly, ruff,
and diff whitespace checks passed.

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
  paths, `..` traversal, backslashes, surrounding whitespace, leading `-`, or
  git pathspec metacharacters in `run_exclusions.txt` or registry exclusions.
- `check_docs_parity.py <thread_dir>` should fail cleanly if the thread
  manifest is missing or malformed; do not let the traceback return.
- Do not add reviewed no-op ledger entries without inspecting the upstream diff
  and getting an explicit acceptance decision. If the user says no action is
  needed but gives no specific reason, use this exact reason:
  `User reviewed and confirmed this upstream change does not need to be ported to the shadow.`
- Do not use `unique_paths` for shadow no-op decisions. `unique_paths` is only
  cleanup inventory and is outside the monthly shadow sync process.
- Do not add or modify reviewed shadow no-op entries without reviewing the
  upstream diff and recording the exact reason. The current two prior-sync
  warnings were reviewed and recorded with explicit user approval.
- Patch against current file text. A past patch failed because docs wording had
  already diverged.
- Avoid complex multiline `rg` regexes for verification; use simple literal
  searches when possible.
- Do not treat `archive_improvements.md` as active protocol. It is historical
  only; canonical sync instructions are in `guide.md`, `templates/`, and `smd/`.
- Do not reintroduce `kamma/upstream_sync/suggestions.md`; use temporary
  `new_improvements.md` during active syncs and then promote accepted lessons to
  `archive_improvements.md`.
- Keep active guide search-command wording aligned with project rules: use
  `rg`, not `grep` or `find`.
- Preserve unrelated dirty/untracked `resources/*` entries unless the user
  explicitly asks to handle them.
- Do not reintroduce singular SMD category aliases such as `russian_copy` or
  `modified_upstream`; SMD `Category` must use the exact `registry.json` key.
- Do not broaden autonomous commit exceptions beyond human-run Bash scripts in
  `scripts/cl_dps/`. Agents and Python sync scripts must not commit.

## Current State

- Previous upstream-sync improvement sessions were implemented and validated.
- A separate review found no major redesign needed; the current
  registry + SMD + manifest + FAST/ADVANCED hard-stop architecture remains the
  recommended design.
- The separate review's recommended hardening was implemented: manifest
  `blocker_paths`, direct `as_upstream` pinning, full-SHA finalization, and
  Stage 5 finalization wording.
- The later standalone review hardening was implemented: full-SHA schema
  enforcement, stale SMD entry rejection, stricter sync exclusion validation,
  unknown SMD rule rejection, clean docs manifest errors, and reviewed no-op
  handling for the two prior-sync shadow warnings.
- The typed-hardening thread was finalized and archived at
  `kamma/archive/20260531_upstream_sync_typed_hardening`.
- This legacy thread directory currently exists as a compact handoff location.
  Do not assume `spec.md` or `plan.md` exist here; inspect the directory first.
- `reviewed_shadow_noops.json` contains two reviewed entries from sync commit
  `cc60ac42a91339f3e5c7c515aaa7c17610410b06`: RU Kindle titlepage date/time
  is locally generated, and DPS backup TSVs intentionally do not use upstream
  chunk splitting because the localized backups are small.
- The live shadow modification check is clean after those reviewed no-op
  entries.
- The smoke sync test now uses temporary config isolation. Do not reintroduce
  writes to `config.ini`.
- Standalone sync review found no architectural redesign needed. The approved
  entrypoint cleanup was implemented: `scripts/cl_dps/dpd-kamma-sync` remains
  the only sync-related Bash entrypoint; `init_sync_thread.py` now lives under
  `kamma/upstream_sync/scripts/`; post-sync assertions were folded into
  `execute_sync.py`; obsolete Bash sync paths were deleted.
- The latest standalone review hardening is implemented and validated: category
  naming is exact, commit exceptions are bounded, path safety is checked earlier,
  no-op ledger entries are stricter, and thread initialization gives an exact
  Stage 1 prompt.
- The latest simplification cleanup is implemented and validated: no active
  sync docs/tooling mention symlinks for no-translate docs, helper script output
  uses `tools.printer`, and prep diff parsing is NUL-delimited.
- No agent-side git commit was made.
- User manual review may still be needed for any uncommitted working-tree
  changes.
- Current unrelated dirty/untracked state remains under `resources/*`; preserve
  it unless the user explicitly asks to handle it.

## Errors, Issues, and Repeated Mistakes

- Red phase was confirmed: the new docs-policy test failed before guide/template
  wording was added.
- Real `execute_sync.py` was not run because it mutates git state; behavior was
  validated through focused unit tests and static checks.
- The corrected latest-sync baseline exposed two existing shadow warnings from
  the previous upstream sync. They were not fixed in this scope because the user
  asked for the no-op recording mechanism and handoff update, not porting those
  changes.
- The two prior-sync shadow warnings were reviewed with upstream diffs and
  recorded as exact no-op entries after user confirmation. The live shadow
  check now passes.
- Red phase was confirmed for this hardening: new tests initially failed on
  missing `check_unregistered_smd_entries` and `validate_repo_relative_paths`.
- Red phase was confirmed for the latest hardening: new tests initially failed
  on padded `run_exclusions.txt` path acceptance, missing leading-`-` and
  pathspec rejection, missing `--` path separation for restore, and missing
  unknown SMD rule rejection.
- Stricter SMD validation exposed 12 obsolete SMD entries for non-sync targets;
  those entries were removed, not reclassified into the registry.
- `tests/test_sync_state.py` also needed full-SHA fixtures after schema
  enforcement; otherwise the broader focused suite would fail.
- Existing untracked/dirty `resources/*` entries remain unrelated and were not
  touched.
- Keep future handoff updates short. This file is summary context, not a
  transcript.
- Red phase was confirmed for the standalone docs-hygiene cleanup: the new
  docs-policy assertions first failed on active `grep`/`find` wording, missing
  historical-only archive wording, missing legacy `stages/` label, and the
  still-present empty `suggestions.md` file.
- Red phase was confirmed for the entrypoint cleanup: the updated tests first
  failed because `run_sync_assertions()` did not exist and obsolete Bash sync
  paths were still present.
- `git mv` failed with `.git/index.lock` permission denial in the sandbox; the
  file move was done in the working tree without staging or committing.
- Red phase was confirmed for the latest standalone hardening: tests first
  failed on singular SMD categories, missing commit-exception wording, missing
  registry path-safety errors, permissive reviewed no-op schema, and the old
  `/kamma:2-do` init prompt.
- Red phase was confirmed for the latest simplification cleanup: tests first
  failed on active symlink policy/tooling references, `print()` usage in sync
  helper scripts, and whitespace-corrupting `prep_analyzer.py` diff parsing.
- A validation command mistakenly passed `AGENTS.md` to `ruff`, causing expected
  Markdown-as-Python syntax errors. The corrected Python-only ruff command then
  passed.

## Recent Recommended Commit Messages

```text
#sync tooling: harden prep parsing and sync docs
#sync tooling: harden upstream sync rules
#sync tooling: consolidate upstream sync entrypoints
#sync docs: simplify upstream sync guidance
#sync tooling: harden exclusions and document reviewed noops
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
