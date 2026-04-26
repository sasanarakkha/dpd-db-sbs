# SMD: EXPORTER

**File**: `exporter/webapp/data_classes.py`
- **Category**: modified_upstream
- **Sync Rule**: PORT
- **Local Changes**:
  1. `HeadwordData.__init__` includes `self.sbs` (line ~18) and `self.show_ru_data` flag (line ~26) plus `ru_meaning`, `ru_meaning_lit`, `ru_notes`, `sbs_meaning`, `sbs_notes` fields (lines ~46-50).
  2. SBS search URL `/sbs/search_json` referenced in rendered HTML (line ~164).
- **Watch For**:
  - New upstream data class fields must be ported to this file AND to `exporter/webapp/data_classes_ru.py` (its shadow).
  - If upstream changes `HeadwordData` constructor signature, update both files.

---


**File**: `exporter/webapp/static/app.js`
- **Category**: modified_upstream
- **Sync Rule**: PORT
- **Local Changes**:
  1. SBS dictionary link to `sasanarakkha.github.io/study-tools/dict/sbs-pali-dictionary` in UI (line ~380).
  2. SBS search endpoint references.
- **Watch For**:
  - Upstream JS refactors may move SBS link anchors — verify after sync that SBS link is still rendered.

---


**File**: `exporter/webapp/static/home.js`
- **Category**: modified_upstream
- **Sync Rule**: PORT
- **Local Changes**:
  1. SBS dictionary link to `sasanarakkha.github.io/study-tools/dict/sbs-pali-dictionary` in English start message (line ~67).
  2. Russian (`language === "ru"`) start message block (lines ~77-91): fully localized RU text with links to `devamitta.github.io/dpd.rus/webapp/` and `devamitta.github.io/dpd.rus/`.
- **Watch For**:
  - Keep SBS link in sync with the one in `app.js` — they reference the same URL.
  - If upstream adds new language branches to the start-message block, ensure the RU branch remains syntactically valid alongside them.

---


**File**: `exporter/deconstructor/deconstructor_exporter_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `DeconstructorDataRu` subclass overrides `_generate_header` to use `deconstructor_header_ru.jinja` and applies "deconstructor" CSS style via `CSSManager`.
  2. `ProgData` class replaces `GlobalVars`, adding `rupth: RuPaths` and storing both `pth` and `rupth`.
  3. `make_deconstructor_dict_data` uses `jinja_env_body` from `exporter/goldendict/ru_components/templates` and renders `deconstructor_ru.jinja`.
  4. Synonyms list logic simplified: removes Sinhala, Devanagari, and Thai unpacks (keeps only Roman and speech marks).
  5. `prepare_and_export_to_gd_mdict` uses Russian strings for `bookname`, `author`, `description`, and `website` (pointing to `devamitta.github.io/dpd.rus/`).
  6. Output dictionary names changed to `ru-dpd-deconstructor` and `ru-dpd-deconstructor2`.
- **Watch For**:
  - Mirror any changes to `DeconstructorData` base class in the `DeconstructorDataRu` override.
  - Template paths are redirected to `ru_components/templates/`.
  - Removal of non-Roman synonyms is intentional for the Russian fork.

---


**File**: `exporter/goldendict/ru_components/javascript/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. JavaScript components for Russian GoldenDict export; mirrors upstream `templates/javascript/`.
  2. All GoldenDict JS object names use `rudata_` prefix (e.g., `rudata_family_compound`) to avoid namespace collisions.
  3. Loader classes and global variables prefixed with `ru_`.
- **Watch For**:
  - Upstream JS logic changes must be mirrored with the `ru_` prefix preserved.
  - Coordinate with `scripts/build/families_to_json_ru.py` which generates these files.

---


