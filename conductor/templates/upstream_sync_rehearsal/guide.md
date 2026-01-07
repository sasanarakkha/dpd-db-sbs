# Upstream Sync Guide (DPS Fork)

## 🚀 How to Start a New Rehearsal

1. **Initialize:** Run the setup script to create the track folder and register it.
   ```bash
   python3 conductor/init_rehearsal.py
   ```

2. **Implement:** Start the agent.
   ```text
   /conductor:implement Upstream Sync Rehearsal
   ```

---

This guide documents the logic and manual steps required to synchronize the DPS fork (`sbs-ru` branch) with the upstream repository (`as_upstream` branch).

## Sync Registry (`dps_sync_registry.json`)

The `dps_sync_registry.json` is the source of truth for managing the relationship between the fork and upstream.

### Categories:
- **`modified_upstream_files`**: Files that exist upstream but have been significantly modified in the fork. These files are **restored from the fork's current state** after an upstream pull to preserve local logic. They require manual merging if upstream changes occur.
- **`ignored_files`**: Paths that should be completely ignored by the sync process (e.g., local data, tracks).
- **`unique_paths`**: Files and folders that exist ONLY in the fork. The sync script should never touch or delete these.
- **`russian_copies` & `sbs_copies`**: Map shadow copies to their upstream sources. Used to track which files need manual logic porting when upstream is updated. The copies should not be deleted by the sync script, unless the corresponding copy has been deleted.

## Core Logic for Preservation

The following logic and files MUST be preserved during any synchronization process.

### 1. Database Schema (`db/models.py`)
- **Deviations:**
    - Adds `SBS`, `Russian`, and `Sinhala` tables.
    - Extensive hybrid properties and methods in `DpdHeadword` and `DpdRoot` to support Russian meanings, SBS examples, and UI button logic (e.g., `needs_sbs_example_button`, `needs_ru_notes`).
    - Configurable link URLs in `SuttaInfo.tbw` using `tools.configger`.
- **Sync Strategy:** Manual merge required. Ensure all custom classes (`SBS`, `Russian`, `Sinhala`) and their relationships are maintained. Carefully merge updates to existing classes.

### 2. Webapp (DPS Customizations)
- **`exporter/webapp/data_classes.py`**: Preserves `show_ru_data` logic and configuration-based toggles.
- **`exporter/webapp/static/app.js` & `home.js`**:
    - Preserves search URL redirection to `/sbs/search_json` when language is English.
    - Preserves Russian localization for the UI (start messages, links).
    - Preserves links to DPS-specific documentation (e.g., Study Tools).
- **Sync Strategy:** Manual merge. Look for `if (language === 'en')` or `if (language === 'ru')` blocks in JS files.

### 3. Desktop GUI (`gui2/`)
- **`gui2/main.py`**:
    - Uses `tools.fast_api_utils_dps`.
    - Includes `DpsView` tab.
- **`gui2/pass2_add_view.py`**:
    - Uses `tools.fast_api_utils_dps`.
    - Preserves custom UI font sizes (17px for text, 15px for hints).
    - Preserves automatic lemma copying to clipboard on save.
- **Sync Strategy:** Manual merge. Ensure `tools.fast_api_utils_dps` is used instead of the upstream version.

### 4. AI & Infrastructure
- **`tools/ai_manager.py`**: Preserves additional providers (OpenAI) and custom model preferences/fallbacks.
- **`.gitignore`**: Preserves exclusions for Russian-specific generated components (kindle, goldendict javascript).
- **`AGENTS.md` / `README.md`**: Preserves fork-specific developer instructions and project context.
- **Conductor Files (`product.md`, `tech-stack.md`, `product-guidelines.md`)**: Preserves the core identity and technical mapping of the DPS fork while allowing for upstream framework/structure updates.
- **Sync Strategy:** Manual merge. Perform a diff to receive framework-level updates from upstream while ensuring DPS-specific descriptions and rules are preserved.

## Logic for Shadow Copies

Shadow copies (`*_ru.py`, `*_sbs.py`, etc.) are fork-specific versions of upstream files. When the original upstream file is updated, the changes might need to be ported to the shadow copy.

### 1. Russian Shadow Copies (`*_ru.py`)
- **Key Characteristics:**
    - Use `RuPaths` (from `tools/paths_ru.py`).
    - Use `Russian` table and relationships.
    - Implement `ru_replace_abbreviations`.
    - Use `rus_degree_of_completion`.
    - Use `make_ru_meaning_html` for rendering meanings in Russian.
    - Often have unique Mako templates located in `ru_templates/` or `ru_components/`.
- **Merge Strategy:** Compare the updated original file with the shadow copy. Port functional improvements or bug fixes from the original to the shadow, while ensuring all `ru_` specific imports and logic blocks remain intact.

### 2. SBS/DPS Shadow Copies (`*_sbs.py`, `*_dps.py`)
- **Key Characteristics:**
    - Use `DPSPaths` (from `tools/paths_dps.py`).
    - Use `tools/utils_sbs.py` for specialized rendering and utility functions.
    - Often include `joinedload` on `sbs` relationship to optimize performance.
    - Reference specialized Mako templates in `sbs_templates/`.
