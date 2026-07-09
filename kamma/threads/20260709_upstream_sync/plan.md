# Plan: Upstream Sync 2026-07-09

> Follow the 4-stage workflow + async Docs Translation Track in `kamma/upstream_sync/guide.md`.
> Mark tasks `[~]` before starting, `[x]` on completion. Every stage ends with a fresh-session hard
> stop and updated `handoff.md` — see guide.md § Session Management for the full contract.
> Run `uv run python3 kamma/upstream_sync/scripts/sync_status.py <thread_dir> --instructions` for
> the current stage's guide section instead of re-reading the whole guide.

---

## Stage 1: FAST Prep

**Owner**: FAST (or ADVANCED running the scripted command directly). See guide.md § Stage 1.

- [ ] **1.1 Environmental Check**:
  - [ ] `git status` — must be clean before sync work begins. (Hard-enforced by
    `execute_sync.py`'s `GitContext` dirty-tree guard at Stage 1.5, not by this checklist item.)
  - [ ] `git fetch upstream` — fetch latest upstream refs.
  - [ ] `uv run ruff check tools/ scripts/ db/ exporter/ --select F821 --extend-exclude scripts/archive,scripts/dps_archive --quiet` — catches undefined names and syntax/API breakage before sync work begins.
  - [ ] Review `kamma/upstream_sync/accepted_sync.json` — starting SHA/date/ref are present.
- [ ] **1.2 Pre-sync Shadow Health Check**:
  - [ ] `uv run python3 tests/check_shadow_modifications.py` — output is clean, or every warning has an exact ADVANCED-reviewed entry in `kamma/upstream_sync/reviewed_shadow_noops.json`.
  - [ ] If the user confirms a warning is intentionally a no-op but gives no specific reason, use this reason exactly: "User reviewed and confirmed this upstream change does not need to be ported to the shadow."
- [ ] **1.3 Validation**:
  - [ ] `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` — passes.
- [ ] **1.4 Factual Diff**:
  - [ ] `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py <thread_dir>` — generates `prep_report.md` and `prep_manifest.json`.
  - [ ] If `prep_manifest.json.discuss_paths` is non-empty, stop before `execute_sync.py`.
  - [ ] If `prep_manifest.json.blocker_paths` is non-empty, STOP before `execute_sync.py`. To acknowledge deletion blockers you intend to handle in Stage 2, create `<thread_dir>/run_acknowledged_blockers.txt` (one path per line; `#` comments allowed). `verify_manifest` will warn for each acknowledged path but will not block on them. Collision blockers still require registry changes before `execute_sync.py`.
- [ ] **1.5 Automated Pull + Commit 1 Gate**:
  - [ ] Review `<thread_dir>/run_exclusions.txt` if needed.
  - [ ] `uv run python3 kamma/upstream_sync/scripts/execute_sync.py <thread_dir>`.
  - [ ] Confirm `execute_sync.py <thread_dir>` leaves changes unstaged by default; review `git diff` before manual staging.
  - [ ] Prepare commit message only: `#sync: upstream pull <from>..<to>, <N> files, YYYY-MM-DD`.

**Hard stop**: update `<thread_dir>/handoff.md` (see guide.md § Session Management), then stop.

---

## Stage 2: ADVANCED Analysis

**Owner**: ADVANCED only. See guide.md § Stage 2.

- [ ] **2.1** Read `prep_report.md` and `prep_manifest.json`; classify every changed path (port / mirror / preserve / discuss / inspired / skip / docs).
- [ ] **2.2** Resolve every `discuss: true` entry with the user; record decisions in `dynamic_plan.md`.
- [ ] **2.3** Write `<thread_dir>/dynamic_plan.md` with exact file paths, anchors, literal edits, and verify commands — no vague wording.
- [ ] **2.4** Present `dynamic_plan.md` for approval; wait for explicit approval before Stage 3.

**Hard stop**: update `handoff.md` with decisions and next steps, then stop.

---

## Stage 3: FAST Execution & Verification

**Owner**: FAST only. See guide.md § Stage 3.

- [ ] **3.1** Execute `dynamic_plan.md` item by item; mark progress.
- [ ] **3.2** Run every plan verification command, plus:
  - [ ] `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py -v`.
  - [ ] `uv run python3 tests/check_shadow_modifications.py`.
  - [ ] `uv run python tests/smoke_test_sync.py`.
- [ ] **3.3** Cleanup only as explicitly listed in `dynamic_plan.md`.
- [ ] **3.4 Commit 2 Gate**: prepare commit message only: `#sync: manual merge resolutions 2026-07-09`.

**Hard stop**: update `handoff.md` with completed/failed items, files changed, test evidence, then stop.

---

## Docs Track: ADVANCED Docs Analysis

**Owner**: ADVANCED only, unnumbered/async. See guide.md § Docs Translation Track. Run
`uv run python3 kamma/upstream_sync/scripts/sync_status.py --section docs-track` for the guide
section instead of re-reading the whole guide.

- [ ] Read `docs_parity_report.md` (`uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py <thread_dir>`).
- [ ] Build a terminology glossary from 3-5 existing `docs_rus/` files.
- [ ] Write `<thread_dir>/docs_translation_plan.md`; present for approval.

**Hard stop**: update `handoff.md` with translation plan decisions, then stop.

---

## Docs Track: FAST Docs Translation

**Owner**: FAST only, unnumbered/async. See guide.md § Docs Translation Track. Run
`uv run python3 kamma/upstream_sync/scripts/sync_status.py --section docs-track` for the guide
section instead of re-reading the whole guide.

- [ ] Translate/update files exactly as listed in `docs_translation_plan.md`.
- [ ] `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py <thread_dir> --strict`.
- [ ] Prepare commit message only: `#docs: translate/update docs_rus/ for sync <from>..<to>`.

**Hard stop**: update `handoff.md` with files changed and next action, then stop.

---

## Stage 4: ADVANCED Verification & After-sync

**Owner**: ADVANCED for acceptance; hand off to FAST for mechanical finalization. See guide.md § Stage 4.

- [ ] Review Stage 3 and Docs Track evidence; ask user for manual GoldenDict/webapp verification.
- [ ] Wait for explicit user confirmation: `all is good, proceed`.
- [ ] Write `retrospective.md` (required before finalize); promote accepted items to `archive_improvements.md`.
- [ ] If accepted, ADVANCED may run `uv run python3 kamma/upstream_sync/scripts/finalize_accepted_sync.py <thread_dir>` directly (pre-authorized scripted command, same carve-out as Stage 1), or write exact FAST handoff instructions to run it.
- [ ] Prepare final commit message only after acceptance.

**Final hard stop**: update `handoff.md` with final state, verification evidence, files changed, and any remaining risks, then stop.