**File**: `exporter/goldendict/ru_components/templates/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Triple Shadow**: This directory, `exporter/goldendict/sbs_templates/`, and upstream `exporter/goldendict/templates/` are all related.
- **Local Changes**:
  1. All HTML/Jinja2 templates use `ru_` prefixed IDs, CSS classes, and JS calls (e.g., `ru_load_js()`).
  2. Specific templates added: `dpd_headword_ru.jinja`, `root_headword_ru.jinja`, `help_abbrev_ru.jinja`, `help_help_ru.jinja`, `deconstructor_ru.jinja`.
- **Watch For**:
  - Structural changes in upstream templates must be ported while meticulously preserving the `ru_` prefixes.
  - Missing templates in this directory will cause exporter failures.

---


**File**: `exporter/goldendict/export_dpd_ru.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Significant divergence in data structures and RU output logic.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. `DpdHeadwordDbParts` includes `ru: Russian` model; queries filter for `Russian.id.isnot(None)`.
  2. `render_pali_word_dpd_html` uses `data_classes_dps.HeadwordData` and renders via `dpd_headword_ru.jinja`.
  3. Size tracking: `size_dict["dpd_summary"]` records `data.ru_meaning` length instead of English meaning.
  4. Synonyms include Russian set names via `tools_for_ru_exporter.read_set_ru_from_tsv()`.
  5. `generate_dpd_html` uses `rupth: RuPaths` and `joinedload(DpdHeadword.ru)`.
- **Watch For**:
  - The Russian filter means only translated words are exported.
  - Synonyms logic includes a manual Russian set lookup.

---


**File**: `exporter/goldendict/export_help_ru.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Localized help export with RU-specific content structure.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. `Abbreviation` and `Help` data classes add `ru_abbrev`, `ru_help`, and `ru_meaning` fields.
  2. `generate_help_html` uses `rupth: RuPaths` and loads templates from `ru_components/templates/`.
  3. `add_abbrev_html` and `add_help_html` use `ru_abbrev` or `ru_help` as the GoldenDict dictionary key.
  4. `add_bibliography` and `add_thanks` use `rupth` paths but remain structurally similar to upstream.
- **Watch For**:
  - Dictionary keys are in Russian (e.g., Russian abbreviations) to allow lookup from Russian text.
  - Template names are suffixed with `_ru.jinja`.

---


**File**: `exporter/goldendict/export_roots_ru.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: RU-specific data injection makes mechanical parity impractical.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. `generate_root_html` signature adds `rupth: RuPaths`.
  2. Uses `data_classes_dps.RootsData` and `root_headword_ru.jinja` template.
  3. `size_dict["root_definition"]` tracks the full `final_html` length.
- **Watch For**:
  - `RootsData` in `data_classes_dps.py` contains the Russian-specific fields (`ru_root_info`, `ru_root_matrix`).

---


**File**: `exporter/goldendict/export_variant_spelling_ru.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: RU output logic diverges from upstream structure.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. `generate_variant_spelling_html` uses `rupth: RuPaths`.
  2. `generate_see_data_list` logic is entirely removed (merged into other types or omitted).
  3. `generate_variant_data_list` and `generate_spelling_data_list` use `_ru.jinja` templates.
  4. Templates use `main` or `correction` variables directly rather than a complex `data` object.
- **Watch For**:
  - Omission of `see_dict` processing compared to upstream.
  - Direct template variable passing instead of `data` object wrapping.

---


**File**: `exporter/goldendict/main_ru.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: RU-specific dictionary entry point with different build orchestration.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. Imports from Russian variants of exporters (e.g., `exporter.goldendict.export_dpd_ru`).
  2. `GlobalVars` adds `rupth: RuPaths` and sets `self.paths = self.rupth`.
  3. `prepare_export_to_goldendict_mdict` uses Russian dictionary metadata (bookname, author, website) and sets `target_lang="ru"`.
  4. JS paths point to `ru_components/javascript/`.
  5. `dict_name` set to `ru-dpd`.
- **Watch For**:
  - Ensure all `generate_*_html` calls in `main()` use the Russian versions and pass `rupth`.
  - Check that `export_rpd` is used instead of `export_epd`.

---