- **Merge Strategy:** Similar to Russian copies. Port upstream logic changes while preserving `sbs` table integration, `DPSPaths`, and SBS-specific template paths.

### 3. Path Management
- **Always Verify:** After merging, check that the shadow copy is still importing its corresponding path utility (`RuPaths` or `DPSPaths`) instead of the standard `ProjectPaths`).
- **Path Parity:** If significant features or new path logic (e.g., new directory constants or helper methods) are added to the upstream `tools/paths.py`, they MUST be ported to `tools/paths_ru.py` and `tools/paths_dps.py` if they are relevant for the localized components.

## Documentation Parity

Maintaining parity between English (`docs/`) and Russian (`docs_rus/`) documentation is critical for the DPS fork's user experience.

### 1. Identify New Documentation
- **Check for new files:** Compare the file list of `docs/` with `docs_rus/`.
- **Action:** For every new `.md` file in `docs/`, create a corresponding file in `docs_rus/`. If immediate translation is not possible, copy the English content and add a "TRANSLATION PENDING" banner at the top.

### 2. Identify Updated Documentation
- **Check for changes:** For files that exist in both directories, check if the upstream English version has been updated significantly.
- **Action:** Port the updates to the Russian version. Use AI translation if necessary, but always verify context.

### 3. Handle Unique Documentation
- **Preserve local-only docs:** Files like `docs_rus/dpd_rus.md` are unique to the fork. Ensure they are not overwritten by any automated sync logic.

### 4. MkDocs Configuration Parity
- **`mkdocs.yaml` vs `mkdocs_ru.yaml`**: 
    - When new pages are added to `mkdocs.yaml` (original), they MUST be added to the Russian navigation structure in `mkdocs_ru.yaml`.
    - Ensure `mkdocs_ru.yaml` continues to use the Russian theme/language settings.

### 5. Automated Indexing
- Run `python3 scripts/rus_exporter/docs_add_indexes.py` after updating documentation to ensure navigation indexes and links are correctly generated for the Russian site.

## Manual Sync Checklist

Follow these steps when performing an upstream sync:

### Phase 1: Automated Pull
1. [ ] Run `bash scripts/cl_dps/dpd-sync-folders`.
2. [ ] Choose **Option 2 (Selective Sync)**.
3. [ ] Verify that `sbs-ru` is updated and modified files listed in the registry are preserved.

### Phase 2: Manual Porting (Reasoning Phase)
4. [ ] **`modified_upstream_files`**: For each file, compare `sbs-ru` version against `as_upstream`. If upstream has new features or bug fixes, manually integrate them into the fork's version.
5. [ ] **`db/models.py`**: Pay special attention to core schema changes.
6. [ ] **Shadow Copies**: For each entry in `russian_copies` and `sbs_copies`, check if their **source (the 'value' in the registry)** has changed significantly compared to the **shadow copy (the 'key' in the registry)**. If so, port those logic changes to the shadow copy.
7. [ ] **Documentation Parity**:
    - [ ] List all files in `docs/` that don't have a counterpart in `docs_rus/`.
    - [ ] Create missing files in `docs_rus/` (at least as placeholders).
    - [ ] Update `mkdocs_ru.yaml` navigation to match `mkdocs.yaml`.
    - [ ] Run `python3 scripts/rus_exporter/docs_add_indexes.py`.
8. [ ] **Deleted Upstream Files**:
    - Iterate through `folders_to_check` in the registry.
    - Identify files present in `sbs-ru` but missing in `as_upstream`.
    - Filter out files already listed in `unique_paths` or `ignored_files`.
    - For the remaining "orphaned" files:
        - **Grep** the codebase to see if they are imported or used by `*_ru.py`, `*_sbs.py`, or `gui2/dps_*`.
        - **If used:** You must either refactor your local code to stop using them OR add them to `unique_paths` to preserve them.
        - **If unused:** Ensure they are deleted to keep the fork clean.
9. [ ] **UI Scaling**: Verify `gui2/font_scaling_helper.py` was executed correctly (it is part of the sync script).
10. [ ] **Verification Tests**:
    - Run `uv run pytest tests/test_dps_imports.py` to verify that all critical DPS modules are intact and dependencies are met.
    - Run `uv run pytest tests/test_dps_logic.py` to verify that key family generation and lookup logic is preserved.
    - Run `uv run pytest tests/test_dps_exporters_functional.py` to verify the control flow of critical exporters and build scripts.
    - Run `uv run pytest tests/test_dps_docs_parity.py` to verify that `docs/` and `docs_rus/` are perfectly synced (except for `dpd_rus.md`).
11. [ ] **Commit Changes**: Once manual merges are complete, perform a final commit with a descriptive message (e.g., `sync: manual merge of upstream updates` with the current date, same as done by the sync script).
12. [ ] **Update Registry**: If new shadow copies were created during the process, add them to `dps_sync_registry.json`.