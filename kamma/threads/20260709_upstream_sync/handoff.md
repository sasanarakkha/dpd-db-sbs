# Handoff: Upstream Sync 2026-07-09

## Status

**Stage 2 COMPLETE and APPROVED.** User approved `dynamic_plan.md` on 2026-07-09 (task 2.4 `[x]`).
The §0 pre-execution mechanics are DONE (see below). The thread is now at a **setup-commit gate**
that must clear before `execute_sync.py` can run. Owner: ADVANCED presented the gate; USER commits;
then Stage 1.5 pull + Stage 3 FAST.

## §0 pre-execution mechanics — DONE (this session)

1. **D8 registry entry added** — `tools/ai_models.json` appended to `registry.json`
   `modified_upstream_files` with `sync_rule: PRESERVE`, `discuss: false` (always stays local; never
   gates a sync). It is now in the `execute_sync.py` restore set, so the pull will not clobber it.
2. **`prep_analyzer.py` rerun** — manifest regenerated; `ai_models.json` moved out of
   `needs_classification`/`unregistered_local`.
3. **Manifest `discuss_paths` → `[]`** — hand-edited (all D1–D6 resolved). Clears the discuss gate.
4. **`run_acknowledged_blockers.txt` written** — 8 blockers (7× `shared_data/help/*` deletions +
   byte-identical `exporter/analysis/ui_utils.py` collision).
5. **`validate_registry.py` passes** (exit 0). Manifest gate state: `discuss_paths=[]`,
   `blocker_paths` count 8 (all acknowledged).

## SETUP-COMMIT GATE (next action — USER commits)

`execute_sync.py` (line 249) HARD-BLOCKS on a dirty working tree
(`git status --porcelain --ignore-submodules=dirty`, which also counts untracked files). All §0 +
thread-bookkeeping edits live in `kamma/` (no_sync — never touched by the pull), but the blunt guard
still blocks. So the tree must be committed clean first.

**Commit scope (8 files, all `kamma/`):**
- `kamma/upstream_sync/registry.json` (D8 entry)
- `kamma/threads/20260709_upstream_sync/prep_manifest.json` (discuss_paths → [])
- `kamma/threads/20260709_upstream_sync/prep_report.md` (regenerated)
- `kamma/threads/20260709_upstream_sync/plan.md`, `handoff.md`
- `kamma/threads/20260709_upstream_sync/dynamic_plan.md` (untracked)
- `kamma/threads/20260709_upstream_sync/run_acknowledged_blockers.txt` (untracked)
- `kamma/threads/20260709_upstream_sync/skill_scope_improvement.md` (untracked)

**Excluded:** 7 dirty `resources/*` submodules (bw2, dpd-updater, dpd-updater-go, fdg_dpd,
other-dictionaries, sc-data, tpr_downloads) — NOT commit scope; `--ignore-submodules=dirty` means
they will not block the pull either.

**Prepared message:**
`#sync: stage-2 analysis complete + pre-execution setup (D8 registry, ack blockers, discuss cleared)`

## After the setup commit — forward plan

1. **Stage 1.5 pull** (`execute_sync.py <thread_dir>`) — orchestrator MAY run this pre-authorized
   scripted command directly (guide §Stage 1 carve-out), OR dispatch `sync-fast`. Leaves changes
   UNSTAGED. Expect a LARGE diff: P0 deletion pass removes ~108 files (whole upstream-deleted
   `scripts/archive/` tree, `tests/exporter/kindle|tbw/*`, etc.) — this is correct delete-to-match,
   NOT a fault (dynamic_plan §0.6). Submodule gitlink updates pulled from upstream ARE Commit-1 scope
   (distinct from the locally-dirty submodules above).