**File**: `exporter/goldendict/data_classes_dps.py`
- **Category**: russian_copy, sbs_copy, tamil_copy
- **Sync Rule**: PORT
- **Triple Shadow Note**: This file serves russian_copies, sbs_copies, AND tamil_copies.
- **Local Changes**:
  1. `HeadwordData.__init__` accepts `ru: Russian | None`, `sbs: SBS | None`, `ta: Tamil | None`, `show_grammar`, `show_sbs_data`, `show_ru_data`, and `show_ta_data` parameters.
  2. Russian fields populated: `ru_pos`, `ru_plus_case`, `ru_meaning`, `ru_summary`, `ru_complete`, `ru_grammar`, `ru_base`, `ru_phonetic`, `ru_inflections_html`.
  3. SBS fields populated: `sbs_meaning`, `sbs_notes`, `sbs_index`, `sbs_class`, and many `needs_*_example` flags.
  4. Tamil: `self.ta` holds the `Tamil` ORM object; `show_ta_data` flag controls rendering.
  5. `_convert_newlines_ru` replaces `\n, ` with `<br>` in Russian notes.
  6. `_convert_newlines_sbs` handles newline conversion for ~10 SBS string fields.
  7. `RpdData` subclass for Russian EPD entries; `TpdData` subclass for Tamil EPD entries (reserved for future `export_tpd.py`).
- **Watch For**:
  - Upstream changes to `HeadwordData` constructor or methods must be meticulously merged to preserve ALL three data layers (RU, SBS, Tamil).
  - This file is the primary bridge between the DB models and the templates for all localized forks.

---


