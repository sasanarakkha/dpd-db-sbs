# Plan: Apply upstream-sync lessons §24–§29

Spec: `kamma/threads/20261105_sync_lessons_24_29/spec.md`
Source lessons: `kamma/upstream_sync/archive_improvements.md` §24–§29

## Architecture Decisions
- **Fix in place, no new modules.** Every change goes into the existing script or doc
  that misbehaved. The only extraction is `find_orphans()` in
  `tests/test_shadow_cleanup.py`, which makes the selection loop unit-testable.
- **Deletion parsing uses `git diff -z --raw`.** One command gives both the old mode
  (gitlink detection) and unquoted paths. No second `ls-tree` call.
- **Gitlinks are warned about, never deleted**, because a submodule dir can hold
  uncommitted user work.
- **`sync_status` stays artifact-based.** The Stage 2/3 split keys on
  `execute_sync_done.json`; "Closed" keys on `accepted_sync.json` matching the manifest.
  No handoff parsing, which would be brittle prose parsing.
- **Validator fallback is git-object lookup, not network.** `git cat-file -e
  upstream/main:<path>` only reads objects that are already fetched.
- **Stale-ack rejection is unchanged** (spec decision 2).
- Every touched `.py` must pass ruff/pyright/pyrefly. For files under `tests/`, use
  `uv run pyright --project /dev/null <file>`. Run targeted pytest files only.

## Phase 1 — Script fixes

- [ ] **1.1 P0 deletion: non-ASCII paths + gitlinks** (`kamma/upstream_sync/scripts/execute_sync.py`, `tests/test_sync_deletion_propagation.py`)
  - Red: add 2 tests reusing the `sync_repo` fixture pattern (`_make_repo_with_two_upstream_commits`, `_setup_worktree`):
    - `test_non_ascii_deletion_removed`: upstream commit 1 adds `kathāsallāpasikkhā.txt`, commit 2 deletes it; after `propagate_upstream_deletions` the worktree file is gone.
    - `test_gitlink_deletion_skipped_with_warning`: commit 1 adds a gitlink with `git update-index --add --cacheinfo 160000,<any 40-hex sha of an existing commit>,sub` and the worktree dir `sub/` holds a file `keep.txt`; commit 2 removes it (`git update-index --force-remove sub`). After the call: no exception, `sub/keep.txt` still exists.
    - Run them and paste the failure output here before fixing.
  - Green: in `propagate_upstream_deletions`, replace the diff with `["git","diff","-z","--raw","--no-renames","--diff-filter=D",f"{a}..{b}"]`. Parse `stdout` split on `\0`. Records come in pairs: meta `":<oldmode> <newmode> <oldsha> <newsha> D"` then path. If the old mode is `160000`, call `pr.amber(f"  P0 skipped submodule: {path} — remove manually (git rm) after reviewing its uncommitted work")` and count it; otherwise keep the existing protected/exists/unlink logic. Update the docstring. Add the skipped count to the final `pr.yes` summary.
  → verify: `uv run pytest tests/test_sync_deletion_propagation.py -v` → all pass (the 8 existing + 2 new).

- [ ] **1.2 Dry run allowed on a dirty tree** (`execute_sync.py`, `tests/test_execute_sync.py`)
  - Red: following `test_execute_sync_rejects_dirty_working_tree` (line ~194, mocks `GitContext`), add `test_dry_run_allowed_on_dirty_working_tree`: `is_dirty=True`, `dry_run=True`, with manifest verification mocked to 0 as the existing dry-run/clean tests do. Expect return 0. Keep the existing rejection test for `dry_run=False`.
  - Green: change the guard at line ~242 to `if context.is_dirty and not dry_run:`.
  → verify: `uv run pytest tests/test_execute_sync.py -v` → all pass.

