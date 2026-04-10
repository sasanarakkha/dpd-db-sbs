# Dynamic Plan: April 2026 Upstream Sync

**Upstream Range:** `89dcdaf3` → `9af5f7ee` (352 files)  
**Stage:** 2 — Analysis  
**Date:** 2026-04-09  

---

## Discussion Flags (MUST resolve before Stage 3)

### D1. `.gitignore` — ✅ RESOLVED: proceed
**Upstream changes:** Alphabetical re-sort, new entries (`credentials.json`, `dpd.db.tar.bz2`, `.codex`, `.zed/tasks.json`, `.claude/scheduled_tasks.lock`, `go_modules/deconstructor/deconstructor`), removed/renamed deconstructor archive patterns.  
**Decision:** Accept all new upstream entries and re-sort. Preserve DPS block verbatim.

### D2. `AGENTS.md` — ✅ RESOLVED: concise-only update
**Upstream changes:** +185 lines — major rewrite (Python hints, Debugging, Imports, Dependencies, Context7, Project Specs, etc.).  
**Decision:** Do NOT port verbatim. Review the diff, identify what is genuinely new and not already covered in our CLAUDE.md, then add a concise summary of only those items to the "Project Rules (from original upstream)" section. Most upstream content is already covered or is upstream-specific overhead. Key new item to add: Context7 MCP reference.

### D3. `gui2/main.py` — ✅ RESOLVED: proceed
**Upstream changes:** +57 lines — `CompoundTypeTabView` tab, confirmation dialog on Update, Ctrl+S save shortcut.  
**Decision:** Port all three features. Preserve DPS imports (`fast_api_utils_dps`) and `DpsView`/`AnalysisView` tabs.

---

## Group A: Shadow Copies — Russian (`russian_copy`, PORT)

### A1. `db/families/family_compound.py` → `family_compound_ru.py`
- **Delta:** 10 lines changed upstream
- **Strategy:** Diff upstream old→new, port matching structural changes into `_ru.py`, preserve `html_ru`/`data_ru` columns and `RuPaths` usage.

### A2. `db/families/family_idiom.py` → `family_idiom_ru.py`
- **Delta:** 12 lines changed upstream
- **Strategy:** Port structural changes. Preserve RU imports, `joinedload(DpdHeadword.ru)`, `html_ru`/`data_ru` writes, in-place update pattern.

### A3. `db/families/family_root.py` → `family_root_ru.py`
- **Delta:** 16 lines changed upstream
- **Strategy:** Port structural changes. Preserve RU imports, `root_ru_meaning`/`html_ru`/`data_ru`, custom `make_root_header_ru()`, absent functions.

### A4. `db/families/family_set.py` → `family_set_ru.py`
- **Delta:** 134 lines changed upstream (LARGEST — priority review)
- **Strategy:** This is the biggest change. Read the full upstream diff carefully. Port all structural/logic changes into `_ru.py` while preserving `html_ru`/`set_ru`/`data_ru` columns, `populate_set_ru_and_check_errors()`, and in-place update pattern.

### A5. `db/families/family_word.py` → `family_word_ru.py`
- **Delta:** 10 lines changed upstream
- **Strategy:** Port structural changes. Preserve RU imports, `html_ru`/`data_ru`, in-place update, Anki Russian data fields.

### A6. `exporter/deconstructor/deconstructor_exporter.py` → `deconstructor_exporter_ru.py`
- **Delta:** 6 lines changed upstream
- **Strategy:** Minor changes. Port into `_ru.py`, preserve `DeconstructorDataRu`, `ProgData` with `rupth`, Russian metadata, simplified synonyms.

### A7. `exporter/goldendict/data_classes.py` → `data_classes_dps.py`
- **Delta:** 7 lines changed upstream
- **Strategy:** Port `HeadwordData` constructor changes. Preserve dual RU+SBS fields, `show_ru_data`/`show_sbs_data` flags, `RpdData`, newline converters.

