# Thread Handoff: `prepare_update_skill` — 2026-04-04

## Current state

This thread is the active owner of upstream-sync preparation work:

- migrate canonical sync assets to `kamma/upstream_sync/`
- update active consumers to the new registry location
- add registry validation and SMD coverage tooling
- build out `smd.md`

The child thread already has:

- `spec.md`
- `plan.md`
- `suggestions-gpt.md`

## Scope boundary

This thread does **not** own authoring or installing the `/update-upstream` skill file.
That belongs to `kamma/threads/20260404_implement_update_upstream`.

## Important notes

- The original combined thread was split and archived.
- If implementation planning references missing registry, SMD, or validator work, that
  is a prep-thread blocker, not an implementation-thread task.
