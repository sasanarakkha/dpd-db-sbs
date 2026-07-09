# Spec: Upstream Sync 2026-07-09

## Goal

Port all upstream changes from `digitalpalidictionary/dpd-db` to this fork while preserving Russian,
SBS, DPS, and Tamil localized additions.

## Upstream Diff Range

- **From**: `518672a65fa3ea7c36c4c754dc5276bb41f92da7`
- **To**: `upstream/main` at `2026-07-09`

## Success Criteria

- `kamma/upstream_sync/accepted_sync.json` was reviewed and used as the starting sync point.
- Stage 1 FAST prep produced both `prep_report.md` and `prep_manifest.json`.
- Every model boundary ended with a fresh-session hard stop and updated `handoff.md`.
- FAST performed only mechanical work: commands, scripted checks, factual reports, literal edits, tests, and approved translation execution.
- ADVANCED performed only analysis and planning: risk classification, strategy, `discuss` resolution, plan writing, and acceptance decisions.
- Every changed upstream file was reviewed against `registry.json` and classified in `dynamic_plan.md`.
- Any changed upstream source with no shadow edit is either ported before sync or recorded with an exact reviewed no-op in `kamma/upstream_sync/reviewed_shadow_noops.json`.
- All changed `modified_upstream_files` have an explicit PORT, DISCUSS, or PRESERVE decision.
- All shadow files whose upstream source changed have an explicit plan item or documented no-op reason.
- All inspired files whose upstream source changed have an explicit backport decision or documented skip reason.
- All docs parity changes are handled through `docs_translation_plan.md`.
- All automated sync tests pass.
- User manually verified GoldenDict/webapp output and confirmed correct.
- `retrospective.md` was written and any `promote` items were promoted to `archive_improvements.md`.
- Commit messages were prepared and presented for manual execution; no autonomous commit, pull, or push was performed.

For the Iron Rule, model responsibilities, handoff requirements, and subagent dispatch protocol,
see **[guide.md](../guide.md)**.

## Commit Gates

| Commit | When | Message |
|---|---|---|
| Commit 1 | After Stage 1 FAST prep and automated pull | `#sync: upstream pull <from>..<to>, <N> files, YYYY-MM-DD` |
| Commit 2 | After Stage 3 FAST execution and verification | `#sync: manual merge resolutions 2026-07-09` |
| Commit 3 | After cleanup/finalization acceptance | `#sync: cleanup and finalization 2026-07-09` |
| Docs Commit | After Docs Track translation if docs changed | `#docs: translate/update docs_rus/ for sync <from>..<to>` |

Each gate requires explicit user approval before manual commit execution.

## Key References

| File | Purpose |
|---|---|
| `kamma/upstream_sync/guide.md` | Canonical 4-stage model-split workflow + async Docs Translation Track |
| `kamma/upstream_sync/registry.json` | What to sync, what to skip, what to discuss |
| `kamma/upstream_sync/accepted_sync.json` | Last accepted upstream sync state |
| `kamma/upstream_sync/archive_improvements.md` | Accumulated lessons from past runs |
| `<thread_dir>/handoff.md` | Fresh-session resume source of truth |
| `<thread_dir>/prep_report.md` | Factual diff of upstream changes |
| `<thread_dir>/prep_manifest.json` | Machine-readable upstream range and path mapping |
| `<thread_dir>/dynamic_plan.md` | ADVANCED strategic implementation plan |
| `<thread_dir>/docs_translation_plan.md` | ADVANCED docs translation plan |