### A8. `exporter/goldendict/templates/dpd_headword.jinja` → `ru_components/templates/` + `sbs_templates/`
- **Delta:** 4 lines changed upstream
- **Strategy:** Identify which template lines changed, port equivalent changes into `dpd_headword_ru.jinja` and `dpd_headword_sbs.jinja` with appropriate `ru_`/`sbs_` prefixes.

### A9. `exporter/grammar_dict/grammar_dict.py` → `grammar_dict_ru.py`
- **Delta:** 10 lines changed upstream
- **Strategy:** Port changes. Preserve `GrammarDataRu` subclass, `ProgData` with `rupth`, Russian abbreviation replacements, Russian metadata.

### A10. `exporter/kindle/epub/OEBPS/Text/titlepage.xhtml` → `ru_components/epub/`
- **Delta:** 2 lines changed upstream
- **Strategy:** Minimal. Port equivalent change into Russian titlepage, preserving Russian metadata.

### A11. `exporter/kindle/kindle_exporter.py` → `kindle_exporter_ru.py`
- **Delta:** 24 lines changed upstream
- **Strategy:** Port structural changes. Preserve Russian-only script mode, `ru_components/templates/`, `make_ru_meaning_for_ebook`, `render_rpd_xhtml`, `rupth` paths.

### A12. `exporter/tbw/tbw_exporter.py` → `tbw_exporter_ru.py`
- **Delta:** 28 lines changed upstream
- **Strategy:** Port structural changes. Preserve `rupth`, `ru_replace_abbreviations`, `make_ru_meaning_simpl`, FDG-only output.

### A13. `exporter/tpr/tpr_exporter.py` → `tpr_exporter_ru.py`
- **Delta:** 34 lines changed upstream
- **Strategy:** Port structural changes. Preserve `rupth`, `.ru` eager loading, `tpr_headword_ru.jinja`, `root_ru_meaning` in info string, Russian asset naming.

### A14. `exporter/webapp/data_classes.py` → `data_classes_ru.py`
- **Delta:** 10 lines changed upstream
- **Strategy:** Port `HeadwordData` changes. Preserve RU fields, `GrammarData` Russian translations, `RpdData`.

### A15. `exporter/webapp/templates/home.html` → `ru_templates/` + `sbs_templates/`
- **Delta:** 19 lines changed upstream
- **Strategy:** Port layout/structural changes into Russian and SBS template variants, preserving localized bindings.

### A16. `scripts/build/families_to_json.py` → `families_to_json_ru.py`
- **Delta:** 12 lines changed upstream
- **Strategy:** Port changes. Preserve `rupth`, `data_ru_unpack`, `root_ru_meaning`.

### A17. `tools/version.py` → `version_ru.py`
- **Delta:** 2 lines changed upstream
- **Strategy:** Minimal. Port matching change, preserve `version_ru` prefix, `dpd_sbs_release_version` key, Russian metadata.

---

## Group B: Shadow Copies — SBS/DPS (`sbs_copy`/`dps_copy`, PORT)

### B1. `scripts/server/update-dpd.sh` → `update-dpd-sbs.sh`
- **Delta:** 5 lines changed upstream
- **Strategy:** Port structural changes. Preserve `dpd-db-sbs` target, `sasanarakkha/dpd-db-sbs` download, port 8081.

### B2. `scripts/build/db_rebuild_from_tsv.py` → `db_rebuild_from_tsv_dps.py`
- **Delta:** 15 lines changed upstream
- **Strategy:** Port changes. Preserve localized table population, duplicate check, orphaned row handling.

### B3. `db/backup_tsv/backup_dpd_headwords_and_roots.py` → `scripts/backup/backup_dps.py`
- **Delta:** 10 lines changed upstream
- **Strategy:** Port relevant structural changes. Preserve `backup_russian`, `backup_sbs`, `backup_ru_roots`, Russian-empty safety check.

---

## Group C: Tracked Modified Files (PORT, check local divergences)

### C1. `exporter/webapp/data_classes.py`
- **Delta:** 10 lines. Also has `_ru` shadow (A14 above).
- **Strategy:** Check if upstream changes affect the local additions (`self.sbs`, `show_ru_data`, RU/SBS fields, SBS search URL). Port new upstream additions while preserving local fields.

