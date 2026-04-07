# SMD: SCRIPTS

**File**: `scripts/bash/generate_components.sh`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Language mismatch: Bash vs Python; localized build orchestration.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. Converted from `generate_components.py` (upstream) to a Bash script.
  2. Sequential execution of upstream builders followed by Russian shadow builders: `family_root_ru.py`, `family_word_ru.py`, `family_compound_ru.py`, `family_set_ru_update.py`, `family_set_ru.py`, `family_idiom_ru.py`.
  3. Appends `help_abbrev_add_to_lookup_ru.py` after the upstream help script.
  4. Includes explicit `uv run` calls for all Python scripts.
  5. Error handling: `set -e` and explicit dealbreakers status check.
- **Watch For**:
  - Upstream structural changes to builder order must be ported.
  - Ensure all `_ru.py` scripts are executed in the correct dependency order (after their English counterparts).

---


**File**: `scripts/bash/make_dpd.sh`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Language mismatch: Bash vs Python; localized DPD build logic.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. Interactive config selector: (1) DPD-SBS server, (2) DPD-SBS-RU local.
  2. Runs `generate_components.sh` (the localized version).
  3. Exporter sequence: uses `main_sbs.py` and `tpr_exporter_ru.py`.
  4. Automation: moves mdict files and copies server artifacts if option 1 is selected.
  5. Post-build cleanup: `git checkout --` for files modified during the build (e.g., `pyproject.toml`).
- **Watch For**:
  - The hardcoded branch `sbs-ru` checkout at the beginning.
  - Ensure `config_github_local_dpd_sbs.py` is called at the end to reset settings.

---


**File**: `scripts/bash/make_ru_dpd.sh`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Language mismatch: Bash vs Python; RU-specific build entry point.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. Interactive config selector: (1) RUS-DPD server, (2) RUS-DPD local.
  2. Conditional component generation: if skipped, it runs `families_to_json_ru.py` directly.
  3. Exporter sequence: uses `grammar_dict_ru.py`, `main_ru.py`, `deconstructor_exporter_ru.py`, `kindle_exporter_ru.py`, `tbw_exporter_ru.py`, `tpr_exporter_ru.py`.
  4. Moves Russian mdict files and tarballs the DB.
- **Watch For**:
  - This script is focused on the Russian-only export profile.
  - Coordinate with `ru_zip_goldendict_mdict.py`.

---


**File**: `scripts/build/families_to_json_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `GlobalVars` adds `rupth: RuPaths` and sets `self.paths = rupth`.
  2. All `export_family_*` methods call `data_ru_unpack` instead of `data_unpack`.
  3. `export_family_root` uses `root_ru_meaning` instead of `root_meaning`.
- **Watch For**:
  - This script populates the `.js` files in `exporter/goldendict/ru_components/javascript/`.
  - JSON schema must match the expectations of the `ru_` template loader.

---


**File**: `scripts/ru_exporter/config_github_release_dpd_rus.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Sets `show_ru_data="yes"` and `show_sbs_data="no"`.
  2. Disables most rebuild steps (assumes pre-built data).
  3. Sets `link_url="https://find.dhamma.gift/bw/"`.
  4. Disables grammar, deconstructor, variants, and ebook exporters (keeps only DPD, TBW, and TPR).
- **Watch For**:
  - This is a "light" release profile for Russian data updates.

---


**File**: `scripts/ru_exporter/ru_config_github_release.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Full release profile: enables all rebuild steps (`db_rebuild`, `inflections`, etc.).
  2. `show_ru_data="no"` and `show_sbs_data="no"` (standard upstream-like export).
  3. Enables all exporters except `make_txt` and `make_changelog`.
- **Watch For**:
  - Used for building the base Russian GoldenDict artifacts.

---


**File**: `scripts/ru_exporter/ru_zip_goldendict_mdict.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Packages `ru-dpd`, `ru-dpd-grammar`, `ru-dpd-deconstructor`, and `dpd-variants`.
  2. Uses `RuPaths` for all ZIP and MDict path resolution.
  3. MDict list includes Russian-prefixed filenames (e.g., `ru-dpd-grammar-mdict.mdx`).
- **Watch For**:
  - Filename consistency with `kindle_exporter_ru.py` outputs.

---


**File**: `scripts/ru_exporter/zip_dpd_rus.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Packages the *upstream* GoldenDict dir into `dpd+rus-goldendict.zip` and `dpd+rus-mdict.zip`.
  2. Flattened ZIP structure: writes files directly to the archive root (not inside a subfolder).
  3. Uses `ProjectPaths`.
- **Watch For**:
  - This script is for the "combined" export where Russian data is injected into the standard DPD output.

---


**File**: `scripts/ru_exporter/docs_add_indexes.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Uses `RuPaths` and reads `mk_docs_yaml`.
  2. Generates indexes for `docs_rus/`.
- **Watch For**:
  - Relative path logic must point correctly into the `docs_rus/` subdirectory.

---


**File**: `scripts/backup/backup_dps.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. New script: `backup_russian`, `backup_sbs`, and `backup_ru_roots` functions.
  2. Writes to `russian.tsv`, `sbs.tsv`, and `ru_roots.tsv` in the backup folder.
  3. Aborts if the `Russian` table is empty (safety check).
- **Watch For**:
  - No upstream equivalent. This is critical for data persistence in the fork.

---


**File**: `scripts/build/db_rebuild_from_tsv_dps.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. New script: populates localized tables from TSV.
  2. Duplicate check on IDs before import.
  3. Orphaned row check: verifies that all Russian/SBS IDs exist in the main `DpdHeadword` table.
- **Watch For**:
  - SBS missing rows prompt for removal; Russian missing rows are removed silently.

---


**File**: `scripts/fix/character_replacer_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. New script: configurable `table` ("SBS", "Russian", or default) and `column`.
  2. Eagerly loads both relationships for targeted replacement.
- **Watch For**:
  - Manually configure `table` and `column` variables at the top before running.

---


**File**: `scripts/ru_exporter/config_github_release_dpd_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Sets `show_sbs_data="yes"` and `show_ru_data="no"`.
  2. Disables grammar, deconstructor, variants, and ebook exporters (similar to the Russian light profile).
- **Watch For**:
  - Used for targeted SBS data updates.

---


**File**: `scripts/ru_exporter/zip_dpd_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Packages the *upstream* GoldenDict dir into `dpd+sbs-goldendict.zip` and `dpd+sbs-mdict.zip`.
  2. Flattened structure (same as `zip_dpd_rus.py`).
- **Watch For**:
  - Ensure it packages the state *after* an SBS export.

---


**File**: `scripts/server/update-dpd-sbs.sh`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Target directory `dpd-db-sbs`.
  2. Downloads DB from `sasanarakkha/dpd-db-sbs`.
  3. Restarts `main_dps:app` on port 8081.
- **Watch For**:
  - Hardcoded port 8081 must match server firewall settings.

---


**File**: `scripts/export/dps_anki_updater.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Eagerly loads `.ru` and `.sbs` relationships.
  2. `update_note_values` populates ~40 Anki fields covering both Russian and SBS data.
  3. `ru_meaning` logic: falls back to AI translation (`пер ИИ:`) if manual translation is missing.
  4. `deck_selector` filters for SBS-relevant content and places it in the "Pali" deck.
- **Watch For**:
  - Requires `anki` library.
  - Field names must match the "Pāli" note type in the target Anki collection.

---
