# Upstream Sync Infrastructure

Canonical sync process and tooling for the DPD SBS-RU fork.

All local sync-process documentation lives in `kamma/upstream_sync/`. Do not add sync-process
docs under upstream-owned `docs/`.

## Quick Start: The 5-Stage Model-Split Workflow

Before Stage 1, run `scripts/cl_dps/dpd-kamma-sync`. This is the only sync-related
Bash entrypoint: it backs up DPS localization tables, commits only the backup TSV
changes as `backup dps data`, and initializes the Kamma sync thread through
`kamma/upstream_sync/scripts/init_sync_thread.py`. All actual sync execution stays
in Python scripts under `kamma/upstream_sync/scripts/`.
Git commit/push policy is inherited from the global rules.

Sync operations are executed via Kamma threads. Each stage ends with a hard stop, a fresh-session
handoff, and an explicit model switch when needed. Stage 4 has two model-bound substages.

1.  **Stage 1: FAST Prep** — factual diffing, scripted validation, and automated upstream pull.
    -   `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py <thread_dir>`
2.  **Stage 2: ADVANCED Analysis** — strategic planning and `dynamic_plan.md` creation.
    -   Interpret FAST outputs, resolve `discuss` flags, and write a literal execution plan.
3.  **Stage 3: FAST Execution & Verification** — implementation, testing, and cleanup.
    -   `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py -v` (Sync-related suites).
4.  **Stage 4: Docs Translation Parity**
    -   **Stage 4.A: ADVANCED Docs Analysis** — docs parity analysis and `docs_translation_plan.md`.
    -   Read FAST-produced `docs_parity_report.md` from the `prep_manifest.json` range; do not run commands in ADVANCED.
    -   **Stage 4.B: FAST Docs Translation** — execute the approved docs translation plan.
5.  **Stage 5: ADVANCED Verification & After-sync** — decide acceptance after user verification.

FAST performs mechanical work only. ADVANCED performs analysis and planning only. If either model
needs the other responsibility, it must update `handoff.md`, write an exact restart prompt, and stop.

For the full protocol, see **[guide.md](./guide.md)**.

## Core Tooling

| Command | Purpose |
|---|---|
| `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` | Validate `registry.json` schema and paths. |
| `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` | Ensure every sync-relevant registry entry has SMD merge guidance. |
| `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py <thread_dir>` | Generate Stage 1 report and manifest. |
| `uv run python3 kamma/upstream_sync/scripts/execute_sync.py <thread_dir>` | Robustly execute selective sync from upstream. |
| `uv run python3 kamma/upstream_sync/scripts/finalize_accepted_sync.py <thread_dir>` | Advance accepted sync metadata after Stage 5 acceptance. |
| `uv run pytest tests/test_shadow_parity.py` | Verify strict shadow parity with upstream. |
| `uv run python3 tests/check_shadow_modifications.py` | Verify changed upstream sources have matching shadow edits or reviewed no-op entries. |
| `uv run pytest tests/test_namespace_isolation.py` | Enforce symbol naming policy on localized files. |
| `uv run pytest tests/test_template_syntax.py` | Detect legacy Mako syntax in Jinja2 templates. |

## Documentation & Metadata

- **[guide.md](./guide.md)**: Canonical process reference and naming policy.
- **[accepted_sync.json](./accepted_sync.json)**: Last accepted upstream sync point.
- **[reviewed_shadow_noops.json](./reviewed_shadow_noops.json)**: Exact reviewed no-op ledger for changed upstream sources that intentionally need no shadow edit.
- **[smd/index.md](./smd/index.md)**: Per-file merge guidance (Sync Metadata).
- **[registry.json](./registry.json)**: Source of truth for file mappings and categories.
- **[archive_improvements.md](./archive_improvements.md)**: Accumulated lessons from past runs. (Note: `new_improvements.md` is a strictly temporary file used during syncs and must not be committed).

## File Inventory

| File | Purpose |
|---|---|
| `registry.json` | Machine-readable map of every file that diverges from upstream |
| `accepted_sync.json` | Last accepted upstream SHA/date/ref used to anchor Stage 1 |
| `reviewed_shadow_noops.json` | Exact reviewed no-op ledger for changed upstream sources that intentionally need no shadow edit |
| `smd/` | Shadow Module Descriptions (Directory) — per-file merge guidance |
| `guide.md` | Canonical process reference: Iron Rule, 5-stage workflow, model responsibilities, naming policy |
| `archive_improvements.md` | Accumulated lessons from all past sync runs |
| `new_improvements.md` | Strictly temporary intake file during an active sync; must be deleted after promotion to `archive_improvements.md`; ignored by git |
| `templates/` | `plan.md` / `spec.md` starters for new sync kamma threads |
| `scripts/init_sync_thread.py` | Creates the Kamma sync thread after `scripts/cl_dps/dpd-kamma-sync` backs up DPS data |
| `scripts/registry_helper.py` | Shared Python helper to load the registry and extract paths |
| `scripts/validate_registry.py` | Schema and data-quality validator for `registry.json` |
| `scripts/verify_smd_coverage.py` | Coverage checker — ensures every sync-relevant registry entry has an SMD entry in `smd/` |
| `scripts/prep_analyzer.py` | Generates factual Stage 1 report and manifest from the accepted sync range |
| `scripts/execute_sync.py` | Robustly executes selective sync from upstream (Stage 1 automation) |
| `scripts/finalize_accepted_sync.py` | Advances `accepted_sync.json` from a verified prep manifest |
| `scripts/sync_runtime.py` | Runtime manifest verification for shell automation |
| `README.md` | Folder-level quick-start and file inventory |

## Registry Categories

- `modified_upstream_files`: Direct divergences (Manual porting).
- `russian_copies` / `sbs_copies`: Strict shadows (Parity enforced).
- `dps_copies`: Strict DPS fork shadows (Parity enforced). `dps_copies` is the single category for mixed/shared fork shadows, including local upstream shadows that combine Russian, SBS, Tamil, or general DPS behavior.
- `tamil_copies`: Strict Tamil shadows (Parity enforced).
- `inspired_by_upstream`: Structural divergences (Selective backporting).
- `unique_paths`: Fork-only cleanup inventory, not sync targets; no SMD entry required.
- `skip_sync_patterns`: Upstream-owned or irrelevant paths excluded from Stage 1 analysis only; still synced unless also listed in `no_sync_files`.
