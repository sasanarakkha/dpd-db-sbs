# Plan: Upstream Sync <DATE>

> Follow the 5-stage workflow in `kamma/upstream_sync/guide.md`.
> Mark tasks `[~]` before starting, `[x]` on completion.
> Every stage ends with a fresh-session hard stop and updated `handoff.md`.

---

## Stage 1: FAST Prep

**Owner**: FAST only. Run commands and record facts. Do not analyze strategy.

- [ ] **1.1 Environmental Check**:
  - [ ] `git status` — must be clean before sync work begins.
  - [ ] `git fetch upstream` — fetch latest upstream refs.
  - [ ] Review `kamma/upstream_sync/accepted_sync.json` — starting SHA/date/ref are present.
- [ ] **1.2 Pre-sync Shadow Health Check**:
  - [ ] `uv run python3 tests/check_shadow_modifications.py` — output is clean.
- [ ] **1.3 Validation**:
  - [ ] `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` — passes.
  - [ ] `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` — passes.
- [ ] **1.4 Factual Diff**:
  - [ ] `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py <thread_dir>` — generates `prep_report.md` and `prep_manifest.json`.
  - [ ] Record unexpected command failures exactly in `handoff.md`.
- [ ] **1.5 Automated Pull + Commit 1 Gate**:
  - [ ] Review `<thread_dir>/run_exclusions.txt` if needed.
  - [ ] `uv run python3 kamma/upstream_sync/scripts/execute_sync.py <thread_dir>`.
  - [ ] Prepare commit message only: `#sync: upstream pull <from>..<to>, <N> files, YYYY-MM-DD`.

**FAST must stop and request ADVANCED if** registry errors require policy interpretation, a `discuss: true` path changed, a new upstream file needs classification, or command output is ambiguous.

**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with commands run, outputs/failures, files changed, open issues, and repeated mistakes.
- [ ] Restart prompt: `Switch to ADVANCED. Start a fresh session. Continue upstream sync thread: <thread_dir>. First read <thread_dir>/handoff.md, kamma/upstream_sync/guide.md, prep_report.md, and prep_manifest.json. Analyze Stage 1 results and write dynamic_plan.md. Do not perform mechanical edits.`
- [ ] Stop. Do not continue in this session.

---

## Stage 2: ADVANCED Analysis

**Owner**: ADVANCED only. Interpret FAST outputs and write a literal plan. Do not execute it.

- [ ] **2.1 Change Impact Assessment**:
  - [ ] Read `<thread_dir>/prep_report.md`.
  - [ ] Read `<thread_dir>/prep_manifest.json`.
  - [ ] For every changed upstream path, classify the required action: port, mirror, preserve, discuss, inspired backport, skip, or docs translation.
- [ ] **2.2 Discussion Flags**:
  - [ ] For every changed `discuss: true` entry, present the relevant diff and `discuss_reason` to the user.
  - [ ] Record the resolved decision in `dynamic_plan.md`.
- [ ] **2.3 Dynamic Plan Creation**:
  - [ ] Create `<thread_dir>/dynamic_plan.md`.
  - [ ] Every item includes exact file paths, source file paths, anchor strings or line references, literal code/text changes, and verification commands.
  - [ ] Remove all vague wording such as "figure out", "determine", "check", "inspect", or "fix as needed".
- [ ] **2.4 User Approval Gate**:
  - [ ] Present `dynamic_plan.md`.
  - [ ] Wait for explicit approval before Stage 3.

**ADVANCED must stop and request FAST if** files need to be copied, edited, formatted, tested, generated, or translated mechanically.

**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with decisions, open questions, and exact next steps.
- [ ] Restart prompt: `Switch to FAST. Start a fresh session. Continue upstream sync thread: <thread_dir>. First read <thread_dir>/handoff.md, kamma/upstream_sync/guide.md, and <thread_dir>/dynamic_plan.md. Execute dynamic_plan.md literally item by item. Do not analyze or redesign. Stop if any plan item is incomplete or fails unexpectedly.`
- [ ] Stop. Do not continue in this session.

---

## Stage 3: FAST Execution & Verification

**Owner**: FAST only. Execute the approved plan literally. Do not repair or redesign it.

- [ ] **3.1 Implementation**:
  - [ ] Execute `<thread_dir>/dynamic_plan.md` item by item.
  - [ ] Mark progress in `dynamic_plan.md`.
  - [ ] Split after every 5 implementation items.
