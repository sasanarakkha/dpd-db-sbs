# Upstream Sync Infrastructure

Canonical sync process and tooling for the DPD SBS-RU fork.

## Quick Start: The 3-Stage Workflow

Sync operations are executed via Kamma threads using the following stages:

1.  **Stage 1: Prep** — Factual diffing and environmental validation.
    -   `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py`
2.  **Stage 2: Analysis** — Strategic planning and `dynamic_plan.md` creation.
    -   High-model analysis of upstream changes.
3.  **Stage 3: Execution & Verification** — Implementation, testing, and cleanup.
    -   `uv run pytest` (Full suite).

For the full protocol, see **[guide.md](./guide.md)**.

## Core Tooling

| Command | Purpose |
|---|---|
| `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` | Validate `registry.json` schema and paths. |
| `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` | Ensure every registry entry has SMD merge guidance. |
| `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py` | Generate factual diff report for Stage 1. |
| `uv run pytest tests/test_shadow_parity.py` | Verify strict shadow parity with upstream. |
| `uv run pytest tests/test_namespace_isolation.py` | Enforce symbol naming policy on localized files. |
| `uv run pytest tests/test_template_syntax.py` | Detect legacy Mako syntax in Jinja2 templates. |

## Documentation & Metadata

- **[guide.md](./guide.md)**: Canonical process reference and naming policy.
- **[smd/index.md](./smd/index.md)**: Per-file merge guidance (Sync Metadata).
- **[registry.json](./registry.json)**: Source of truth for file mappings and categories.
- **[archive_improvements.md](./archive_improvements.md)**: Accumulated lessons from past runs. (Note: `new_improvements.md` is a strictly temporary file used during syncs and must not be committed).

## Registry Categories

- `modified_upstream_files`: Direct divergences (Manual porting).
- `russian_copies` / `sbs_copies`: Strict shadows (Parity enforced).
- `inspired_by_upstream`: Structural divergences (Selective backporting).
- `unique_paths`: Fork-only files (No sync).
- `skip_sync_patterns`: Ignored paths.
