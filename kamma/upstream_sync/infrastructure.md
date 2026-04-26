# Upstream Sync Infrastructure

This document describes the canonical location, purpose, and usage of the upstream sync tooling for the DPD fork (SBS/RU).

---

## Canonical Location

All upstream sync assets live in `kamma/upstream_sync/`.

| File | Purpose |
|---|---|
| `registry.json` | Machine-readable map of every file that diverges from upstream |
| `accepted_sync.json` | Last accepted upstream SHA/date/ref used to anchor Stage 1 |
| `smd/` | Shadow Module Descriptions (Directory) — per-file merge guidance |
| `guide.md` | Process reference: category definitions, 3-stage workflow, naming policy |
| `archive_improvements.md` | Accumulated lessons from all past sync runs |
| `new_improvements.md` | A strictly temporary intake file generated during an active sync run. After its contents are reviewed and promoted to `archive_improvements.md`, the file MUST be deleted. It is ignored by git. |
| `templates/` | `plan.md` / `spec.md` starters for new sync kamma threads |
| `stages/` | Stage-specific contracts and checklists (Prep, Analysis, Execution) |
| `scripts/registry_helper.py` | Shared Python helper to load the registry and extract paths |
| `scripts/validate_registry.py` | Schema and data-quality validator for `registry.json` |
| `scripts/verify_smd_coverage.py` | Coverage checker — ensures every registry entry has an SMD entry in `smd/` |
| `scripts/prep_analyzer.py` | Generates factual Stage 1 report and manifest from the accepted sync range |
| `scripts/execute_sync.py` | Robustly executes selective sync from upstream (Stage 1 automation) |
| `scripts/finalize_accepted_sync.py` | Advances `accepted_sync.json` from a verified prep manifest |
| `scripts/sync_runtime.py` | Emits runtime sync metadata for shell automation |
| `README.md` | Folder-level quick-start |

---

## Registry Purpose

`registry.json` is the single source of truth for sync decisions. It has these top-level sections:

| Key | Meaning |
|---|---|
| `modified_upstream_files` | Files that exist upstream but have local modifications — review carefully on each sync |
| `russian_copies` | Shadow copies mirroring upstream with Russian additions (Strict parity) |
| `sbs_copies` | Shadow copies mirroring upstream with SBS additions (Strict parity) |
| `dps_copies` | Shadow copies mirroring upstream with DPS additions (Strict parity) |
| `tamil_copies` | Shadow copies mirroring upstream with Tamil additions (Strict parity) |
| `inspired_by_upstream` | Local files derived from upstream but structurally diverged (Selective backporting) |
| `unique_paths` | Files that exist only in this fork — never sync these from upstream |
| `no_sync_files` | Infrastructure files to skip entirely during sync |
| `skip_sync_patterns` | Glob patterns ignored during sync scanning |

Every `modified_upstream_files` entry is an object:
```json
{ "path": "db/models.py", "discuss": true, "discuss_reason": "..." }
```
Entries with `discuss: true` require human review before any port.

Every `inspired_by_upstream` entry is an object:
```json
{ "local/path": { "upstream": "upstream/path", "divergence_reason": "..." } }
```

---

## Shadow Module Descriptions (SMD)

The `smd/` directory provides per-file context for every registry entry.

Each entry contains:
- **Sync Rule**: `PORT` / `MIRROR_EXACTLY` / `PRESERVE` / `DISCUSS` / `inspired_only`
- **Local Changes**: numbered list of concrete divergences from upstream
- **Watch For**: specific merge pitfalls

Run `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` to check coverage.

---

## Validator Scripts

### `validate_registry.py`

Checks schema integrity of `registry.json`. Enforces `divergence_reason` for inspired files and rejects legacy keys like `ignored_files`.

### `verify_smd_coverage.py`

Aggregates entries from `smd/*.md` and ensures every registry entry is covered. Supports `inspired_only` sync rule.

### `prep_analyzer.py`

Generates `prep_report.md` and `prep_manifest.json` by diffing the explicit upstream range from `accepted_sync.json` to the current target upstream ref.

---

## Consumer Scripts

| Script | Role |
|---|---|
| `scripts/execute_sync.py` | Robustly executes selective sync from upstream |
| `tests/test_shadow_parity.py` | Verifies structural parity of strict shadows |
| `tests/check_shadow_modifications.py` | Checks shadows updated after upstream change |
| `tests/test_shadow_cleanup.py` | Finds orphaned files |
| `tests/test_namespace_isolation.py` | Enforces symbol naming policy |
| `tests/test_template_syntax.py` | Detects legacy Mako syntax |

---

## Legacy Status

`smd.md` has been replaced by the `smd/` directory. `ignored_files` has been renamed to `skip_sync_patterns`. `folders_to_check` has been removed.