- [ ] **1.3 sync_status Stage 2 vs 3, and Closed** (`kamma/upstream_sync/scripts/sync_status.py`, `tests/test_sync_status.py`)
  - Red:
    - Change `test_dynamic_plan_present_is_stage_3` to also write `execute_sync_done.json`.
    - Add `test_dynamic_plan_without_done_marker_is_stage_2` (expects stage starting with "Stage 2").
    - Add `test_retrospective_with_matching_accepted_sync_is_closed`: write `accepted_sync.json` in tmp_path with `last_accepted_upstream_sha` equal to the manifest `to_upstream_sha` and pass `accepted_sync_path=`; expect "Closed" in the stage.
    - Make `test_retrospective_present_is_stage_4_finalize` pass a non-matching or missing `accepted_sync_path` so it no longer depends on the real repo file.
    - Add the Closed and new Stage 2 branches to `_all_descriptors` so the drift guards cover them.
  - Green:
    - Add `ACCEPTED_SYNC_PATH = Path(__file__).resolve().parent.parent / "accepted_sync.json"`. Change the signature to `derive_stage(thread_dir: Path, accepted_sync_path: Path = ACCEPTED_SYNC_PATH)`.
    - In the retrospective branch: if the manifest exists, `accepted_sync_path` exists, and their SHAs match, return `StageDescriptor(stage="Stage 4: Closed (sync accepted)", next_command="none — sync closed; start a new sync thread with /update-upstream", owner="ADVANCED", dispatch="self", gate_before=None, gate_after=None, reads=["accepted_sync.json"], produces=[], stop_condition="n/a", guide_anchor=<same Stage 4 anchor>)`.
    - In the dynamic_plan branch: if `execute_sync_done.json` is absent, return the existing Stage 2 descriptor.
    - Update the `derive_stage` docstring.
  → verify: `uv run pytest tests/test_sync_status.py -v` → all pass; `uv run python3 kamma/upstream_sync/scripts/sync_status.py kamma/archive/20261105_upstream_sync` prints `Stage 4: Closed (sync accepted)`.

- [ ] **1.4 Validator: upstream path present only in the upstream ref** (`kamma/upstream_sync/scripts/validate_registry.py`, `tests/test_validate_registry.py`)
  - Red: add `test_upstream_path_found_in_upstream_ref_only`: in tmp_path, `git init`, commit `a.py`, then `git update-ref refs/remotes/upstream/main HEAD` and delete `a.py` from the worktree. A `russian_copies` entry `{"x_ru.py": {"upstream": "a.py", ...}}` with `x_ru.py` present → `validate_registry_core(data, tmp_path)` has no "does not exist" error for `a.py`. Copy the required entry fields from existing fixtures (`base_data`).
  - Green: add helper `_exists_in_upstream_ref(repo_root: Path, path: str, ref: str = "upstream/main") -> bool` running `git -C <repo_root> cat-file -e <ref>:<path.rstrip('/')>` (`check=False`, `capture_output=True`; returns False on `OSError`). Call it as the fallback before appending each upstream "does not exist" error: the shadow mapping file and dir branches (~169–177) and `validate_inspired_by_upstream` (~266). Shadow-path (local) checks are unchanged.
  → verify: `uv run pytest tests/test_validate_registry.py -v` → all pass, including `test_inspired_by_upstream_missing_upstream_target_path`; `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` → valid.

- [ ] **1.5 Orphan scanner reads the index and honours all categories** (`tests/test_shadow_cleanup.py`, new `tests/test_shadow_cleanup_orphans.py`)
  - Red: new test file importing `from tests.test_shadow_cleanup import find_orphans`. Cases with in-memory lists and a minimal registry dict:
    - a path under `scripts/archive/` (skip_sync) is not an orphan
    - an `inspired_by_upstream` key is not an orphan
    - a file under an `inspired_by_upstream` key ending in `/` is not an orphan
    - an unregistered file absent from upstream_files is an orphan
  - Green: extract `find_orphans(current_files: list[str], upstream_files: set[str], registry: dict[str, object]) -> list[str]` from the loop in `main()` (lines ~103–140). Exclusions: `no_sync_files` + `unique_paths` + `skip_sync_patterns`. Shadow map: the 4 `*_copies` + `inspired_by_upstream`. Replace `run_git(["ls-tree","-r","HEAD","--name-only",scan_folder])` with `run_git(["ls-files","--",scan_folder])`. Add type hints to `run_git`'s caller code only where touched.
  → verify: `uv run pytest tests/test_shadow_cleanup_orphans.py -v` → all pass; `uv run python3 tests/test_shadow_cleanup.py --folder scripts/ --dry-run` lists no `scripts/archive/` paths and no `scripts/bash/{generate_components,make_dpd,make_ru_dpd}.sh`.