- [ ] **3.2 Verification**:
  - [ ] Run every verification command specified by `dynamic_plan.md`.
  - [ ] `uv run pytest tests/test_shadow_parity.py tests/test_shadow_cleanup.py tests/test_namespace_isolation.py tests/test_template_syntax.py -v`.
  - [ ] `uv run python3 tests/check_shadow_modifications.py`.
  - [ ] `uv run python tests/smoke_test_sync.py`.
- [ ] **3.3 Cleanup**:
  - [ ] Run orphan cleanup commands only if explicitly listed in `dynamic_plan.md`.
  - [ ] Update `registry.json` and `smd/` only if explicitly listed in `dynamic_plan.md`.
- [ ] **3.4 Commit 2 Gate**:
  - [ ] Prepare commit message only: `#sync: manual merge resolutions <DATE>`.

**FAST must stop and request ADVANCED if** an expected anchor is missing, a test failure is not covered by the plan, a merge conflict requires judgment, or a different implementation seems necessary.

**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with completed items, failed items, files changed, commands run, test evidence, and repeated mistakes.
- [ ] Restart prompt: `Switch to ADVANCED. Start a fresh session. Continue upstream sync thread: <thread_dir>. First read <thread_dir>/handoff.md, kamma/upstream_sync/guide.md, and <thread_dir>/dynamic_plan.md. Analyze Stage 3 evidence and decide whether to proceed to docs parity or write a corrective plan. Do not perform mechanical edits.`
- [ ] Stop. Do not continue in this session.

---

## Stage 4.A: ADVANCED Docs Analysis

**Owner**: ADVANCED only. Analyze docs parity and write a translation plan. Do not bulk translate.

- [ ] **4.A.1 Parity Report**:
  - [ ] Use the FAST output from `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py <thread_dir>` or request FAST to run it if missing.
- [ ] **4.A.2 Terminology and Scope**:
  - [ ] Read 3-5 existing `docs_rus/` files to build a terminology glossary.
  - [ ] For each stale file, capture the exact upstream diff.
- [ ] **4.A.3 Translation Plan**:
  - [ ] Create `<thread_dir>/docs_translation_plan.md`.
  - [ ] Include glossary, translation rules, source paths, target paths, and per-file instructions.
  - [ ] Present plan to user for approval.

**ADVANCED must stop and request FAST if** the parity script must be run, files must be translated, or `mkdocs_ru.yaml` must be edited.

**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md`.
- [ ] Restart prompt: `Switch to FAST. Start a fresh session. Continue upstream sync thread: <thread_dir>. First read <thread_dir>/handoff.md, kamma/upstream_sync/guide.md, and <thread_dir>/docs_translation_plan.md. Execute the docs translation plan literally. Stop if terminology or scope is unclear.`
- [ ] Stop. Do not continue in this session.

---

## Stage 4.B: FAST Docs Translation

**Owner**: FAST only. Execute the approved docs translation plan literally.

- [ ] Translate or update files exactly as listed in `docs_translation_plan.md`.
- [ ] Split after every 5 translation files.
- [ ] Update `mkdocs_ru.yaml` only if explicitly instructed.
- [ ] Prepare commit message only: `#docs: translate/update docs_rus/ for sync <from>..<to>`.

**FAST must stop and request ADVANCED if** terminology, source diff interpretation, or translation scope is unclear.

**Hard stop handoff**:
- [ ] Update `<thread_dir>/handoff.md` with files changed, remaining files, and issues.
- [ ] Restart prompt: `Switch to ADVANCED. Start a fresh session. Continue upstream sync thread: <thread_dir>. First read <thread_dir>/handoff.md, kamma/upstream_sync/guide.md, and docs translation evidence. Decide whether Stage 5 verification can begin. Do not perform mechanical edits.`
- [ ] Stop. Do not continue in this session.

---

## Stage 5: ADVANCED Verification & After-sync

**Owner**: ADVANCED for acceptance decisions. Hand off to FAST for any mechanical finalization.

- [ ] Review Stage 3 and Stage 4 evidence.
- [ ] Ask user for manual GoldenDict/webapp verification.
- [ ] Wait for explicit user confirmation: `all is good, proceed`.
- [ ] Decide whether `accepted_sync.json` may be advanced.
- [ ] If final mechanical edits are needed, write exact FAST instructions and stop.
- [ ] Review `kamma/upstream_sync/new_improvements.md` if it exists; promote accepted items to `archive_improvements.md` by FAST handoff if edits are needed.
- [ ] Prepare final commit message only after acceptance.

**Final hard stop**:
- [ ] Update `<thread_dir>/handoff.md` with final state, verification evidence, files changed, and any remaining risks.
- [ ] Stop.
