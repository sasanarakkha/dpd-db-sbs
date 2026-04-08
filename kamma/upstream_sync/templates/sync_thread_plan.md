# Plan: Upstream Sync <DATE>

> **Executing model**: Follow the 3-Stage workflow defined in `kamma/upstream_sync/guide.md`.
> Mark tasks `[~]` before starting, `[x]` on completion.

---

## Stage 1: Prep (Factual Analysis)

- [ ] **1.1 Environmental Check**:
  - [ ] `git status` — must be clean.
  - [ ] `git branch -a | grep as_upstream` — tracking branch must exist.
  - [ ] `git tag pre-sync-<DATE>` — backup tag.
- [ ] **1.2 Validation**:
  - [ ] `uv run python3 kamma/upstream_sync/scripts/validate_registry.py` — passes.
  - [ ] `uv run python3 kamma/upstream_sync/scripts/verify_smd_coverage.py` — passes.
- [ ] **1.3 Factual Diff**:
  - [ ] Run `uv run python3 kamma/upstream_sync/scripts/prep_analyzer.py` — generate `prep_report.md`.
  - [ ] Review `prep_report.md` for any unexpected changes.
- [ ] **1.4 Automated Pull + Commit 1**:
  - [ ] Run automated sync script (`full_sync.sh`).
  - [ ] ⛔ **USER APPROVAL GATE** — STOP. Wait for explicit **"Proceed with Commit 1"**.
  - [ ] Stage and present commit: `sync: automated upstream pull <DATE>`.

**Stage 1 complete when:** Baseline verified, prep report generated, Commit 1 staged.

---

## Stage 2: Analysis (Strategic Planning)

> ⚡ **MODEL SWITCH**: Ask user to switch to **Higher model** for this stage.

- [ ] **2.1 Change Impact Assessment**:
  - [ ] Review `prep_report.md`. For each modified source, list all shadow/inspired destinations.
  - [ ] Review `modified_upstream_files` delta.
- [ ] **2.2 Discussion Flags**:
  - [ ] For every `discuss: true` entry that changed: STOP, present diff, state reason, wait for decision.
- [ ] **2.3 Dynamic Plan Creation**:
  - [ ] Create `dynamic_plan.md` in THIS thread folder.
  - [ ] For each action item: include path, source, strategy, and SMD reference.

**Stage 2 complete when:** every changed upstream file has a local action in `dynamic_plan.md`.

---

## Stage 3: Execution & Verification

### Implementation (Lower model)

- [ ] **3.1 Execution**:
  - [ ] Execute `dynamic_plan.md` item-by-item following the **Iron Rule**.
  - [ ] Apply PORT / inspired-backport logic.
  - [ ] Verify namespace isolation (`ru_`, `sbs_`, `dps_` prefixes).
- [ ] **3.2 Dual-Shadow Parity**:
  - [ ] Ensure sibling shadows are updated in the same step.
  - [ ] `uv run pytest tests/test_shadow_parity.py --tb=short -q` (Continuous).

### Logic Audit (Higher model)

- [ ] **3.3 Audit**:
  - [ ] Verify **Iron Rule** compliance for all shadow updates.
  - [ ] Confirm no novel solutions or workarounds.

### Testing & Verification (Lower model)

- [ ] **3.4 Full Test Suite**:
  - [ ] `uv run pytest --tb=short -q` (Full suite).
  - [ ] `uv run python3 tests/check_shadow_modifications.py`.
- [ ] **3.5 Manual Verification**:
  - [ ] ⛔ **MANUAL VERIFICATION GATE** — STOP. Ask user to verify GoldenDict/webapp.
- [ ] **3.6 Commit 2 Gate**:
  - [ ] ⛔ **USER APPROVAL GATE** — Wait for explicit **"Proceed with Commit 2"**.
  - [ ] Stage and present commit: `sync: manual merge resolutions <DATE>`.

### Cleanup & Finalization (Lower model)

- [ ] **3.7 Orphan Cleanup**:
  - [ ] `uv run python3 tests/test_shadow_cleanup.py`. Archive or promote orphans.
- [ ] **3.8 Final Validation**:
  - [ ] Re-run all validators and `verify_smd_coverage.py`.
  - [ ] `uv run ruff check . && uv run ruff format .`.
- [ ] **3.9 Commit 3 Gate**:
  - [ ] Review `kamma/upstream_sync/new_improvements.md` (if it exists) and promote valuable entries to `archive_improvements.md`.
  - [ ] Delete the temporary `kamma/upstream_sync/new_improvements.md` file.
  - [ ] ⛔ **USER APPROVAL GATE** — Wait for explicit **"Proceed with Commit 3"**.
  - [ ] Stage and present commit: `sync: cleanup and finalization <DATE>`.

**Stage 3 complete when:** All implementation items complete, tests pass, manual verification done, orphans archived, Commit 2 & 3 presented.
