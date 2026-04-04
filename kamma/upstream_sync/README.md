# kamma/upstream_sync/

Canonical upstream sync tooling for the DPD SBS-RU fork.

## What belongs here

| File | Purpose |
|---|---|
| `registry.json` | Source of truth: all shadow mappings, unique paths, and discussion flags |
| `registry_helper.py` | Shared Python helpers for loading/querying the registry |
| `smd.md` | Shadow Module Descriptions — per-file merge guidance for every registry entry |
| `guide.md` | Process reference: registry categories, merge strategies, sync checklist |
| `archive_improvements.md` | Accumulated post-mortem lessons from all past sync runs |
| `new_improvements.md` | Lessons from the most recent sync run (overwritten each cycle) |
| `templates/` | Starter `plan.md` and `spec.md` for new sync threads |
| `validate_registry.py` | Schema + data quality validator for `registry.json` |
| `verify_smd_coverage.py` | Checks every registry entry has a complete SMD section |
| `gen_smd_scaffold.py` | Generates stub SMD entries from `registry.json` |

## What does NOT belong here

- Per-run dynamic plans (`dynamic_plan.md`) — keep those thread-local.
- Session logs or archive snapshots — those go in `kamma/archive/`.
- Upstream diffs or temporary work files — clean these up before finalizing.

## Relationship to old location

The files previously under `conductor/templates/upstream_sync_rehearsal/` have been
archived to `conductor/archive/upstream_sync_rehearsal/`. The canonical files for all
active sync operations are in this directory.

## Consumers

Scripts that read `registry.json` directly:

| Consumer | What it reads |
|---|---|
| `scripts/bash/full_sync.sh` | `modified_upstream_files[].path` + `no_sync_files` |
| `scripts/cl_dps/dpd-sync-folders` | `modified_upstream_files[].path` + `no_sync_files` |
| `tests/test_shadow_parity.py` | `russian_copies`, `sbs_copies` |
| `tests/check_shadow_modifications.py` | `russian_copies`, `sbs_copies` |
| `tests/test_shadow_cleanup.py` | `folders_to_check`, `no_sync_files`, `unique_paths` |
