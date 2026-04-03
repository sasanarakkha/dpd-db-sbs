# Plan: `/update-upstream` Skill

## Phase 1: File Relocation & Registry Migration

- [ ] Create `kamma/upstream_sync/` directory
- [ ] Copy `dps_sync_registry.json` → `kamma/upstream_sync/registry.json`
- [ ] Add `discuss` and `discuss_reason` fields to all registry entries; mark discussion-flagged files
- [ ] Copy `improvements.md` → `kamma/upstream_sync/improvements.md`
- [ ] Write slimmed `kamma/upstream_sync/guide.md` (process reference, not full protocol)

**Phase 1 complete when:** `kamma/upstream_sync/` exists with registry, improvements, and guide.

---

## Phase 2: Shadow Module Descriptions (`smd.md`)

This is the most important deliverable. Write a concrete per-file entry for every file in the registry.

### 2.1 Modified Upstream Files (13 files)
- [ ] `db/models.py` — SBS table (30+ cols), Russian table (5 cols), Sinhala table, `.sbs`/`.ru` relationships, `root_ru_meaning` on DpdRoot
- [ ] `exporter/webapp/data_classes.py` — `show_ru_data` flag, `.ru`/`.sbs` rendering, extended `string_columns`
- [ ] `exporter/webapp/static/app.js` — SBS search routing (`/sbs/search_json`)
- [ ] `exporter/webapp/static/home.js` — localized start messages (EN → SBS docs, RU → Russian docs)
- [ ] `gui2/main.py` — `fast_api_utils_dps` import, DpsView + AnalysisView tabs
- [ ] `gui2/pass2_add_view.py` — `request_dpd_server` from `fast_api_utils_dps`, font scaling
- [ ] `tools/ai_manager.py` — DeepseekManager, OpenRouterManager, OpenAIManager extras
- [ ] `.gitignore` — DPS-specific exclusions for generated ru/kindle paths
- [ ] `AGENTS.md`, `conductor/product.md`, `conductor/product-guidelines.md`, `conductor/tech-stack.md` — fork identity docs

### 2.2 Triple-Shadow Files (highest risk)
- [ ] `tools/paths.py` → `tools/paths_ru.py` AND `tools/paths_dps.py`
- [ ] `exporter/goldendict/templates/` → `ru_components/templates/` AND `sbs_templates/`
- [ ] `exporter/webapp/templates/` → `ru_templates/` AND `sbs_templates/`
- [ ] `exporter/goldendict/export_epd.py` → `export_epd_sbs.py` (no RU equivalent)

### 2.3 Key Russian Shadow Copies (~49 files)
- [ ] `exporter/goldendict/export_dpd_ru.py` — RuPaths, Russian tuple type, `make_dpd_html_ru()`
- [ ] `exporter/webapp/data_classes_ru.py` — `make_ru_meaning()`, `ru_make_grammar_line()`
- [ ] `exporter/webapp/main_ru.py` — RuPaths, `/sbs/` endpoint routing
- [ ] `tools/tools_for_ru_exporter.py` — Russian meaning construction, abbreviation replacement
- [ ] `db/families/family_*_ru.py` (5 files) — Russian family groupings
- [ ] Remaining ~40 Russian shadow exporters, scripts, templates (batch entry with common pattern)

### 2.4 Key SBS Shadow Copies (~15 files)
- [ ] `exporter/goldendict/export_dpd_sbs.py` — DPSPaths, SBS tuple type, sbs_templates
- [ ] `tools/fast_api_utils_dps.py` — `start_dpd_server()`, `request_dpd_server()`
- [ ] `tools/utils_sbs.py` — SBS utility functions
- [ ] Remaining SBS exporters and scripts

**Phase 2 complete when:** `smd.md` has a concrete entry for every file in the registry. Verified against registry — no gaps.

---

## Phase 3: Write the Skill (`update-upstream.md`)

- [ ] Write Phase 0 — Pre-flight: read smd.md + registry + backup
- [ ] Write Phase 1 — Automated sync script + Commit 1 preparation
- [ ] Write Phase 2 — PRO model analysis → `dynamic_plan.md` with concrete per-file instructions
- [ ] Write Phase 3 — Implementation with Iron Rule printed at start of every task
- [ ] Write Phase 4 — PRO logic audit + smd.md verification per file
- [ ] Write Phase 5 — Testing + Commit 2 gate
- [ ] Write Phase 6 — Cleanup + orphan archiving
- [ ] Write Phase 7 — Final verification + Commit 3 gate
- [ ] Add Iron Rule enforcement block (bold, repeated) at top of skill and in Phases 3 and 4
- [ ] Add discussion flag protocol — STOP blocks for flagged files

**Phase 3 complete when:** Skill file at `/Users/deva/.claude/commands/update-upstream.md` is complete and internally consistent.

---

## Phase 4: Verification

- [ ] Read `smd.md` as if you are the AI agent — can you determine exactly what to preserve in each file?
- [ ] Read `update-upstream.md` — is the Iron Rule unambiguous at every phase?
- [ ] Verify registry `discuss` flags cover all high-risk files
- [ ] Update `kamma/threads.md` to mark thread in progress
- [ ] Update `kamma/setup_state.json` to `3.3_initial_thread_generated`

**Phase 4 complete when:** Human review of smd.md and skill file confirms clarity and completeness.