2. **Commit 1 gate (USER)**: `#sync: upstream pull <from>..<to>, <N> files, 2026-07-09`.
3. **Stage 3 FAST** (dispatch `sync-fast`, sequential batches): execute `dynamic_plan.md` §9 recipes
   (D1–D8/D13 manual merges, S1–S13 shadow ports, I1–I15 inspired backports, D7 rename fan-out, D11
   removals, D12 explicit `git rm`), then the §8 verification battery, then Commit 2 gate (message
   only: `#sync: manual merge resolutions 2026-07-09`).
   - Dispatch prompt = embed `uv run python3 kamma/upstream_sync/scripts/sync_status.py <thread_dir>
     --instructions` output (NOT a whole-guide read). Verify subagent work from files, not self-report.
4. **Docs Track** (ADVANCED analysis → FAST translation), **Stage 4** acceptance.

## Highest-risk Stage 3 items (from §9)

- **I1/I2** (largest): port `export_dpd.py` ProcessPoolExecutor rewrite into `export_dpd_ru.py` /
  `export_dpd_sbs.py`, re-layering RU/SBS joinedloads + locale flags.
- **S4/S6/S7**: pulled `data_classes.py` constructor signatures change → shadow subclasses MUST adapt
  (S4 eliminates the `DeconstructorData_ru` subclass; header-once) or they crash at runtime.
- **S10**: switch `cst_source_sutta_example` import → `cst_source` (old module deleted by P0) or ImportError.
- **S12+I14+I15**: bz2→xz fan-out (server script, release workflows, docs).
- Verified N/A: I4/I5 `zip[1:]` bibliography bug ABSENT in RU/SBS copies; I6 RU has no `see` builder.

## Last upstream sync range

- **From SHA**: `518672a65fa3ea7c36c4c754dc5276bb41f92da7` (2026-06-12)
- **To**: `be49bffe2c2c85971784337d4e09915ad1f42800` (`upstream/main`, 2026-07-09, 120 commits)

## Errors, Issues, And Repeated Mistakes

- Transient `.git/index.lock` race when scripts `git add` right after bulk writes — retry manually.
- `ruff --exclude` on CLI REPLACES pyproject excludes; always `--extend-exclude`.
- Dirty `resources/*` submodules: NOT commit scope, EXCEPT upstream gitlink updates pulled by
  execute_sync (those belong to Commit 1). Report both kinds separately at each commit gate.
- `execute_sync.py` dirty-guard counts UNTRACKED files too → all thread artifacts must be committed
  before the pull (this is the setup-commit gate above).
- `as_upstream` staleness self-heals in `execute_sync.py` (force `update-ref` to target_sha) — no manual fix.

## Retrospective candidates (for Stage 4)

- (carried) stage1 lint gate fixes; tests/kamma rename; "never name a tests/ subpackage after a
  top-level repo package" (tests/exporter/ still shadows root exporter/).
- Local-commit sweep caught unregistered locally-modified upstream files (ai_models.json,
  example_bolding fix) the registry missed — consider adding to prep_analyzer.
- `skill_scope_improvement.md` — guide/skill fixes surfaced during 2b scope correction; apply as a
  SEPARATE post-sync task (do NOT act during this sync).

## Next Model

USER (commit), then ADVANCED orchestrator to run/dispatch Stage 1.5 pull. Consider a fresh session
for the pull to keep context light.

## Restart Prompt

```text
Continue upstream sync thread: kamma/threads/20260709_upstream_sync.
Stage 2 is COMPLETE + APPROVED; §0 pre-execution mechanics DONE (D8 registry,
manifest discuss_paths=[], run_acknowledged_blockers.txt, validate_registry green).
The setup-commit gate has been (or must be) cleared: commit the 8 kamma/ files with
message "#sync: stage-2 analysis complete + pre-execution setup ...", excluding the
7 dirty resources/* submodules. Then run Stage 1.5 pull:
`uv run python3 kamma/upstream_sync/scripts/execute_sync.py kamma/threads/20260709_upstream_sync`
(leaves changes unstaged; expect ~108-file P0 deletion — correct delete-to-match).
Prepare Commit 1 (`#sync: upstream pull 518672a..be49bffe, <N> files, 2026-07-09`),
then dispatch sync-fast for Stage 3 §9 recipes + §8 battery + Commit 2 gate.
```
