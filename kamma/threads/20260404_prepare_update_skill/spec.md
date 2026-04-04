# Spec: Prepare Upstream Sync Infrastructure

## Goal

Migrate all upstream sync tooling from `conductor/templates/upstream_sync_rehearsal/` to
`kamma/upstream_sync/`, enrich the registry with discussion flags, build Shadow Module
Descriptions (SMD), and add validation scripts — so the `/update-upstream` skill has a
clean, machine-readable foundation to operate on.

## Root Problems Being Solved

1. **Registry in the wrong place** — sync tooling is buried under `conductor/templates/`,
   making it hard to find and maintain.
2. **Registry data quality** — `unique_paths` has 4 duplicates; `modified_upstream_files`
   is a flat string array with no metadata.
3. **No per-file local-change documentation** — AI has no concrete record of what to
   preserve when syncing each shadow file.
4. **No automated validation** — registry schema drift and SMD coverage gaps go undetected.

## Success Criteria

- `kamma/upstream_sync/registry.json` exists, is deduped, and has `discuss`/`discuss_reason`
  fields on every `modified_upstream_files` entry.
- All 5 consumer scripts and 3 policy docs reference the new canonical path.
- `kamma/upstream_sync/smd.md` has a concrete entry (local changes, sync rule, watch-for
  notes) for every file in the registry.
- `validate_registry.py` passes with zero errors against the new registry.
- `verify_smd_coverage.py` passes with zero gaps.
- All relevant tests pass (`test_shadow_parity.py`, `check_shadow_modifications.py`,
  `test_shadow_cleanup.py`).
- No active code references the old `upstream_sync_rehearsal/dps_sync_registry.json` path.

## Deliverables

| File | Description |
|---|---|
| `kamma/upstream_sync/registry.json` | Migrated, deduped, v2-schema registry |
| `kamma/upstream_sync/smd.md` | Per-file shadow module descriptions |
| `kamma/upstream_sync/guide.md` | Slimmed process reference (no AI instructions) |
| `kamma/upstream_sync/improvements.md` | Copied from conductor templates |
| `kamma/upstream_sync/validate_registry.py` | Registry schema + data quality validator |
| `kamma/upstream_sync/verify_smd_coverage.py` | SMD coverage checker |
| `conductor/templates/upstream_sync_rehearsal/LEGACY_NOTICE.md` | Freeze marker |

## Key Design Decisions

### Safety-First Approach
No migration work begins until the worktree is clean (or explicitly backed up) and all
consumers are documented. This prevents destructive sync commands from running against
an inconsistent state.

### Registry v2 Schema
`modified_upstream_files` becomes an array of objects:
```json
{ "path": "db/models.py", "discuss": true, "discuss_reason": "..." }
```
Shell consumers extract `["path"]` from each object for backward compatibility.

### SMD Auto-Scaffold First
Generate a scaffold from the registry (all entries with stubs), then manually enrich
high-risk entries. Only after the scaffold exists is full completion required.

### Static vs Runtime Separation
`kamma/upstream_sync/` contains only canonical reusable assets (registry, smd, guide,
validators). Per-run files like `dynamic_plan.md` stay thread-local.
