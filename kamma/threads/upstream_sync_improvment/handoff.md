# Upstream Sync Improvement Handoff

Keep this file compact. It is future-session context, not a transcript.

## Purpose

Improve `kamma/upstream_sync` so upstream syncs are safer, restartable,
model-boundary aware, and validated for RU/SBS/DPS/Tamil localized files.

## Core Architecture

- Upstream sync uses a 5-stage workflow with explicit FAST/ADVANCED boundaries.
- FAST runs mechanical commands and writes evidence.
- ADVANCED analyzes evidence, plans, accepts/rejects changes, and writes
  restartable handoffs.
- If either model crosses its responsibility boundary, stop and write a handoff.
- `prep_manifest.json` is the central sync contract.
- `prep_manifest.json.discuss_paths` and `blocker_paths` are hard stops before
  `execute_sync.py`.
- `execute_sync.py` must run from a thread directory and pin `as_upstream`
  directly to the verified manifest target SHA using `git update-ref`.
- Do not restore the older `checkout as_upstream` plus `reset --hard` flow.
- `finalize_accepted_sync.py` must verify current accepted sync state before
  advancing `accepted_sync.json`, and must write full 40-character lowercase
  SHAs.
- Autonomous agent commits remain prohibited. The only known sync exception is
  the human-run Bash wrapper under `scripts/cl_dps/`, which may commit exactly
  `backup dps data`.

## Implemented Hardening

- Workflow docs now describe the 5-stage FAST/ADVANCED model, Stage 1 API health
  checks, Stage 4 docs parity, Stage 5 finalization wording, restartable
  handoffs, and current sync scope.
- Sync runtime gates reject unsafe branch/state, stale or invalid manifests,
  unresolved `discuss_paths`, unresolved `blocker_paths`, unsafe prep paths, and
  failed post-sync assertions.
- Metadata parsing and validation are centralized in `sync_schema.py`.
- Registry, SMD, prep manifest, mapped actions, no-op ledger, and accepted sync
  state are validated more strictly.
- Prep analysis handles deleted upstream sources, rename facts,
  `local_target_path`, and NUL-delimited `git diff --name-status -z` output.
- Docs parity uses the thread manifest range when available, supports strict
  final verification, keeps standalone report mode, and handles report dirs
  outside the repo.
- Registry/SMD tooling covers Tamil, exact category names, DPS/Tamil scaffold
  categories, single-category policy, and stale SMD entry rejection.
- `reviewed_shadow_noops.json` records explicit reviewed decisions not to port
  specific upstream shadow changes.
- `unique_paths` is cleanup inventory only. It is outside the monthly shadow
  sync process and should not get SMD coverage.
- `execute_sync.py` validates exclusion paths as repo-relative, pathspec-safe
  paths and leaves changes unstaged unless `--stage` is passed.
- `tests/smoke_test_sync.py` uses `temp/smoke_config.ini`; do not reintroduce
  writes to `config.ini`.
- Active sync docs/tooling no longer depend on `kamma/threads.md`,
  symlink-based no-translate policy, or obsolete Bash sync entrypoints.
- Helper script output was migrated to `tools.printer` where relevant.
- `check_docs_parity.py --strict` now fails if docs git-diff evidence cannot be
  collected; non-strict standalone report mode still warns and continues.
- Exclusion/path validation rejects leading `:` Git pathspec magic in addition
  to absolute paths, `..`, backslashes, whitespace, leading `-`, and glob
  metacharacters where globs are not explicitly allowed.
- `init_sync_thread.py` now reads `accepted_sync.json`, fills the sync spec
  source SHA/ref, and writes a fuller restartable `handoff.md` with the
  required errors/issues section.
- `prep_analyzer.py` has a single rename expansion path: NUL-delimited
  `git diff --name-status -z` parsing expands renames, with no second
  whitespace-splitting pass.
- `scripts/cl_dps/dpd-kamma-sync` now checks that the current branch is
  `sbs-ru` before running the backup script or committing `backup dps data`.

## Important Files

- Workflow docs and templates: `kamma/upstream_sync/guide.md`,
  `kamma/upstream_sync/templates/`, `kamma/upstream_sync/stages/`.
- Registry/SMD: `kamma/upstream_sync/registry.json`,
  `kamma/upstream_sync/smd/*.md`.
- Reviewed no-op ledger:
  `kamma/upstream_sync/reviewed_shadow_noops.json`.
- Main scripts: `init_sync_thread.py`, `prep_analyzer.py`, `execute_sync.py`,
  `finalize_accepted_sync.py`, `sync_runtime.py`, `sync_schema.py`,
  `validate_registry.py`, `verify_smd_coverage.py`, `check_docs_parity.py`,
  `gen_smd_scaffold.py`.
- Main tests: focused upstream-sync, registry, SMD, prep analyzer, docs parity,
  docs policy, and shadow modification tests under `tests/`.

## Validation Pattern

For any future related change, rerun targeted tests for touched behavior plus
the relevant validators:

```fish
uv run ruff check --fix <changed-python-files>
uv run ruff format <changed-python-files>
uv run pyright <changed-python-files>
uv run --with pyrefly pyrefly check --min-severity warn <changed-python-files>
uv run python3 kamma/upstream_sync/scripts/validate_registry.py
uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py
uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py --strict
uv run python3 tests/check_shadow_modifications.py
git diff --check -- <changed-files>
```

Do not reuse old validation results as current proof. Previous sessions had
passing focused suites, but every new change needs fresh targeted evidence.

## Current State

- Prior upstream-sync improvement sessions were implemented and validated.
- No major redesign is currently recommended; keep the registry + SMD +
  manifest + FAST/ADVANCED hard-stop architecture.