**File**: `exporter/grammar_dict/grammar_dict_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `GrammarDataRu` subclass overrides `_process_grammar` to translate POS and components using `ru_replace_abbreviations`.
  2. `ProgData` class adds `rupth: RuPaths`.
  3. `generate_html_from_lookup` preloads Russian abbreviations and performs string replacements on the rendered HTML (e.g., replacing "of" with "для").
  4. `prepare_gd_mdict_and_export` uses Russian metadata and sets `target_lang="ru"`.
  5. `dict_name` set to `ru-dpd-grammar`.
- **Watch For**:
  - Manual string replacements in `generate_html_from_lookup` are brittle; verify if upstream template changes.
  - Ensure Russian abbreviation table contains all needed grammar terms.

---


**File**: `exporter/kindle/kindle_exporter_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `render_dpd_xhtml` signature changed to accept `pth` and `rupth`; `script_attr` logic removed (Russian fork uses Roman script only).
  2. Loads templates from `ru_components/templates/`.
  3. `render_ebook_entry` builds a Russian summary using `make_ru_meaning_for_ebook`, `ru_replace_abbreviations`, and `ru_degree_of_completion`.
  4. `render_grammar_templ` and `render_example_templ` use `_ru.jinja` templates.
  5. `render_rpd_xhtml` (replacing upstream's `render_epd_xhtml`) uses the Russian alphabet and `Lookup.rpd`.
  6. Output paths resolve via `rupth` (e.g., `ru-dpd-kindle.epub`).
- **Watch For**:
  - Upstream `KindleData` class is not used; instead, fields are passed directly to templates.
  - The entire EBTS text set logic is preserved but applied to Russian outputs.

---


**File**: `exporter/kindle/ru_components/cover/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Russian-language cover image for Kindle/EPUB.
  2. Replaces upstream metadata attributes with Russian definitions.
- **Watch For**:
  - Standard Kindle cover dimensions must be maintained if updated.

---


**File**: `exporter/kindle/ru_components/epub/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Russian-language EPUB structural files (OEBPS/content.opf, titlepage.xhtml).
  2. Metadata (title, creator, language="ru") set to Russian fork values.
- **Watch For**:
  - Navigation entries in `content.opf` must match the generated letter files.

---


**File**: `exporter/kindle/ru_components/templates/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Full set of Russian XHTML templates for ebook export: `ebook_ru_entry.jinja`, `ebook_ru_grammar.jinja`, `ebook_ru_example.jinja`, `ebook_ru_rpd_letter.jinja`, etc.
  2. Binds Russian localized context variables replacing upstream english variables.
- **Watch For**:
  - Template variables must match the direct dictionary passing in `kindle_exporter_ru.py`.

---


**File**: `exporter/tbw/tbw_exporter_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `ProgData` class adds `rupth: RuPaths`.
  2. `generate_dpd_ebt_dict` uses `ru_replace_abbreviations` for POS and `make_ru_meaning_simpl` for the definition.
  3. `save_js_files_for_tbw` logic removed; only `save_js_files_for_fdg` remains, outputting to `fdg_dpd_ebts_js_ru_path`.
  4. Repository targets changed from `TBW2` to `FDG` only.
- **Watch For**:
  - Verify that the `FDG` repo path in `RuPaths` is correct.
  - Definition format is "simplified" for TBW usage.

---


**File**: `exporter/tpr/tpr_exporter_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `GlobalVars` adds `rupth: RuPaths`.
  2. `make_dpd_db` eagerly loads `.ru` relationship.
  3. `generate_tpr_data` uses `tpr_headword_ru.jinja` template.
  4. Roots logic appends `r.root_ru_meaning` to the info string.
  5. `copy_zip_to_tpr_downloads` uses `rupth.tpr_with_rus_path` and names the asset "DPD with Russian".
- **Watch For**:
  - The TPR SQL format is rigid; ensure the Russian additions don't break the importer.

---


**File**: `exporter/webapp/data_classes_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `HeadwordData.__init__` populates `ru_meaning`, `ru_complete`, `ru_grammar`, `ru_pos`, `ru_plus_case`, `ru_root_base`, `ru_phonetic`, and `inflections_html_ru`.
  2. `GrammarData` translates headword, POS, and components to Russian.
  3. `RpdData` class added for Russian EPD lookups.
- **Watch For**:
  - Shared with the webapp `toolkit_ru.py`.
  - Upstream `HeadwordData` additions must be ported here.

---


**File**: `exporter/webapp/main_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Routes updated: `@app.get("/")` maps to `home_page_ru`, and `/sbs` is added for the English/SBS view.
  2. `templates_ru` and `templates_sbs` initialized separately.
  3. `db_search_json_ru` calls `make_dpd_html_ru`.
  4. `db_search_gd_ru` returns Russian HTML for GoldenDict API.
  5. Application entry point changed to `main_ru:app`.
- **Watch For**:
  - This file serves as the main entry point for the Russian webapp (port 8081).
  - It maintains a dual-mode (RU at root, SBS at `/sbs`).

---


**File**: `exporter/webapp/preloads_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `make_headwords_clean_set_ru` filters `Lookup` entries to only include those with Russian EPD data (`Lookup.rpd != ""`).
  2. Replaces upstream load routines to utilize localized subsets of database values.
- **Watch For**:
  - Performance optimization via `defer()` is preserved.

---


**File**: `exporter/webapp/toolkit_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `make_dpd_html_ru` accepts `rupth: RuPaths`.
  2. Eagerly loads `.ru` for headword results.
  3. Renders using `templates_ru` and maps `Lookup.rpd` to `RpdData`.
  4. "No results found" messages translated to Russian.
- **Watch For**:
  - Ensure all webapp templates exist in `ru_templates/`.

---


**File**: `exporter/webapp/ru_templates/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Webapp Jinja2 templates with Russian bindings.
  2. `home.html` and `home_simple.html` translated.
- **Watch For**:
  - Complex merge of upstream layout and RU data fields.

---


**File**: `exporter/goldendict/sbs_templates/`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Triple Shadow**: See `exporter/goldendict/ru_components/templates/` — same pattern, SBS variant.
- **Local Changes**:
  1. All HTML/Jinja2 templates use `sbs_` prefixed IDs and CSS classes.
  2. Specific templates added: `dpd_headword_sbs.jinja`, `root_headword_sbs.jinja`, `epd_sbs.jinja`, `help_abbrev_sbs.jinja`, `help_help_sbs.jinja`.
  3. `dpd_headword_sbs.jinja`: Russian block renders when `show_ru_data`; SBS block when `show_sbs_data`; Tamil "தமிழ்" row after SBS block when `show_ta_data and d.ta and d.ta.ta_meaning`.
- **Watch For**:
  - Never blindly overwrite — meticulous prefix preservation is required.
  - When upstream adds new grammar table rows, verify the locale rows (RU, SBS, Tamil) are re-applied in order.

---


**File**: `exporter/goldendict/export_dpd_sbs.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: Significant structural divergence for SBS output format.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. `generate_dpd_html` signature adds `dpspth: DPSPaths`, `show_sbs_data`, `show_ru_data`, `show_ta_data`, and `show_grammar` flags.
  2. Eagerly loads `.rt`, `.ru`, `.ta`, and `.sbs` relationships.
  3. Synonyms logic includes a conditional Russian set lookup if `show_ru_data` is true.
  4. `_parse_batch_top_level` uses `sbs_templates/` and passes all locale flags including `show_ta_data`.
  5. `DpdHeadwordRenderDataBase` TypedDict includes `show_ta_data: bool`.
- **Watch For**:
  - When upstream adds new eager-loaded relationships, also add `.ta` to the joinedload chain.
  - All locale flags (`show_sbs_data`, `show_ru_data`, `show_ta_data`, `show_grammar`) must be threaded through `render_data`, `_parse_batch_top_level`, and `render_pali_word_dpd_html` in sync.

---


**File**: `exporter/goldendict/export_epd_sbs.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: SBS-specific output logic diverges from upstream.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. `EpdDataSBS` subclass added to handle combined English + Russian + Tamil EPD entries.
  2. `generate_epd_html` accepts `show_ru_data` and `show_ta_data` flags.
  3. If `show_ru_data` is true, queries `Lookup.rpd` and merges into the EPD dict.
  4. If `show_ta_data` is true, queries `Lookup.tpd` and merges into the EPD dict.
  5. Uses `epd_sbs.jinja` template.
- **Watch For**:
  - Merged results mean one lookup key can map to DPD + Russian + Tamil equivalents simultaneously.
  - Adding a new locale lookup follows the same pattern: query `Lookup.<locale>`, iterate entries, merge into `epd_dict`.

---


**File**: `exporter/goldendict/export_help_sbs.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: SBS-specific help content structure.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. `generate_help_html` accepts `show_ru_data` flag and passes it to `add_abbrev_html` and `add_help_html`.
  2. Templates `help_abbrev_sbs.jinja` and `help_help_sbs.jinja` receive the `show_ru_data` flag to conditionally render Russian columns.
  3. Uses `utils_sbs.RenderedSizes` and `DPSPaths`.
- **Watch For**:
  - Requires `utils_sbs.py` to be in sync with `tools/utils.py`.

---


**File**: `exporter/goldendict/export_roots_sbs.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: SBS data injection makes mechanical parity impractical.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. `generate_root_html` accepts `show_ru_data` flag.
  2. Uses `root_headword_sbs.jinja` template.
- **Watch For**:
  - Template structure must match `data_classes_dps.RootsData`.

---


**File**: `exporter/goldendict/main_sbs.py`
- **Category**: inspired_by_upstream
- **Divergence Reason**: SBS-specific dictionary entry point.
- **Sync Rule**: inspired_only
- **Local Changes**:
  1. `GlobalVars` adds `dpspth: DPSPaths`.
  2. Config flags `show_sbs_data`, `show_ru_data`, `show_ta_data`, and `show_grammar` are read from `config.ini` during initialization.
  3. `show_ta_data` is passed to both `generate_dpd_html()` and `generate_epd_html()`.
  4. `prepare_export_to_goldendict_mdict` appends "SBS fork by Devamitta" to the author and description.
  5. JS paths use `dpspth` and point to `sbs_` prefixed files.
- **Watch For**:
  - When adding a new locale flag, wire it through `GlobalVars`, `generate_dpd_html`, and `generate_epd_html` — all three must be updated together.

---


**File**: `exporter/webapp/sbs_templates/`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Webapp Jinja2 templates with SBS field bindings (chant links, class links).
  2. Shared layout with `ru_templates/` but different data bindings.
- **Watch For**:
  - High structural parity with `ru_templates/` is expected.

---
