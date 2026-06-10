# Plan: Upstream Sync Skill Improvements (Audit Follow-up)

> Spec: `spec.md` in this thread. Follow `kamma/workflow.md` (TDD lifecycle,
> quality gates, phase checkpoints). Mark tasks `[~]` in progress, `[x]` done.

## Architecture Decisions

- **Order: behavior/code first, docs last.** Script changes (Phases 1–3) land
  before the doc consolidation (Phase 4) so `guide.md` is rewritten exactly
  once, describing final behavior (new staging semantics, blocker/ack
  workflow, subagent dispatch).
- **Typed refactor is one atomic task.** Splitting `registry_helper.py` and
  its 6 script consumers across tasks would leave the tree broken mid-phase;
  they change together, tests updated in the immediately following task.
- **Helper API shape:** `load_registry()` → `RegistryData`,
  `load_accepted_sync_state()` → `AcceptedSyncState`,
  `load_prep_manifest()` → `PrepManifest` (frozen dataclasses from
  `sync_schema.py`). Derived getters (`get_strict_shadow_mappings`, etc.)
  become thin functions over `RegistryData` attributes — names preserved to
  limit churn in shadow-parity/namespace tests.
- **New manifest field:** `needs_classification_paths` (required list, may be
  empty) in `prep_manifest.json` / `PrepManifest`. Archived manifests are not
  migrated; only new threads matter.
- **Collision definition (Phase 3):** an added upstream path blocks iff
  (a) the path exists in the local worktree, or (b) it equals/falls under any
  local path registered in `russian_copies`/`sbs_copies`/`dps_copies`/
  `tamil_copies`/`inspired_by_upstream` keys or `unique_paths`. Everything
  else → `needs_classification_paths`.
- **Ack file:** `<thread_dir>/run_acknowledged_blockers.txt`, same comment/
  line format as `run_exclusions.txt`. Read by `verify_manifest` (it already
  receives `thread_dir`); acknowledged paths are subtracted from effective
  blockers but still printed as warnings.
- **Subagent file at `.claude/agents/sync-fast.md`** (project-level, committed),
  `model: sonnet`, restricted tools. Guide describes dispatch as primary; the
  restart-prompt template moves to a "Manual fallback" subsection unchanged.
- **Not abstracted deliberately:** no shared "docs framework"; `guide.md`
  stays one flat Markdown file. No new config for collision rules.

---

## Phase 1: execute_sync staging fix

- [ ] 1.1 Write failing test in `tests/test_execute_sync.py`: fixture repo
      where sync runs; assert post-sync `git diff --cached` is empty and
      `git diff` shows changes; assert `--stage` then stages everything.
      Also cover: file deleted upstream stays present (current behavior),
      excluded file restored correctly.
  → verify: `uv run pytest tests/test_execute_sync.py -v` — new tests fail
    against current code (staged), rest pass.
- [ ] 1.2 Replace `git checkout as_upstream -- .` in
      `kamma/upstream_sync/scripts/execute_sync.py` (step 5) with
      `git restore --source as_upstream --worktree -- .`; re-check step 6
      exclusion restore + step 7 `--stage` logic against unstaged state;
      first confirm command equivalence empirically in a temp repo
      (`temp/staging_probe.py`, delete after).
  → verify: `uv run pytest tests/test_execute_sync.py -v` all pass; probe
    output recorded in handoff.md; temp file deleted.
- [ ] 1.3 Correct the three stale claim lines only (no restructuring yet):
      `guide.md:196-197`, `README.md` core-tooling row,
      `templates/sync_thread_plan.md` task 1.5.
  → verify: `rg -n "leaves changes unstaged|git diff --cached" kamma/upstream_sync/`
    shows only wording consistent with new behavior.
- [ ] 1.4 Phase gate: quality gates on changed files.
  → verify: `uv run ruff check --fix`, `uv run ruff format`,
    `uv run pyright`, `uv run --with pyrefly pyrefly check --min-severity warn`
    on `execute_sync.py`; `uv run pytest tests/test_execute_sync.py -v` green.
    Prepare commit message `fix(sync): leave execute_sync changes unstaged as documented`.

## Phase 2: Script cleanups (typed refactor, strict helpers, dead code)

