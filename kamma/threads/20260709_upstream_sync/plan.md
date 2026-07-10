# Plan: Upstream Sync 2026-07-09

> Follow the 4-stage workflow + async Docs Translation Track in `kamma/upstream_sync/guide.md`.
> Mark tasks `[~]` before starting, `[x]` on completion. Every stage ends with a fresh-session hard
> stop and updated `handoff.md` — see guide.md § Session Management for the full contract.
> Run `uv run python3 kamma/upstream_sync/scripts/sync_status.py <thread_dir> --instructions` for
> the current stage's guide section instead of re-reading the whole guide.

---

## Stage 1: FAST Prep

**Owner**: FAST (or ADVANCED running the scripted command directly). See guide.md § Stage 1.

- [x] **1.1 Environmental Check**:
  - [x] `git status` — must be clean before sync work begins. (Hard-enforced by
    `execute_sync.py`'s `GitContext` dirty-tree guard at Stage 1.5, not by this checklist item.)
  - [x] `git fetch upstream` — fetch latest upstream refs.
  - [x] `uv run ruff check tools/ scripts/ db/ exporter/ --select F821 --extend-exclude scripts/archive,scripts/dps_archive --quiet` — catches undefined names and syntax/API breakage before sync work begins.
  - [x] Review `kamma/upstream_sync/accepted_sync.json` — starting SHA/date/ref are present.
- [x] **1.2 Pre-sync Shadow Health Check**:
  - [x] `uv run python3 tests/check_shadow_modifications.py` — output is clean, or every warning has an exact ADVANCED-reviewed entry in `kamma/upstream_sync/reviewed_shadow_noops.json`.
  - [x] If the user confirms a warning is intentionally a no-op but gives no specific reason, use this reason exactly: "User reviewed and confirmed this upstream change does not need to be ported to the shadow."
- [x] **1.3 Validation**:
  - [x] `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` — passes.
- [x] **1.4 Factual Diff**:
  - [x] `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py <thread_dir>` — generates `prep_report.md` and `prep_manifest.json`.
  - [x] If `prep_manifest.json.discuss_paths` is non-empty, stop before `execute_sync.py`. (6 discuss paths → routed to Stage 2.)
  - [x] If `prep_manifest.json.blocker_paths` is non-empty, STOP before `execute_sync.py`. (8 blocker paths → routed to Stage 2.) To acknowledge deletion blockers you intend to handle in Stage 2, create `<thread_dir>/run_acknowledged_blockers.txt` (one path per line; `#` comments allowed). `verify_manifest` will warn for each acknowledged path but will not block on them. Collision blockers still require registry changes before `execute_sync.py`.
- [x] **1.5 Automated Pull + Commit 1 Gate**:
  - **PIN NOTE (2026-07-09):** upstream/main advanced +2 CI-only commits (`188600bbf`, `820113551`, single new file `.github/workflows/deconstructor_ci_test.yml`) after Stage 2 approval. Per user decision (Option A), `accepted_sync.json.last_accepted_upstream_ref` AND `prep_manifest.json.target_upstream_ref` pinned to the analyzed SHA `be49bffe…`; the 2 new commits are deferred to the next sync. **STAGE-4 TODO:** after finalize (which derives the next ref from `manifest.target_upstream_ref`), reset `accepted_sync.json.last_accepted_upstream_ref` back to `"upstream/main"`.
  - **TOOLING FIX (2026-07-09), committed `7c2ea4035`:** `execute_sync.py` step 5 used `git restore --source as_upstream --worktree` (no-overlay default) which DELETED every local-only tracked file (~2780 files: shadows, unique_paths, local data). Fixed to `git restore --overlay …` (verified: preserves local files, adds/updates upstream, stays unstaged). Regression from `33ed53d34` (checkout→restore). First two pull attempts wiped the tree (recovered via `git checkout HEAD -- .`, HEAD never lost); third attempt (fix committed first) succeeded.
  - [x] Review `<thread_dir>/run_exclusions.txt` — none for this run.
  - [x] `uv run python3 kamma/upstream_sync/scripts/execute_sync.py <thread_dir>` — SUCCEEDED. 314 files changed (200 M, 108 D, 53 A). All 108 deletions verified upstream-deleted (P0). All local-only files preserved (verified: paths_ru.py, paths_dps.py, sbs_table_functions.py, russian/sbs/tamil.tsv, russian_words_user_dict.txt). `cst_source_sutta_example.py` correctly removed (S10). `as_upstream` → be49bffe2.
  - [x] Confirmed changes left UNSTAGED. Marker `execute_sync_done.json` written.
  - [x] **Commit 1 Gate (USER):** LANDED as `699c10cd1` `#sync: upstream pull 518672a6..be49bffe, 363 files, 2026-07-09`. Committed with `--no-verify` (user-approved) because pre-commit `ruff`/`pyright`/`pyrefly` hooks lint RAW UPSTREAM code (Commit 1 is verbatim upstream by design) — the hook auto-modified 202 files + reported 21 unfixable errors, which would corrupt the pristine baseline Stage 3 diffs against. Pristine index committed; ruff worktree-noise then stashed off (`ruff-worktree-noise-20260709`). **THREE redundant session stashes to drop** (`ruff-worktree-noise`, `sync-rerun2`, `sync-rerun`) — `git stash drop` each; the other `stash@{...}` WIP entries are the user's — do not touch.

**Hard stop**: update `<thread_dir>/handoff.md` (see guide.md § Session Management), then stop.

---

## Stage 2: ADVANCED Analysis

**Owner**: ADVANCED only. See guide.md § Stage 2.

- [x] **2.1** Read `prep_report.md` and `prep_manifest.json`; classify every changed path (port / mirror / preserve / discuss / inspired / skip / docs). (2a complete — see `dynamic_plan.md` §§1-7; includes unregistered-local and orphan classification.)
- [x] **2.2** Resolve every `discuss: true` entry with the user; record decisions in `dynamic_plan.md`. (2b COMPLETE — D1-D13 resolved; scope correction applied, see `skill_scope_improvement.md`.)
- [x] **2.3** Write `<thread_dir>/dynamic_plan.md` with exact file paths, anchors, literal edits, and verify commands — no vague wording. (§9 authored; §5/§6/§7 reconciled with 2b corrections; D3/D5/D6/D7 concrete detail added; two high-risk claims empirically verified.)
- [x] **2.4** Present `dynamic_plan.md` for approval; wait for explicit approval before Stage 3. (APPROVED 2026-07-09. §0 pre-execution mechanics then executed: D8 `tools/ai_models.json` registered in `modified_upstream_files` (PRESERVE, discuss:false); `prep_analyzer.py` rerun; manifest `discuss_paths` → `[]`; `run_acknowledged_blockers.txt` written with the 8 blockers; `validate_registry.py` passes.)

**Hard stop**: update `handoff.md` with decisions and next steps, then stop.

---

## Stage 3: FAST Execution & Verification

**Owner**: FAST only. See guide.md § Stage 3.

- [x] **3.1** Execute `dynamic_plan.md` item by item; mark progress. (All batches A–F done + verified
  from files: A registry-merges, B simple ports+rename+removals, B-completion cst_source, C header-once
  ports, D shadow ports+I3–I8/I11/I14, E I1/I2 ProcessPoolExecutor rewrites, F registry §7 additions.)
- [x] **3.2** Run every plan verification command, plus:
  - [x] `pytest test_shadow_parity test_shadow_cleanup test_namespace_isolation test_template_syntax`:
    `test_shadow_cleanup` ✓, `test_template_syntax` ✓ (178). The `test_shadow_parity` (collection error)
    + `test_namespace_isolation` (30 fail) PRE-EXISTING breakage (both helpers read registry copies as
    `{shadow: upstream_str}` but the schema is `{shadow: {upstream: str, …}}` since `bdddb9e3c`) was
    **RESOLVED during Commit 2** (user-authorized): each helper `upstream` → `upstream["upstream"]` in
    `test_shadow_parity.py` + `test_namespace_isolation.py`; 3 intentional divergences whitelisted. See §3.4.
  - [x] `uv run python3 tests/check_shadow_modifications.py` — SUCCESS (added S9 titlepage no-op ledger
    entry for the current sync_commit `699c10cd1…` in `reviewed_shadow_noops.json`).
  - [x] `uv run python tests/smoke_test_sync.py` — 25 passed / 0 failed.
  - [x] Also: `validate_registry.py` valid; ruff/format/pyright on all 22 hand-edited files 0 errors
    (formatted `export_variant_spelling_ru.py`); `test_ai_manager.py` 20 passed; §8.7 import smoke OK.
- [x] **3.3** Cleanup only as explicitly listed in `dynamic_plan.md`. (D7 rename, D11/D12 removals,
  docs relocations — all done in Batches B/B-completion.)
- [x] **3.4 Commit 2 Gate**: landed as `426aa64fc` (`#sync: manual merge resolutions 2026-07-09`),
  60 files. User authorized commit. Pre-commit hook fully green (ruff/format/pyright/pyrefly).
  Excluded (unstaged, intentional): kindle build artifacts (`titlepage.xhtml`, `content.opf`,
  `shared_data/changed_templates`) and all `resources/*` submodule pointers.
  - Pre-existing test-helper breakage (rich-object registry schema) fixed in
    `test_shadow_parity.py` + `test_namespace_isolation.py`; 3 intentional divergences whitelisted.
  - Pre-commit pyrefly (NOT pyright — pyright excludes gui2, pyrefly has no config so checks all
    staged files) blocked on 18 pre-existing errors in `gui2/dps_example_field.py`. User chose to
    fix them: resolved via `cast()` accessors (`_stash`/`_view`/`_active_page`) for the intentional
    incompatible base-attribute overrides, `cast(ft.ControlEvent, None)` for the base handler that
    ignores `e`, and renamed the incompatible `get_fields`→`get_fields_dps` (all 6 base callers are
    child-overridden and no external caller exists, so behavior is preserved). 0 pyrefly diagnostics.

**Hard stop**: update `handoff.md` with completed/failed items, files changed, test evidence, then stop.

---

## Docs Track: ADVANCED Docs Analysis

**Owner**: ADVANCED only, unnumbered/async. See guide.md § Docs Translation Track. Run
`uv run python3 kamma/upstream_sync/scripts/sync_status.py --section docs-track` for the guide
section instead of re-reading the whole guide.

- [x] Read `docs_parity_report.md` (`uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py <thread_dir>`). (0 missing, 3 stale — all same 1-line `.tar.bz2`→`.tar.xz` diff; 1 unexpected-local file noted informationally.)
- [x] Build a terminology glossary from 3-5 existing `docs_rus/` files. (`build_db.md`, `index.md`, `dpd_headwords_table_ru.md`, `rootdict.md`.)
- [x] Write `<thread_dir>/docs_translation_plan.md`; present for approval. (Written — awaiting user approval before Translation phase.)

**Hard stop**: update `handoff.md` with translation plan decisions, then stop.

---

## Docs Track: FAST Docs Translation

**Owner**: FAST only, unnumbered/async. See guide.md § Docs Translation Track. Run
`uv run python3 kamma/upstream_sync/scripts/sync_status.py --section docs-track` for the guide
section instead of re-reading the whole guide.

- [x] Translate/update files exactly as listed in `docs_translation_plan.md`. (3 one-line
  `.tar.bz2`→`.tar.xz` edits: `local_server_setup.md`, `quick_start.md`, `use_db.md`. User approved
  the plan 2026-07-10.)
- [x] `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py <thread_dir> --strict`. (Exit 1
  — expected: "stale" is a range-based flag (EN file changed within the fixed sync range), not a live
  content diff, so it never clears for this thread regardless of the fix. Confirmed via source read of
  `check_docs_parity.py` lines 236-239. `git diff --stat` confirms exactly the 3 intended 1-line edits
  landed, nothing else.)
- [x] Prepare commit message only: `#docs: translate/update docs_rus/ for sync <from>..<to>`. (See
  handoff.md — message drafted, not committed.)

**Hard stop**: update `handoff.md` with files changed and next action, then stop.

---

## Stage 4: ADVANCED Verification & After-sync

**Owner**: ADVANCED for acceptance; hand off to FAST for mechanical finalization. See guide.md § Stage 4.

- [x] Review Stage 3 and Docs Track evidence; ask user for manual GoldenDict/webapp verification.
- [x] Wait for explicit user confirmation: `all is good, proceed`. (Received 2026-07-10, incl. the Batch E `joinedload(DpdHeadword.rt)` root-render watch item + the kindle-mobi investigation.)
- [x] Write `retrospective.md` (required before finalize); promote accepted items to `archive_improvements.md`. (Done: `retrospective.md` written; promoted §21–§23.)
- [x] If accepted, ADVANCED may run `uv run python3 kamma/upstream_sync/scripts/finalize_accepted_sync.py <thread_dir>` directly. (Ran, exit 0; `accepted_sync.json` advanced to `be49bffe`. PIN reset applied: `last_accepted_upstream_ref` → `"upstream/main"`; +2 CI-only commits `188600bbf`/`820113551` deferred to next sync.)
- [x] Prepare final commit message only after acceptance. (Landed as `39c73fd6f` `#sync: Stage 4 finalize + build-verification fixes` and `436145647` `fix(go-deconstructor): local stopgaps for lookup table db-population`; the separate cl_dps CWD-hardening fix landed as `3828db917`. All confirmed via `git log`.)

**Final hard stop**: update `handoff.md` with final state, verification evidence, files changed, and any remaining risks, then stop.