- The typed-hardening thread was finalized and archived at
  `kamma/archive/20260531_upstream_sync_typed_hardening`.
- This legacy thread directory is only a compact handoff location. It may not
  contain `spec.md` or `plan.md`; inspect the directory before assuming Kamma
  thread structure.
- `reviewed_shadow_noops.json` contains two reviewed entries from sync commit
  `cc60ac42a91339f3e5c7c515aaa7c17610410b06`: RU Kindle titlepage date/time is
  locally generated, and DPS backup TSVs intentionally skip upstream chunk
  splitting because localized backups are small.
- The live shadow modification check was clean after those no-op entries.
- No agent-side git commit was made for these improvement sessions.
- User manual review may still be needed for uncommitted working-tree changes.
- Unrelated dirty/untracked state has existed under `resources/*`; preserve it
  unless the user explicitly asks to handle it.
- Current uncommitted upstream-sync improvement work touches only:
  `check_docs_parity.py`, `sync_schema.py`, `init_sync_thread.py`,
  `prep_analyzer.py`, `scripts/cl_dps/dpd-kamma-sync`, and targeted tests.
- Latest validation passed: targeted upstream-sync tests (`64 passed`),
  related metadata/finalization tests (`97 passed`), ruff check/format,
  pyright, pyrefly, Bash syntax check, registry/SMD validators, docs parity,
  shadow-modification check, and `git diff --check`.

## Mistakes To Avoid

- Do not list one local path in more than one registry category.
- Do not let SMD `Category` drift from `registry.json`; use exact category keys.
- Use `dps_copies` for mixed/shared fork shadows.
- Keep Tamil in helper and test coverage.
- Do not reintroduce singular SMD aliases such as `russian_copy` or
  `modified_upstream`.
- `exporter/webapp/main.py` maps as `russian_copy`, not `dps_copy`.
- Some parity divergences are intentional and SMD-documented. Known examples:
  `db/families/family_idiom_ru.py` omits upstream `update_db_cache()`, and
  `db/tpd/tpd_to_lookup.py` omits root helpers from `db/epd/epd_to_lookup.py`.
- Do not add SMD entries for paths outside sync-relevant registry categories.
- Do not use `unique_paths` for shadow no-op decisions.
- Do not add or modify reviewed no-op entries without inspecting the upstream
  diff and recording the exact user-approved reason.
- If the user confirms a no-op but gives no specific reason, use this exact
  reason: `User reviewed and confirmed this upstream change does not need to be
  ported to the shadow.`
- Keep accepted sync and prep manifest SHAs full-length lowercase SHAs.
- Keep prep manifest, registry exclusion, and run-exclusion paths
  repo-relative and pathspec-safe.
- Do not allow absolute paths, `..`, backslashes, surrounding whitespace,
  leading `-`, leading `:` pathspec magic, or git pathspec metacharacters in
  exclusions.
- Do not reintroduce `kamma/threads.md`; sync thread discovery is directory
  based under `kamma/threads/`.
- Do not make `execute_sync.py` auto-stage by default.
- For final docs verification after Stage 4.B, use
  `check_docs_parity.py <thread_dir> --strict`.
- Do not treat `archive_improvements.md` as active protocol. Canonical sync
  instructions are in `guide.md`, templates, and SMD docs.
- Do not reintroduce `kamma/upstream_sync/suggestions.md`; use temporary
  `new_improvements.md` during active syncs and promote accepted lessons to
  `archive_improvements.md`.
- Prefer simple literal `rg` verification over fragile multiline regexes.
- Patch against current file text; docs wording has diverged during past work.
- Keep future handoff updates short.

## Errors, Issues, And Repeated Mistakes

- Real `execute_sync.py` was not run during hardening because it mutates git
  state; behavior was validated with focused unit tests and static checks.
- A past success-path `execute_sync` test accidentally ran the real assertion
  script. Mock assertion-script presence and execution deliberately.
- Stricter SMD validation exposed obsolete entries for non-sync targets; they
  were removed instead of reclassified into the registry.
- Full-SHA enforcement required updating test fixtures too.
- A validation command once passed `AGENTS.md` to `ruff`, causing expected
  Markdown-as-Python syntax errors. Keep ruff commands Python-only.
- `git mv` failed once with `.git/index.lock` permission denial in the sandbox;
  the file move was done in the working tree without staging or committing.
- The user previously ran `dpd-kamma-sync`, which committed `backup dps data`
  before `init_sync_thread.py` failed on missing `kamma/threads.md`. Do not undo
  that commit or generated sync state unless explicitly requested.
- Existing unrelated dirty/untracked `resources/*` entries were not touched.
- TDD red phase for strict docs parity failed at collection because
  `DocsDiffError` did not exist yet; this was the intended initial failure.
- One existing strict docs parity test needed its mock expectation updated to
  include `fail_on_error=True` after strict mode began calling the safer path.

## Recent Commit Message Candidates

```text
#sync tooling: harden prep parsing and sync docs
#sync tooling: harden sync safety and remove legacy threads index
#sync tooling: harden upstream sync rules
#sync tooling: consolidate upstream sync entrypoints
#sync docs: simplify upstream sync guidance
#sync tooling: harden exclusions and document reviewed noops
#sync tooling: harden sync metadata validators
#sync tooling: add reviewed shadow noop ledger
#sync docs: clarify unique cleanup inventory
#sync tooling: block unsafe prep paths and pin upstream ref
#sync docs: enforce single dps shadow category
#sync tooling: harden sync init and docs parity
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
