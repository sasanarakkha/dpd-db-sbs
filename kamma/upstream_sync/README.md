# Upstream Sync Infrastructure

Canonical sync process and tooling for the DPD SBS-RU fork.

All local sync-process documentation lives in `kamma/upstream_sync/`. Do not add sync-process
docs under upstream-owned `docs/`.

## Quick Start: The 5-Stage Model-Split Workflow

Sync operations are executed via Kamma threads. Each stage ends with a hard stop, a fresh-session
handoff, and an explicit model switch when needed.

1.  **Stage 1: FAST Prep** — factual diffing, scripted validation, and automated upstream pull.
    -   `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py <thread_dir>`
2.  **Stage 2: ADVANCED Analysis** — strategic planning and `dynamic_plan.md` creation.
    -   Interpret FAST outputs, resolve `discuss` flags, and write a literal execution plan.
3.  **Stage 3: FAST Execution & Verification** — implementation, testing, and cleanup.
    -   `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py -v` (Sync-related suites).
4.  **Stage 4.A: ADVANCED Docs Analysis** — docs parity analysis and `docs_translation_plan.md`.
    -   `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py <thread_dir>`
5.  **Stage 4.B: FAST Docs Translation** — execute the approved docs translation plan.
6.  **Stage 5: ADVANCED Verification & After-sync** — decide acceptance after user verification.

FAST performs mechanical work only. ADVANCED performs analysis and planning only. If either model
needs the other responsibility, it must update `handoff.md`, write an exact restart prompt, and stop.

For the full protocol, see **[guide.md](./guide.md)**.

## Core Tooling

| Command | Purpose |
|---|---|
| `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` | Validate `registry.json` schema and paths. |
| `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` | Ensure every registry entry has SMD merge guidance. |
| `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py <thread_dir>` | Generate Stage 1 report and manifest. |
| `uv run python3 kamma/upstream_sync/scripts/execute_sync.py <thread_dir>` | Robustly execute selective sync from upstream. |
| `uv run python3 kamma/upstream_sync/scripts/finalize_accepted_sync.py <thread_dir>` | Advance accepted sync metadata after Stage 5 acceptance. |
| `uv run pytest tests/test_shadow_parity.py` | Verify strict shadow parity with upstream. |
| `uv run pytest tests/test_namespace_isolation.py` | Enforce symbol naming policy on localized files. |
| `uv run pytest tests/test_template_syntax.py` | Detect legacy Mako syntax in Jinja2 templates. |

## Documentation & Metadata

- **[guide.md](./guide.md)**: Canonical process reference and naming policy.
- **[accepted_sync.json](./accepted_sync.json)**: Last accepted upstream sync point.
- **[smd/index.md](./smd/index.md)**: Per-file merge guidance (Sync Metadata).
- **[registry.json](./registry.json)**: Source of truth for file mappings and categories.
- **[archive_improvements.md](./archive_improvements.md)**: Accumulated lessons from past runs. (Note: `new_improvements.md` is a strictly temporary file used during syncs and must not be committed).

## Registry Categories

- `modified_upstream_files`: Direct divergences (Manual porting).
- `russian_copies` / `sbs_copies`: Strict shadows (Parity enforced).
- `dps_copies`: Strict DPS shadows (Parity enforced).
- `tamil_copies`: Strict Tamil shadows (Parity enforced).
- `inspired_by_upstream`: Structural divergences (Selective backporting).
- `unique_paths`: Fork-only files (No sync).
- `skip_sync_patterns`: Ignored paths.
