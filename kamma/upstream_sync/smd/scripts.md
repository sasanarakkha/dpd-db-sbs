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


**File**: `scripts/backup/backup_dps.py`
- **Category**: dps_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. New script: `backup_russian`, `backup_sbs`, `backup_ta`, and `backup_ru_roots` functions.
  2. Writes to `russian.tsv`, `sbs.tsv`, `tamil.tsv`, and `ru_roots.tsv` in the backup folder.
  3. Aborts if the `Russian` table is empty (safety check); aborts if `Tamil` table is empty (safety check).
  4. Tamil backup follows the same TSV structure as Russian and SBS (header row + data rows).
  5. Does not mirror upstream `split_tsv_file()` chunking; DPS localized backup TSVs are small and are intentionally kept as single files.
- **Watch For**:
  - No upstream equivalent. This is critical for data persistence in the fork.
  - Tamil table will be empty until AI meaning generation is run; empty-check prevents data loss.
  - Do not port upstream chunk-size/header behavior from `split_tsv_file()` unless DPS backup TSVs become large enough to require splitting.

---


**File**: `scripts/build/db_rebuild_from_tsv_dps.py`
- **Category**: dps_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. New script: populates localized tables from TSV.
  2. Duplicate check on IDs before import (Russian, SBS, Tamil).
  3. Orphaned row check: verifies that all Russian/SBS/Tamil IDs exist in the main `DpdHeadword` table.
  4. Tamil rebuild helper `make_table_data_ta()` mirrors Russian/SBS pattern: reads TSV, zips columns, filters empty keys, instantiates Tamil rows.
- **Watch For**:
  - SBS missing rows prompt for removal; Russian and Tamil missing rows are removed silently.
  - Tamil TSV will be empty until after AI meaning generation runs and data is backed up.

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


**File**: `scripts/server/update-dpd-sbs.sh`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Target directory `dpd-db-sbs`.
  2. Downloads DB from `sasanarakkha/dpd-db-sbs`.
  3. Restarts `main_ru:app` on port 8081.
- **Watch For**:
  - Hardcoded port 8081 must match server firewall settings.

---
