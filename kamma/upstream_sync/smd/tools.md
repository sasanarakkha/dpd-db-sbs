# SMD: TOOLS


**File**: `tools/degree_of_completion_ru.py`
- **Category**: russian_copies
- **Sync Rule**: PORT
- **Local Changes**:
  1. `ru_degree_of_completion` function wraps upstream `degree_of_completion`.
  2. If `i.ru.ru_meaning` exists, it removes the `"gray"` class from the result of the upstream function (making the completion symbol full-color).
  3. Otherwise, it falls back to the standard upstream completion symbol.
- **Watch For**:
  - If upstream changes the completion symbol markup, this regex-based replacement might need updating.

---


**File**: `tools/paths_ru.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Fundamental path redirection logic for RU build outputs.
- **Sync Rule**: inspired_only
- **Triple Shadow**: Both `tools/paths_ru.py` (class `RuPaths`) and `tools/paths_dps.py` (class `DPSPaths`) shadow `tools/paths.py`.
- **Local Changes**:
  1. `RuPaths` class mapping all upstream `ProjectPaths` constants to Russian-prefixed equivalents.
  2. Russian-specific paths: `abbreviations_tsv_path` (help_ru), `sets_ru_path`, `ru_components/templates/`, `fdg_dpd_ebts_js_ru_path`, etc.
  3. `create_dirs` logic filtered to only needed output directories.
- **Watch For**:
  - New upstream path constants are *silently missing* in this shadow file until ported.
  - All localized exporters depend on this file for output locations.

---


**File**: `tools/ru_spelling.py`
- **Category**: russian_copies
- **Sync Rule**: PORT
- **Local Changes**:
  1. `RuSpellChecker` singleton using `SpellChecker(language="ru")`.
  2. Loads custom Russian dictionary from `DPSPaths.ru_user_dict_path`.
  3. Provides `add_to_ru_dictionary` method to append new words to the custom TSV.
- **Watch For**:
  - Requires `pyspellchecker` library.
  - The custom dictionary file must be UTF-8 encoded.

---


**File**: `tools/translit_ru.py`
- **Category**: russian_copies
- **Sync Rule**: PORT
- **Local Changes**:
  1. `is_cyrillic` helper using Unicode range check (`\u0400` - `\u04FF`).
  2. `auto_translit_to_roman` short-circuits if `is_cyrillic(text)` is true.
  3. Transliteration logic preserves Roman Pali, English, and Cyrillic text while converting others to IAST.
- **Watch For**:
  - Used by the webapp search to handle multilingual input.

---


**File**: `tools/version_ru.py`
- **Category**: russian_copies
- **Sync Rule**: PORT
- **Local Changes**:
  1. `make_version` returns an additional `version_ru` string (prefixed with `ru_`).
  2. `update_db_version` uses `dpd_sbs_release_version` key in `DbInfo`.
  3. Metadata fields (email, website, docs, github) point to Russian fork endpoints.
- **Watch For**:
  - This version is displayed in the Russian webapp footer.

---


**File**: `tools/utils_sbs.py`
- **Category**: sbs_copies
- **Sync Rule**: PORT
- **Local Changes**:
  1. Adds `paragraphs_are_similar` utility (used by `db/models.py`).
  2. `RenderedSizes` TypedDict adds `sbs_example` field.
- **Watch For**:
  - Keep structurally aligned with `tools/utils.py`.

---


**File**: `tools/paths_dps.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Fundamental path redirection for DPS/SBS build outputs.
- **Sync Rule**: inspired_only
- **Triple Shadow**: Shadows `tools/paths.py`.
- **Local Changes**:
  1. `DPSPaths` class mapping upstream constants to SBS/DPS output directories.
  2. SBS-specific paths: `sbs_index_path`, `class_index_path`, `ru_user_dict_path`, `anki_csvs_dir`, etc.
  3. Paths for AI suggestion history and batch reports.
- **Watch For**:
  - Massive divergence from `ProjectPaths`; must be updated every time a new path is added upstream.

---


**File**: `tools/fast_api_utils_dps.py`
- **Category**: inspired_by_upstream
- **Shadow of**: `tools/fast_api_utils.py`
- **Divergence Reason**: DPS-specific FastAPI utilities; architectural divergence from upstream.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. `start_dpd_server` launches `main_ru:app` on `127.0.0.1:8080` (GUI internal startup port).
  2. `request_dpd_server` redirects to `http://127.0.0.1:8080/sbs/`.
- **Watch For**:
  - Port split is intentional: `8080` = GUI-initiated internal server; `8081` = standalone `main_ru.py` server. Do not collapse them.
  - `127.0.0.1` is the correct local Mac development address — never replace it with `0.0.0.0` or `localhost`.
  - When upstream `fast_api_utils.py` adds new server helpers or changes the startup API, evaluate whether the DPS equivalent needs a matching `_dps` variant. Do not blindly port — this file is `inspired_only`.

---
