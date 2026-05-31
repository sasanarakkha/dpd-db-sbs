# Spec: Upstream Sync <DATE>

## Goal

Port all upstream changes from `digitalpalidictionary/dpd-db` to this fork while preserving Russian,
SBS, DPS, and Tamil localized additions.

## Upstream Diff Range

- **From**: `<FILL: last accepted upstream SHA from accepted_sync.json>`
- **To**: `upstream/main` at `<DATE>`

## Success Criteria

- `kamma/upstream_sync/accepted_sync.json` was reviewed and used as the starting sync point.
- Stage 1 FAST prep produced both `prep_report.md` and `prep_manifest.json`.
- Every model boundary ended with a fresh-session hard stop and updated `handoff.md`.
- FAST performed only mechanical work: commands, scripted checks, factual reports, literal edits, tests, and approved translation execution.
- ADVANCED performed only analysis and planning: risk classification, strategy, `discuss` resolution, plan writing, and acceptance decisions.
- Every changed upstream file was reviewed against `registry.json` and classified in `dynamic_plan.md`.
- All changed `modified_upstream_files` have an explicit PORT, DISCUSS, or PRESERVE decision.
- All shadow files whose upstream source changed have an explicit plan item or documented no-op reason.
- All inspired files whose upstream source changed have an explicit backport decision or documented skip reason.
- All docs parity changes are handled through `docs_translation_plan.md`.
- All automated sync tests pass.
- User manually verified GoldenDict/webapp output and confirmed correct.
- `new_improvements.md` was reviewed, valuable items were promoted, and the temporary file was deleted if present.
- Commit messages were prepared and presented for manual execution; no autonomous commit, pull, or push was performed.

## Iron Rule

When a shadow file breaks after sync, the ONLY fix is:
1. Open the upstream source.
2. See exactly how upstream implements it.
3. Copy that exact solution.
4. Re-apply ONLY the local changes from `smd/`.

FORBIDDEN: workarounds, alternative imports, try/except papering, or restructuring differently from upstream. The sources are correct. Broken means sync is incomplete.

## Model Boundaries

| Stage | Owner | Responsibility |
|---|---|---|
| Stage 1 Prep | FAST | Run commands, generate factual reports, record failures |
| Stage 2 Analysis | ADVANCED | Interpret reports, resolve strategy, write `dynamic_plan.md` |
| Stage 3 Execution | FAST | Execute `dynamic_plan.md` literally and run tests |
| Stage 4.A Docs Analysis | ADVANCED | Analyze docs parity and write `docs_translation_plan.md` |
| Stage 4.B Docs Translation | FAST | Execute `docs_translation_plan.md` literally |
| Stage 5 Verification | ADVANCED | Decide acceptance after user verification |

FAST must stop if analysis, planning, judgment, conflict resolution, or plan repair is needed.
ADVANCED must stop if mechanical editing, command execution, formatting, testing, file copying, or bulk translation is needed.

## Handoff Requirements

Every hard stop must update `<thread_dir>/handoff.md` with:
- Current stage and owner model.
- Completed work.
- Exact commands already run.
- Exact outputs or failures summarized.
- Files changed.
- Open decisions.
- Errors, issues, and repeated mistakes.
- Next model to use.
- Exact restart prompt for a fresh session.
- Instruction: `Do not continue in this session.`

## Commit Gates

| Commit | When | Message |
|---|---|---|
| Commit 1 | After Stage 1 FAST prep and automated pull | `#sync: upstream pull <from>..<to>, <N> files, YYYY-MM-DD` |
| Commit 2 | After Stage 3 FAST execution and verification | `#sync: manual merge resolutions <DATE>` |
| Commit 3 | After cleanup/finalization acceptance | `#sync: cleanup and finalization <DATE>` |
| Docs Commit | After Stage 4.B docs translation if docs changed | `#docs: translate/update docs_rus/ for sync <from>..<to>` |

Each gate requires explicit user approval before manual commit execution.

## Key References

| File | Purpose |
|---|---|
| `kamma/upstream_sync/guide.md` | Canonical 5-stage model-split workflow |
| `kamma/upstream_sync/registry.json` | What to sync, what to skip, what to discuss |
| `kamma/upstream_sync/accepted_sync.json` | Last accepted upstream sync state |
| `kamma/upstream_sync/smd/index.md` | Per-file local changes and sync pitfalls |
| `kamma/upstream_sync/archive_improvements.md` | Accumulated lessons from past runs |
| `<thread_dir>/handoff.md` | Fresh-session resume source of truth |
| `<thread_dir>/prep_report.md` | Factual diff of upstream changes |
| `<thread_dir>/prep_manifest.json` | Machine-readable upstream range and path mapping |
| `<thread_dir>/dynamic_plan.md` | ADVANCED strategic implementation plan |
| `<thread_dir>/docs_translation_plan.md` | ADVANCED docs translation plan |
