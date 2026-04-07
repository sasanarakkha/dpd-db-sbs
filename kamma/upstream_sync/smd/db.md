# SMD: DB

**File**: `db/models.py`
- **Category**: modified_upstream
- **Sync Rule**: DISCUSS
- **Why DISCUSS**: Adds three entire tables (`SBS`, `Russian`, `Sinhala`) plus relationships (`.sbs`, `.ru`) on `DpdHeadword` and extra columns (`root_ru_meaning`, `sanskrit_root_ru_meaning`) on `DpdRoot`. Blind porting would silently delete all localized schema.
- **Local Changes**:
  1. `SBS` table (~30 columns) at line ~1655: chant data, class mapping, SBS-specific indices and hybrid properties (`sbs_index`, `sbs_chant_link_1/2`, `sbs_class_link`).
  2. `Russian` table (~5 columns) at line ~1865 with `ru_` prefixed fields.
  3. `Sinhala` table at line ~1879.
  4. `.sbs` and `.ru` relationships on `DpdHeadword` (lines ~959, ~962).
  5. `root_ru_meaning` and `sanskrit_root_ru_meaning` columns on `DpdRoot` (lines ~110-111) and `FamilyRoot` (line ~188).
  6. `data_ru` JSON pack/unpack helpers on family tables.
  7. Import of `sbs_table_functions.SBS_table_tools` and `paragraphs_are_similar` (line ~29).
- **Watch For**:
  - New upstream columns/relationships on `DpdHeadword` must not overwrite SBS/Russian additions — manually merge, never auto-replace.
  - Upstream renames of base columns require matching updates in SBS hybrid properties that reference them.
  - Any upstream change to `DpdRoot` must preserve `root_ru_meaning`/`sanskrit_root_ru_meaning`.
  - `paragraphs_are_similar` import from `tools.sbs_table_functions` is DPS-specific — do not remove.

---


**File**: `db/families/family_compound_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Writes `html_ru` and `data_ru` columns on `FamilyCompound` model in addition to upstream `html` column.
  2. Uses `RuPaths` from `tools/paths_ru.py` instead of `ProjectPaths`.
- **Watch For**:
  - New upstream columns written to `FamilyCompound` must have corresponding `_ru` variants added here.
  - Upstream logic refactors (HTML generation, JSON data format) must be mirrored exactly before adding RU layer.

---


**File**: `db/families/family_idiom_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports `ru_degree_of_completion`, `make_short_ru_meaning`, `ru_replace_abbreviations` from Russian utils.
  2. Adds `joinedload(DpdHeadword.ru)` to DB query to eager-load Russian data.
  3. Writes `html_ru` and `data_ru` columns on `FamilyIdiom` instead of upstream's `html`/`data`.
  4. DB update is in-place (lookup + assign) rather than upstream's delete-all / bulk-insert approach.
  5. Upstream's `sync_idiom_numbers_with_family_compound()` function is entirely absent — Russian fork does not auto-sync idiom numbering.
- **Watch For**:
  - Upstream idiom auto-sync logic is removed; if upstream changes the numbering scheme, Russian fork won't inherit it.
  - Update-in-place vs. delete-insert may diverge on new idiom entries — verify counts after sync.

---


**File**: `db/families/family_root_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports `ru_degree_of_completion`, `make_short_ru_meaning`, `ru_replace_abbreviations` from Russian utils.
  2. Adds `joinedload(DpdHeadword.ru)` to DB query.
  3. Writes `root_ru_meaning`, `html_ru`, `data_ru` columns on `FamilyRoot`; DB update is in-place.
  4. Custom `make_root_header_ru()` generates Russian-language header HTML.
  5. Three upstream functions absent: `update_lookup_table()`, `generate_root_info_html()`, `generate_root_matrix()`.
  6. Anki deck reduced from two (Family Root + Root Matrix) to one (Family Root RU only).
- **Watch For**:
  - Lookup table synchronization is entirely removed — upstream lookup updates do not flow to the Russian fork.
  - If upstream changes `FamilyRoot` HTML structure or adds new columns, `html_ru` generation must be updated separately.

---


**File**: `db/families/family_set_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports `ru_degree_of_completion`, `make_short_ru_meaning`, `ru_replace_abbreviations`, `populate_set_ru_and_check_errors`.
  2. Adds `joinedload(DpdHeadword.ru)` to DB query.
  3. Writes `html_ru`, `set_ru`, `data_ru` columns on `FamilySet`; DB update is in-place.
  4. Calls `populate_set_ru_and_check_errors()` to populate Russian set name translations.
- **Watch For**:
  - Upstream uses delete-all / bulk-insert; fork uses in-place update — verify record counts after upstream refactors.
  - `set_ru` field requires Russian translations to exist; missing translations cause empty columns silently.

---


**File**: `db/families/family_word_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports `ru_degree_of_completion`, `make_short_ru_meaning`, `ru_replace_abbreviations`.
  2. Adds `joinedload(DpdHeadword.ru)` to DB query.
  3. Writes `html_ru` and `data_ru` columns on `FamilyWord`; DB update is in-place.
  4. Anki data tuple includes Russian data fields not present in upstream.
- **Watch For**:
  - In-place update vs. upstream delete-insert — check for orphaned entries after upstream structural changes.
  - Anki tuple structure must stay in sync if upstream changes the anki data format.

---


**File**: `db/lookup/help_abbrev_add_to_lookup_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports and stores `RuPaths` alongside `ProjectPaths`.
  2. Reads help and abbreviations from Russian-specific TSV files via `RuPaths` (different file paths and column indices than upstream).
  3. Functions renamed with `_ru` suffix: `add_help_ru()`, `add_abbreviations_ru()`.
  4. Uses `read_tsv_as_dict_with_different_key()` with hardcoded column indices (2 for help, 5 for abbrev) instead of upstream's `read_tsv_as_dict()`.
  5. Stores `ru_meaning` from TSV into the Lookup model's Russian meaning column.
- **Watch For**:
  - Hardcoded column indices will break silently if Russian TSV format changes.
  - `help_ru_pack()` and `abbrev_pack()` methods must exist on the `Lookup` model.

---
