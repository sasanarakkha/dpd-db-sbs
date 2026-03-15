# Dynamic Sync Plan

This plan details the manual steps required to merge upstream changes into our localized `sbs-ru` files.
**CRITICAL MAJOR UPSTREAM CHANGE:** Upstream has migrated from raw HTML string formatting to Jinja2 (`.jinja`) templates across all exporters (GoldenDict, Kindle, Grammar Dict, etc.). We must port this migration to all our Russian and SBS shadow copies.

## Part 1: Modified Upstream Files (Direct Integrations)

### 1.1 db/models.py
- **Upstream Change:** Added `from functools import cached_property`, replaced `@property` with `@cached_property` globally. Added `see` column to `Lookup` model with `see_pack`/`see_unpack`.
- **Local Preservation:** Retain all `ru` and `sbs` columns (e.g., `root_ru_meaning`, `data_ru_pack`).
- **Action:** Add `cached_property` to imports. Update local properties to `@cached_property` matching upstream. Add the `see` column and its methods.

### 1.2 exporter/webapp/data_classes.py & SeeData
- **Upstream Change:** Added a new `SeeData` class.
- **Local Preservation:** Keep `ru` and `sbs` logic in `HeadwordData` and `update_fields`.
- **Action:** Add the `SeeData` class from upstream. Check if it needs porting to `data_classes_ru.py` (which is a shadow copy!).

### 1.3 gui2/main.py
- **Upstream Change:** Added `RootsTabView`, `_on_submit_data`, `_on_check_updates`, `_get_current_lemma`. Added elements to `appbar_actions`. Changed `ctrl+F` shortcut logic.
- **Local Preservation:** Keep `DpsView` and `AnalysisView` imports, tabs, and logic.
- **Action:** Integrate upstream features while preserving custom DPS tabs.

### 1.4 tools/ai_manager.py
- **Upstream Change:** Restructured `DEFAULT_MODELS`, added `gemini-1.5-flash`, `gemini-2.5-pro`, various OpenRouter models, and removed OpenAI.
- **Action:** Sync the `DEFAULT_MODELS` and `__init__` logic to match upstream.

### 1.5 Documentation & Gitignore
- **conductor/tech-stack.md:** Update Python to 3.13, add `ty`.
- **conductor/product.md:** Add "Contributors" and "Contributor Onboarding" sections.
- **.gitignore:** Add new ignores (`gui2/data/*.json`, `CLAUDE.md`, `__pycache__/`, `.DS_Store`). **CRITICAL:** Preserve the "DPS / SBS / RU UNIQUE patterns" section at the end.

---

## Part 2: Shadow Copy Sources (Jinja2 Migration & Logic Updates)

The following upstream source files were modified in the latest sync. We must port the relevant logic (especially the Jinja2 rendering migration) to their corresponding shadow copies.

### 2.1 GoldenDict Exporter Migration
- **Source Files Changed:** `export_dpd.py`, `export_epd.py`, `export_help.py`, `export_roots.py`, `export_variant_spelling.py`
- **Shadow Copies to Update:**
  - **RU:** `export_dpd_ru.py`, `export_help_ru.py`, `export_roots_ru.py`, `export_variant_spelling_ru.py`
  - **SBS:** `export_dpd_sbs.py`, `export_epd_sbs.py`, `export_help_sbs.py`, `export_roots_sbs.py`
- **Action:** Update all these Python scripts to use `exporter.jinja2_env` instead of previous string interpolation. 

### 2.2 GoldenDict Templates
- **Source Files Changed:** `exporter/goldendict/templates/*.jinja` (migrated from `.html`)
- **Shadow Copies to Update:** `exporter/goldendict/ru_components/templates/` and `exporter/goldendict/sbs_templates/`
- **Action:** Rename local `.html` shadow templates to `.jinja`. Refactor local syntax inside these templates to valid Jinja2 syntax to match upstream changes.

### 2.3 Kindle Exporter Migration
- **Source File Changed:** `exporter/kindle/kindle_exporter.py`, `exporter/kindle/templates/*.jinja`
- **Shadow Copies to Update:** `kindle_exporter_ru.py`, `exporter/kindle/ru_components/templates/`
- **Action:** Migrate the Russian kindle exporter to Jinja2 and rename/refactor the Russian templates to `.jinja`.

### 2.4 Webapp & Tooling
- **Source File Changed:** `exporter/webapp/main.py`, `exporter/webapp/toolkit.py`, `exporter/webapp/templates/see.html`, `exporter/webapp/templates/see_summary.html`
- **Shadow Copies to Update:** `main_ru.py`, `toolkit_ru.py`, `exporter/webapp/ru_templates/`
- **Action:** Port Webapp routing and templating updates to the Russian shadow copies. Ensure new `see.html` templates are replicated for RU if necessary.

### 2.5 Other Exporters & Scripts
- **Deconstructor:** Port `deconstructor_exporter.py` changes to `deconstructor_exporter_ru.py`.
- **Grammar Dict:** Port `grammar_dict.py` changes to `grammar_dict_ru.py`.
- **TPR Exporter:** Port `tpr_exporter.py` changes to `tpr_exporter_ru.py`.
- **Paths & Utils:** Update `paths_ru.py`, `paths_dps.py`, `utils_sbs.py` to match new variables in `paths.py` and `utils.py`.
- **Scripts:** Update `make_dpd.sh`, `make_ru_dpd.sh`, `generate_components.sh`, and `dps_anki_updater.py` to reflect their upstream Python script counterparts' changes if applicable.
- **Spelling:** Port `tools/spelling.py` changes to `ru_spelling.py`.