- [ ] 2.1 Typed round-trip refactor (atomic): `registry_helper.py` returns
      `sync_schema` dataclasses; delete `type AcceptedSyncState`/`PrepManifest`
      dict aliases; update consumers to attribute access in the same change:
      `prep_analyzer.py`, `execute_sync.py`, `sync_runtime.py`
      (`verify_manifest` drops isinstance re-checks),
      `finalize_accepted_sync.py`, `check_docs_parity.py`,
      `init_sync_thread.py`, `gen_smd_scaffold.py` (if affected),
      `validate_registry.py`/`verify_smd_coverage.py` (signature touchpoints).
  → verify: `uv run pyright kamma/upstream_sync/scripts/` clean;
    `rg -n "type AcceptedSyncState|type PrepManifest" kamma/` empty.
- [ ] 2.2 Update all test consumers to the typed API:
      `tests/test_sync_state.py`, `test_prep_analyzer.py`,
      `test_execute_sync.py`, `test_finalize_accepted_sync.py`,
      `test_check_docs_parity.py`, `test_init_sync_thread.py`,
      `test_gen_smd_scaffold.py`, `test_sync_schema.py`,
      `tests/check_shadow_modifications.py` + its test,
      `test_shadow_parity.py`, `test_namespace_isolation.py`,
      `test_registry_category_naming.py`, `test_validate_registry.py`,
      `test_verify_smd_coverage.py` (only where helper APIs are touched).
  → verify: run each listed test file individually with
    `uv run pytest <file> -v` — all green.
- [ ] 2.3 Strict helpers: remove lenient branches in
      `get_modified_upstream_paths` / `get_string_mapping` (derive from
      `RegistryData`); add a test proving malformed registry now fails at
      `load_registry` rather than being silently filtered.
  → verify: `uv run pytest tests/test_sync_state.py tests/test_validate_registry.py -v`.
- [ ] 2.4 Remove dead CLI: delete `print-exclusions`/`print-target-ref`
      subcommands and functions from `sync_runtime.py` (keep
      `verify_manifest`); fold `get_permanent_exclusions` duplication
      (`execute_sync.py`) into one helper; update `tests/test_sync_state.py`.
  → verify: `rg -n "print-exclusions|print_target_ref|print_exclusions" --type py`
    returns nothing; tests green.
- [ ] 2.5 `prep_analyzer.py` dedup: extract `match_sources(path, mapping)`
      replacing the 4× dir-or-exact loops; fix added-files-under-mapped-dirs
      double-listing (report them under Shadow/Inspired Sources only);
      extend `tests/test_prep_analyzer.py` with an added-file-in-mapped-dir case.
  → verify: `uv run pytest tests/test_prep_analyzer.py -v`; report fixture
    shows the path in exactly one section.
- [ ] 2.6 Drop redundant `resolve_commit_sha` rev-parse of an already-full
      SHA in `finalize_accepted_sync.py`.
  → verify: `uv run pytest tests/test_finalize_accepted_sync.py -v`.
- [ ] 2.7 Phase gate: quality gates on every file changed in Phase 2.
  → verify: ruff/pyright/pyrefly per changed file; all Phase-2 test files
    green. Prepare commit message
    `refactor(sync): typed helpers, strict registry access, remove dead CLI`.

## Phase 3: Blocker softening (collision-only) + acknowledgment file

- [ ] 3.1 Schema first: add `needs_classification_paths` to
      `sync_schema.PrepManifest` (+ `to_json`), with tests for presence,
      empty default rejection rules, and path validation.
  → verify: `uv run pytest tests/test_sync_schema.py -v`.
- [ ] 3.2 `prep_analyzer.py`: implement collision rule from Architecture
      Decisions; non-colliding `A` paths → `needs_classification_paths` +
      new report section "Needs Classification (Stage 2)"; colliding paths
      remain blockers with the collision reason in the report. Tests:
      non-colliding add, add colliding with worktree file, add colliding
      with registered local path, deletion (still blocker).
  → verify: `uv run pytest tests/test_prep_analyzer.py -v`.
- [ ] 3.3 Ack file: `verify_manifest` (sync_runtime) reads
      `<thread_dir>/run_acknowledged_blockers.txt`, subtracts acknowledged
      paths from effective blockers, warns for each acknowledged path,
      fails on acknowledged paths not present in the manifest (stale ack).
      Tests: acknowledged passes, unacknowledged fails, stale ack fails.
  → verify: `uv run pytest tests/test_sync_state.py -v`.
- [ ] 3.4 Thread template + init: add the ack file to
      `templates/sync_thread_plan.md` Stage 1 checklist wording and to
      `init_sync_thread.py` next-steps output if referenced.
  → verify: `uv run pytest tests/test_init_sync_thread.py -v`;
    `rg -n "run_acknowledged_blockers" kamma/` shows template + scripts + tests.