- [ ] **1.6 "Needs Classification" wording** (`kamma/upstream_sync/scripts/prep_analyzer.py:568`, `kamma/upstream_sync/guide.md:244`)
  - Replace both "register them" sentences with: "These upstream additions have no local collision and are mirrored verbatim. Register one only if Stage 2 decides it needs a local divergence. They do NOT block `execute_sync.py`." (In prep_analyzer, drop the last sentence if the surrounding report already says so.)
  → verify: `rg -n "Register them" kamma/upstream_sync` → no hits; `uv run pytest tests/test_stage1.py -v` → pass.

- [ ] **1.7 Phase 1 verification**
  - Run on each touched `.py`, one command at a time:
    - `uv run ruff check --fix <file>`
    - `uv run ruff format <file>`
    - `uv run pyright <file>` (files in `tests/`: `uv run pyright --project /dev/null <file>`)
    - `uv run --with pyrefly pyrefly check --min-severity warn <file>`
  - Then `uv run pytest tests/test_sync_deletion_propagation.py tests/test_execute_sync.py tests/test_sync_status.py tests/test_validate_registry.py tests/test_shadow_cleanup_orphans.py tests/test_stage1.py -v`.
  → verify: all lint clean (list any pyrefly warnings left, with reasons); all tests pass.

## Phase 2 — Process rules (doc-only)

- [ ] **2.1 §26–§29 rules** (`.claude/agents/sync-fast.md`, `kamma/upstream_sync/guide.md`)
  - sync-fast.md "What You Do": add a bullet: "Lint/format commands use literal file paths only — no shell variables, no `&&`-chained assignments; never run `ruff check --fix` or `ruff format` without an explicit path."
  - guide.md 2a bullet (line ~268): append two sentences:
    - (§27) Run `git diff --name-status <from>..<to> -- tests/` and check local `tests/` for imports of upstream symbols changed in range. Record upstream-test watch items in the owning source file's registry `watch_for` (tests/ is skip_sync).
    - (§29) For framework major-version migrations, AST-scan the framework's attribute/call usage in local files and probe doubtful APIs with `uv run --no-project --with <pkg>==<ver> python -c ...`.
  - guide.md 2c bullet: append (§28) "Re-verify every 2a/2b factual claim against the files before writing a recipe on it; run every recipe `Verify` command once when writing it."
  - guide.md, near the hard-stop/session rules (~line 99): one bullet: "zsh: write `${SHA}:path`, never `$SHA:path` (modifier expansion). Draft threads go in `kamma/drafts/`, never `kamma/threads/` (spec-gate hook)."
  → verify: `rg -n "literal file paths" .claude/agents/sync-fast.md`, `rg -n -- "-- tests/|--no-project --with|Re-verify every|\\$\\{SHA\\}" kamma/upstream_sync/guide.md` → each hits; `uv run pytest tests/test_sync_status.py tests/test_upstream_sync_docs_policy.py -v` → pass.

- [ ] **2.2 Promote = applied or threaded** (`kamma/upstream_sync/guide.md` Stage 4 step 2 ~388–393, `kamma/upstream_sync/templates/retrospective.md` Promote header)
  - guide: replace "Promote any `promote` items to `archive_improvements.md` before running finalize." with: "A `promote` item is done only when its rule/code change is applied now, or when it is recorded in `archive_improvements.md` AND a follow-up thread exists in `kamma/drafts/`, named under the retrospective's 'Open after finalize'. Archive entries alone are not done."
  - template: change the Promote italic line to the same rule in one sentence.
  → verify: `rg -n "Archive entries alone" kamma/upstream_sync/guide.md` hits; `rg -n "kamma/drafts" kamma/upstream_sync/templates/retrospective.md` hits.

- [ ] **2.3 Final verification**
  - `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` → valid.
  - `uv run pytest tests/test_shadow_parity.py tests/test_namespace_isolation.py tests/test_template_syntax.py tests/test_sync_status.py -v` → same baseline as session 10 (only the accepted pre-existing `sutta_central_exporter_ru` parity FAIL).
  - `git status --short` → only the planned files changed, no root scratch; `resources/*` submodule dirt untouched and excluded.
  → verify: outputs as stated; draft commit message prepared for the user (user commits).
