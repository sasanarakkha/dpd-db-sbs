# Upstream Sync Infrastructure

This document describes the canonical location, purpose, and usage of the upstream sync tooling for the DPD fork (SBS/RU).

---

## Canonical Location

All upstream sync assets live in `kamma/upstream_sync/`.

| File | Purpose |
|---|---|
| `registry.json` | Machine-readable map of every file that diverges from upstream |
| `smd.md` | Shadow Module Descriptions — per-file sync rules and local change notes |
| `guide.md` | Process reference: category definitions, merge strategies, error patterns |
| `archive_improvements.md` | Accumulated lessons from all past sync runs |
| `new_improvements.md` | Written at end of each sync run; overwritten each cycle |
| `templates/` | `plan.md` / `spec.md` starters for new sync kamma threads |
| `registry_helper.py` | Shared Python helper to load the registry and extract paths |
| `validate_registry.py` | Schema and data-quality validator for `registry.json` |
| `verify_smd_coverage.py` | Coverage checker — ensures every registry entry has an SMD section |
| `gen_smd_scaffold.py` | One-shot scaffold generator for new SMD stubs |
| `README.md` | Folder-level explainer |

---

## Registry Purpose

`registry.json` is the single source of truth for sync decisions. It has these top-level sections:

| Key | Meaning |
|---|---|
| `modified_upstream_files` | Files that exist upstream but have local modifications — review carefully on each sync |
| `russian_copies` | Shadow copies of upstream files carrying Russian translations (`shadow → upstream`) |
| `sbs_copies` | Shadow copies carrying SBS study-tool data (`shadow → upstream`) |
| `unique_paths` | Files that exist only in this fork — never sync these from upstream |
| `no_sync_files` | Files/patterns to skip entirely during sync |
| `folders_to_check` | Directories scanned by `test_shadow_cleanup.py` |

Every `modified_upstream_files` entry is an object:
```json
{ "path": "db/models.py", "discuss": true, "discuss_reason": "..." }
```
Entries with `discuss: true` require human review before any port — do not apply upstream changes blindly.

---

## Shadow Module Descriptions (SMD)

`smd/` provides per-file context for every registry entry. Before touching any file during a sync, read its SMD entry. If a file has no entry, stop and create one.

Each entry contains:
- **Sync Rule**: `PORT` / `MIRROR_EXACTLY` / `PRESERVE` / `DISCUSS`
- **Local Changes**: numbered list of concrete divergences from upstream
- **Watch For**: specific merge pitfalls

Run `uv run python3 kamma/upstream_sync/verify_smd_coverage.py` to check coverage and rubric compliance.

---

## Validator Scripts

### `validate_registry.py`

Checks schema integrity of `registry.json`:
- All `modified_upstream_files` entries are objects with `path`, `discuss` (bool), `discuss_reason` (non-empty when `discuss=true`)
- No duplicates in `unique_paths`, `russian_copies`, or `sbs_copies`
- Every shadow path exists in the repo
- Cross-section overlaps warned (1 expected: `data_classes_dps.py`)

```bash
uv run python3 kamma/upstream_sync/validate_registry.py
```

### `verify_smd_coverage.py`

Checks that every registry entry has an SMD section meeting the quality rubric (≥2 local changes, ≥1 watch-for, unless `MIRROR_EXACTLY`).

```bash
uv run python3 kamma/upstream_sync/verify_smd_coverage.py
```

---

## Consumer Scripts

The following scripts read `registry.json` and must stay in sync with its location:

| Script | Role |
|---|---|
| `scripts/bash/full_sync.sh` | Full upstream sync orchestration |
| `scripts/cl_dps/dpd-sync-folders` | Interactive folder sync helper |
| `tests/test_shadow_parity.py` | Pytest: verifies structural parity of shadow copies |
| `tests/check_shadow_modifications.py` | Standalone: checks shadows updated after upstream change |
| `tests/test_shadow_cleanup.py` | Standalone: finds orphaned files (`--dry-run` by default, `--apply` to archive) |

---

## Legacy Status

`conductor/templates/upstream_sync_rehearsal/` has been **archived** to `conductor/archive/upstream_sync_rehearsal/`. It contains the original pre-migration registry (`dps_sync_registry.json`) preserved for historical reference only. No active code references that path.