- [ ] 3.5 Phase gate: quality gates on changed files; full sync-script test
      battery.
  → verify: per-file ruff/pyright/pyrefly;
    `uv run pytest tests/test_sync_schema.py tests/test_prep_analyzer.py tests/test_sync_state.py tests/test_execute_sync.py tests/test_finalize_accepted_sync.py -v` green.
    Prepare commit message
    `feat(sync): collision-only blockers + run-scoped acknowledgment file`.

## Phase 4: Doc consolidation + subagent dispatch

- [ ] 4.1 Rewrite `guide.md` as the single canonical protocol: keep Iron
      Rule, registry categories, SMD rules, naming policy, discussion
      protocol, stage definitions; integrate new staging wording (Phase 1),
      blocker/ack semantics (Phase 3); replace the "MANDATORY MODEL SWITCH"
      table with **subagent dispatch as primary** (Opus parent dispatches
      Stage 1 / Stage 3 batches ≤5 items / Stage 4.B to `sync-fast`;
      user gates stay in parent) and a "Manual fallback" subsection holding
      the existing restart-prompt template.
  → verify: read-through against spec item 2+4 checklist; Iron Rule string
    occurs in exactly one file:
    `rg -l "ONLY permitted fix" kamma/ .claude/` → `guide.md` only.
- [ ] 4.2 Create `.claude/agents/sync-fast.md` (`model: sonnet`,
      `tools: Read, Edit, Write, Bash, Grep, Glob`; body: FAST contract,
      Iron-Rule-by-reference, stop conditions, handoff.md duty).
  → verify: file parses (valid YAML frontmatter); `claude` lists the agent
    (user confirms via `/agents`) or frontmatter fields match
    code.claude.com/docs/en/sub-agents.
- [ ] 4.3 Shrink `README.md` to quick-start + command table + file inventory
      (absorb unique `infrastructure.md` content: file table, legacy-status
      notes worth keeping); delete `infrastructure.md`.
  → verify: `rg -n "infrastructure.md" --hidden -g '!archive'` only in
    `kamma/upstream_sync/archive_improvements.md` historical notes (or zero).
- [ ] 4.4 Delete `stages/` (3 files); slim `templates/sync_thread_plan.md`
      and `templates/sync_thread_spec.md` to thread-specific content
      referencing `guide.md` (remove restated Iron Rule, model tables,
      handoff requirement lists); update `init_sync_thread.py` rendered
      handoff/next-steps to dispatch-first wording.
  → verify: `rg -n "upstream_sync/stages" .` empty;
    `uv run pytest tests/test_init_sync_thread.py -v` green.
- [ ] 4.5 Cross-reference sweep + policy tests: update
      `tests/test_upstream_sync_docs_policy.py`,
      `tests/test_thread_rename_references.py` if they assert deleted paths;
      update `kamma/tech.md` sync-workflow constraint line; check
      `scripts/cl_dps/dpd-kamma-sync` comments (expected: no change).
  → verify: `uv run pytest tests/test_upstream_sync_docs_policy.py tests/test_thread_rename_references.py -v`;
    `rg -n "stages/prep|stages/analysis|stages/execution|infrastructure\.md" kamma/ tests/ scripts/` empty.
- [ ] 4.6 Phase gate: quality gates on changed Python files; prepare commit
      message `docs(sync): single canonical guide + sync-fast subagent dispatch`.
  → verify: per-file ruff/pyright/pyrefly on `init_sync_thread.py`; all
    Phase-4 test files green.

## Phase 5: Final verification sweep

- [ ] 5.1 Run the full targeted battery (one file at a time):
      all 16 sync-related test files listed in spec §"How We'll Know".
  → verify: every `uv run pytest tests/<file> -v` green; results table in
    handoff.md.
- [ ] 5.2 Registry/SMD gate (mandatory for any registry-adjacent change):
      `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` and
      `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py`.
  → verify: both exit 0.
- [ ] 5.3 Duplication proof + stale-reference proof (spec criteria 2):
      Iron Rule, model table, handoff list each in `guide.md` only; no
      references to deleted files anywhere outside `archive/`.
  → verify: documented `rg` outputs in handoff.md, all empty/single-hit.
- [ ] 5.4 Root cleanliness + temp cleanup; prepare final summary for user
      manual verification (next real sync is the end-to-end test).
  → verify: `git status` shows only intended changes; no `temp/` leftovers.
