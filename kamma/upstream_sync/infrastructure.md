# Upstream Sync Infrastructure

This document describes the canonical location, purpose, and usage of the upstream sync tooling for the DPD fork (SBS/RU).

---

## Canonical Location

All upstream sync assets live in `kamma/upstream_sync/`.

| File | Purpose |
|---|---|
| `registry.json` | Machine-readable map of every file that diverges from upstream |
| `accepted_sync.json` | Last accepted upstream SHA/date/ref used to anchor Stage 1 |
| `reviewed_shadow_noops.json` | Exact reviewed no-op ledger for changed upstream sources that intentionally need no shadow edit |
| `smd/` | Shadow Module Descriptions (Directory) — per-file merge guidance |
| `guide.md` | Process reference: category definitions, 5-stage workflow, model responsibilities, naming policy |
| `archive_improvements.md` | Accumulated lessons from all past sync runs |
| `new_improvements.md` | A strictly temporary intake file generated during an active sync run. After its contents are reviewed and promoted to `archive_improvements.md`, the file MUST be deleted. It is ignored by git. |
| `templates/` | `plan.md` / `spec.md` starters for new sync kamma threads |
| `stages/` | Legacy Stage 1-3 reference checklists; `guide.md` and `templates/` are canonical for current 5-stage syncs |
| `scripts/registry_helper.py` | Shared Python helper to load the registry and extract paths |
| `scripts/validate_registry.py` | Schema and data-quality validator for `registry.json` |
| `scripts/verify_smd_coverage.py` | Coverage checker — ensures every sync-relevant registry entry has an SMD entry in `smd/` |
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
| `dps_copies` | Shadow copies mirroring upstream with shared DPS fork additions (Strict parity). `dps_copies` is the single category for mixed/shared fork shadows. |
| `tamil_copies` | Shadow copies mirroring upstream with Tamil additions (Strict parity) |
| `inspired_by_upstream` | Local files derived from upstream but structurally diverged (Selective backporting) |
| `unique_paths` | Fork-only cleanup inventory, not sync targets; no SMD entry required |
| `no_sync_files` | Infrastructure files to skip entirely during sync |
| `skip_sync_patterns` | Upstream-owned or irrelevant paths excluded from Stage 1 analysis only; still synced unless also listed in `no_sync_files` |

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

## Model Responsibility

The sync process is intentionally split between two model roles:

| Model | Owns | Must stop when |
|---|---|---|
| FAST | Commands, scripted checks, factual reports, literal edits from approved plans, tests, translation execution | Analysis, risk classification, strategy, conflict resolution, or plan repair is needed |
| ADVANCED | Interpreting FAST outputs, resolving strategy, planning, acceptance decisions | Mechanical editing, command execution, formatting, testing, or bulk translation is needed |

Every model boundary is a hard stop. The current session must update `<thread_dir>/handoff.md`,
write the exact restart prompt, tell the user which model to switch to, and stop.

---

## Shadow Module Descriptions (SMD)

The `smd/` directory provides per-file context for every sync-relevant registry entry
(`modified_upstream_files`, strict shadows, and `inspired_by_upstream`).

Each entry contains:
- **Sync Rule**: `PORT` / `MIRROR_EXACTLY` / `PRESERVE` / `DISCUSS` / `inspired_only`
- **Category**: exact match to the path's `registry.json` category
- **Local Changes**: numbered list of concrete divergences from upstream
- **Watch For**: specific merge pitfalls

Run `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` to check coverage.

---

## Validator Scripts

### `validate_registry.py`

Checks schema integrity of `registry.json`. Enforces `divergence_reason` for inspired files and rejects legacy keys like `ignored_files`.

### `verify_smd_coverage.py`

Aggregates entries from `smd/*.md` and ensures every sync-relevant registry entry is covered. Supports `inspired_only` sync rule.

### `prep_analyzer.py`

Generates `prep_report.md` and `prep_manifest.json` by diffing the explicit upstream range from `accepted_sync.json` to the current target upstream ref.

---

## Consumer Scripts

| Script | Role |
|---|---|
| `scripts/execute_sync.py` | Robustly executes selective sync from upstream |
| `tests/test_shadow_parity.py` | Verifies structural parity of strict shadows |
| `tests/check_shadow_modifications.py` | Checks shadows updated after upstream change, unless an exact reviewed no-op entry exists in `reviewed_shadow_noops.json` |
| `tests/test_shadow_cleanup.py` | Finds orphaned files |
| `tests/test_namespace_isolation.py` | Enforces symbol naming policy |
| `tests/test_template_syntax.py` | Detects legacy Mako syntax |

---

## Legacy Status

`smd.md` has been replaced by the `smd/` directory. `ignored_files` has been renamed to `skip_sync_patterns`. `folders_to_check` has been removed.