### C2. `exporter/webapp/static/home.js`
- **Delta:** 26 lines added upstream.
- **Strategy:** Check if new upstream code conflicts with the SBS dictionary link (line ~67) and Russian start message block (lines ~77-91). Port new code, preserve local blocks.

### C3. `gui2/pass2_add_view.py`
- **Delta:** 16 lines added upstream.
- **Strategy:** Port new code. Preserve `from tools.fast_api_utils_dps import request_dpd_server`.

### C4. `tools/ai_manager.py`
- **Delta:** 119 lines changed (significant refactor).
- **Strategy:** Since SMD says "no significant localized additions", accept upstream changes. Verify DPS AI tools still import correctly after the refactor.

---

## Group D: Inspired Sources (inspired_only — backport useful improvements)

### D1. `tools/paths.py` → `paths_ru.py`, `paths_dps.py`
- **Delta:** 53 lines changed (IMPORTANT)
- **Strategy:** Read upstream diff. Identify new path constants added to `ProjectPaths`. Add corresponding `ru_`/`dps_` variants to `RuPaths` and `DPSPaths`. Missing paths here cause silent failures in exporters.

### D2. `.github/workflows/draft_release.yml` → `ru_release.yml`, `ru_release_test.yml`
- **Delta:** 33 lines changed.
- **Strategy:** Review upstream workflow changes. Port relevant step updates (artifact names, upload actions, new build steps) into RU release workflows.

### D3. `exporter/goldendict/main.py` → `main_ru.py`, `main_sbs.py`
- **Delta:** 8 lines changed.
- **Strategy:** Review changes. Port structural updates (if any affect the orchestration pattern) into RU and SBS main files.

### D4. `exporter/goldendict/export_epd.py` → `export_epd_sbs.py`
- **Delta:** 2 lines. Minimal — review and port if relevant.

### D5. `exporter/goldendict/export_help.py` → `export_help_ru.py`, `export_help_sbs.py`
- **Delta:** 2 lines. Minimal — review and port if relevant.

### D6. `exporter/goldendict/export_roots.py` → `export_roots_ru.py`, `export_roots_sbs.py`
- **Delta:** 2 lines. Minimal — review and port if relevant.

### D7. `exporter/goldendict/export_variant_spelling.py` → `export_variant_spelling_ru.py`
- **Delta:** 2 lines. Minimal — review and port if relevant.

### D8. `docs/*` → `docs_rus/`
- **Delta:** Newsletters, docs pages, images (cosmetic).
- **Strategy:** No action required this sync. Newsletter images and doc pages are content, not code. Flag for manual translation if needed.

### D9. `mkdocs.yaml` → `mkdocs_ru.yaml`
- **Delta:** Check for new nav entries or plugin changes.
- **Strategy:** Review and port relevant structural changes only.

---

## Execution Order (for Stage 3)

1. **Discussion items first** (D1–D3) — get user approval
2. **Group D1** (`paths.py` → `paths_ru.py`, `paths_dps.py`) — foundational, other files depend on paths
3. **Group A** (Russian shadows) — start with A4 (`family_set_ru.py`, largest delta), then remaining in order
4. **Group B** (SBS/DPS shadows)
5. **Group C** (Tracked modified files)
6. **Group D2–D9** (Remaining inspired sources)
7. **Verification**: `uv run pytest`, `check_shadow_modifications.py`

---

## Summary

| Category | Count | Total Lines Changed |
|---|---|---|
| Discussion flags | 3 | ~274 |
| Russian shadows (PORT) | 17 | ~327 |
| SBS/DPS shadows (PORT) | 3 | ~30 |
| Tracked modified (PORT) | 4 | ~171 |
| Inspired sources | 9 | ~102 |
| **Total items** | **36** | **~904** |

**High-priority items:** A4 (family_set_ru, 134 lines), D1 (paths, 53 lines), C4 (ai_manager, 119 lines)
