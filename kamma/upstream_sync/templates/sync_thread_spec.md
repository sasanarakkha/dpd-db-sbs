# Spec: Upstream Sync <DATE>

## Goal

Port all upstream changes from `digitalpalidictionary/dpd-db` to this fork, preserving all
Russian and SBS localized additions intact.

## Upstream Diff Range

- **From**: `<FILL: last sync commit sha, tag, or date>`
- **To**: `upstream/main` at `<DATE>`

## Success Criteria

- Worktree was clean and `as_upstream` branch existed before sync began.
- Every changed upstream file reviewed against `registry.json` and classified.
- All `modified_upstream_files` that changed: sync rule applied (PORT / DISCUSS / PRESERVE).
- All shadow files whose upstream source changed: PORT strategy applied, SMD local changes verified.
- All automated tests pass (shadow parity, check modifications, ruff).
- User manually verified GoldenDict/webapp output and confirmed correct.
- `new_improvements.md` written with this run's learnings.
- 3 commits staged and presented (automated pull / manual merges / cleanup).

## Iron Rule (non-negotiable)

When a shadow file breaks after sync, the ONLY fix is:
1. Open the upstream source.
2. See exactly how upstream implements it.
3. Copy that exact solution.
4. Re-apply ONLY the local changes from `smd.md`.

FORBIDDEN: workarounds, alternative imports, try/except papering, restructuring
differently from upstream. The sources are correct. Broken means sync is incomplete.

## 3-Commit Gates

| Commit | When | Message |
|---|---|---|
| Commit 1 | After automated sync | `sync: automated upstream pull <DATE>` |
| Commit 2 | After manual merges + user verification | `sync: manual merge resolutions <DATE>` |
| Commit 3 | After cleanup + final validation | `sync: cleanup and finalization <DATE>` |

Each gate requires explicit **"Proceed with Commit N"** from the user.

## Model Switch Points

| Phase | Model | Reason |
|---|---|---|
| Phases 0, 1, 3, 5–7 | Auto | Routine execution |
| Phase 2 (Dynamic Analysis) | PRO | Deep diff analysis, cross-reference all shadows |
| Phase 4 (Logic Audit) | PRO | Iron Rule compliance verification |

## Key References

| File | Purpose |
|---|---|
| `kamma/upstream_sync/registry.json` | What to sync, what to skip, what to discuss |
| `kamma/upstream_sync/smd.md` | Per-file local changes and sync pitfalls |
| `kamma/upstream_sync/guide.md` | Merge strategy definitions, manual checklist |
| `kamma/upstream_sync/archive_improvements.md` | Accumulated lessons from past runs |
| `dynamic_plan.md` (thread-local) | Per-run analysis — created in Phase 2, deleted in Phase 7 |
