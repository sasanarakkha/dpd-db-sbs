# Spec: Upstream Sync <DATE>

## Goal

Port all upstream changes from `digitalpalidictionary/dpd-db` to this fork, preserving all
Russian and SBS localized additions intact.

## Upstream Diff Range

- **From**: `<FILL: last sync commit sha, tag, or date>`
- **To**: `upstream/main` at `<DATE>`

## Success Criteria

- Worktree was clean and `as_upstream` branch existed before sync began.
- `kamma/upstream_sync/accepted_sync.json` was reviewed and used as the starting sync point.
- Stage 1 produced both `prep_report.md` and `prep_manifest.json`.
- Every changed upstream file reviewed against `registry.json` and classified.
- All `modified_upstream_files` that changed: sync rule applied (PORT / DISCUSS / PRESERVE).
- All shadow files whose upstream source changed: PORT strategy applied, SMD local changes verified.
- All inspired files whose upstream source changed: selective improvements backported.
- All automated tests pass (shadow parity, namespace isolation, syntax drift, prep analyzer).
- User manually verified GoldenDict/webapp output and confirmed correct.
- `new_improvements.md` reviewed, valuable items promoted, and then deleted.
- 3 commits staged and presented (automated pull / manual merges / cleanup).

## Iron Rule (non-negotiable)

When a shadow file breaks after sync, the ONLY fix is:
1. Open the upstream source.
2. See exactly how upstream implements it.
3. Copy that exact solution.
4. Re-apply ONLY the local changes from `smd/`.

FORBIDDEN: workarounds, alternative imports, try/except papering, restructuring
differently from upstream. The sources are correct. Broken means sync is incomplete.

## 3-Commit Gates

| Commit | When | Message |
|---|---|---|
| Commit 1 | After Stage 1 (Prep) | `sync: automated upstream pull <DATE>` |
| Commit 2 | After Stage 3 (Execution + Manual Verification) | `sync: manual merge resolutions <DATE>` |
| Commit 3 | After Stage 3 (Cleanup + Final Validation) | `sync: cleanup and finalization <DATE>` |

Each gate requires explicit **"Proceed with Commit N"** from the user.

## Model Switch Points

| Stage | Model | Reason |
|---|---|---|
| Stage 1 (Prep) | Auto | Routine validation and diffing |
| Stage 2 (Analysis) | PRO | Deep diff analysis, strategic planning, cross-reference |
| Stage 3 (Execution) | Auto / PRO | Implementation (Auto), Final Logic Audit (PRO) |

## Key References

| File | Purpose |
|---|---|
| `kamma/upstream_sync/registry.json` | What to sync, what to skip, what to discuss |
| `kamma/upstream_sync/accepted_sync.json` | Last accepted upstream sync state |
| `kamma/upstream_sync/smd/index.md` | Per-file local changes and sync pitfalls |
| `kamma/upstream_sync/guide.md` | 3-stage workflow, merge strategies, naming policy |
| `kamma/upstream_sync/archive_improvements.md` | Accumulated lessons from past runs |
| `prep_report.md` (thread-local) | Factual diff of upstream changes |
| `prep_manifest.json` (thread-local) | Machine-readable upstream range and path mapping |
| `dynamic_plan.md` (thread-local) | Strategic implementation plan |
