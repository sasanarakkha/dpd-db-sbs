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
- `execute_sync.py` must use a thread directory and reset `as_upstream` to the
  verified manifest target SHA, not an unchecked moving ref.
- `finalize_accepted_sync.py` must verify the manifest against current accepted
  sync state before advancing `accepted_sync.json`.
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

## Main Files

- Docs/templates/stages under `kamma/upstream_sync/`.
- Registry/SMD: `kamma/upstream_sync/registry.json`,
  `kamma/upstream_sync/smd/*.md`.
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
- Do not implement replacement of `checkout as_upstream` plus `reset --hard`
  casually. Treat it as a separate behavioral redesign.
- `check_docs_parity.py` must handle report dirs outside the repo.
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
- The typed-hardening thread was finalized and archived at
  `kamma/archive/20260531_upstream_sync_typed_hardening`.
- This legacy thread directory currently exists as a compact handoff location.
  Do not assume `spec.md` or `plan.md` exist here; inspect the directory first.
- No agent-side git commit was made.
- User manual review may still be needed for any uncommitted working-tree
  changes.

## Recent Recommended Commit Messages

```text
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
4. the specific upstream-sync script/docs/tests relevant to the requested task

Do not broaden scope. Preserve unrelated resources/* dirty state. Rerun targeted
tests and validation commands for any touched files before reporting completion.
```
