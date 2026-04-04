# Thread Handoff: `implement_update_upstream` — 2026-04-04

## Current state

This thread is the active owner of the `/update-upstream` skill itself:

- draft the in-repo skill file
- encode the runtime sync workflow
- review the draft
- install to `~/.claude/commands/` only after approval

The child thread already has:

- `spec.md`
- `plan.md`
- `suggestions-gpt.md`

## Scope boundary

This thread depends on preparation work from
`kamma/threads/20260404_prepare_update_skill`:

- canonical `kamma/upstream_sync/registry.json`
- complete `kamma/upstream_sync/smd.md`
- working validators

It should not absorb infrastructure-migration work from the prep thread.

## Important notes

- The original combined thread was split and archived.
- Temporary execution artifacts such as `dynamic_plan.md` should stay thread-local, not
  under `kamma/upstream_sync/`.
