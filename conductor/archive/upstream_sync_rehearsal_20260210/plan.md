# Plan: Upstream Sync Rehearsal (Standard Monthly)

## Phase 1: Automated Synchronization [DONE]
- [x] Task: Pre-Sync Branch Check
- [x] Task: Execute Sync Script (Option 2)
- [x] Task: Update Submodules
- [x] Task: AUTO-COMMIT (COMMIT 1/2)

## Phase 2: Manual Merge & Shadow Porting [DONE]
- [x] Task: Integrate Upstream Updates into Modified Files
- [x] Task: Update Shadow Copies (GoldenDict, Kindle RPD, Webapp)
- [x] Task: Documentation Parity
- [x] Task: Update Rehearsal Templates (Registry & Guide)
    - [x] Removed cleanup tasks from templates.
    - [x] Updated guide with 'SYNC ONLY' mandate.
    - [x] Fixed `ru_templates/home.html` and `sbs_templates/home.html` structure.

## Phase 3: Final Logic Audit & Validation [DONE]
- [x] Task: PRO Logic Audit (Verified all parity)
- [x] Task: Run All Tests (33 Passed)
- [x] Task: FINAL MANUAL COMMIT (COMMIT 2/2)

## Phase 4: Manual System Check (Pending)
- [ ] Task: Verify GoldenDict SBS/Ru exports manually.
- [ ] Task: Verify Kindle Ru export manually.
- [x] Task: Verify Webapp (Ru/SBS) manually.
    - [x] Fixed templates syntax.
    - [x] Verified `preloads_ru.py` parity with upstream optimization.
- [x] Task: GUI Verification (DpsView, Fonts, Tabs) manually.
- [ ] Task: Final User Confirmation "Track is complete".
- [ ] Task: Verify GUI2 (DpsView, Fonts, Tabs) manually.
- [ ] Task: Final User Confirmation "Track is complete".
