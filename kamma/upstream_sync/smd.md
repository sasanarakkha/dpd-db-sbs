# Shadow Module Descriptions (SMD)
> Read this file before touching ANY file during sync.
> If a file has no SMD entry, STOP and flag it.

## Format per entry
- **File**: path
- **Category**: modified_upstream | russian_copy | sbs_copy
- **Sync Rule**: PORT / MIRROR_EXACTLY / PRESERVE / DISCUSS
- **Local Changes**: numbered list of concrete changes
- **Watch For**: specific pitfalls during sync

---

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


**File**: `conductor/product-guidelines.md`
- **Category**: modified_upstream
- **Sync Rule**: PRESERVE
- **Local Changes**:
  1. Fork-specific product guidelines for the DPS/SBS/RU project context.
  2. Upstream may update guidelines; fork version reflects DPS editorial decisions.
- **Watch For**:
  - Review upstream changes for relevant policy shifts, but do not blindly overwrite — DPS guidelines take precedence.

---


**File**: `conductor/product.md`
- **Category**: modified_upstream
- **Sync Rule**: PRESERVE
- **Local Changes**:
  1. Fork-specific product definition for DPS/SBS dictionary builds.
  2. Documents localized build targets (RU goldendict, SBS goldendict, webapp).
- **Watch For**:
  - Upstream product.md reflects upstream build targets only — do not replace fork version.

---


**File**: `conductor/tech-stack.md`
- **Category**: modified_upstream
- **Sync Rule**: PRESERVE
- **Local Changes**:
  1. "DPS Ecosystem" section added: fork repo, recitations, courses, study-tools links.
  2. "Custom Tooling" section references `kamma/upstream_sync/registry.json`.
  3. "Modified Upstream Files" and "DPS & SBS Unique Tooling" sections document fork deviations.
- **Watch For**:
  - Upstream tech-stack changes (new frameworks, tooling) should be merged into the DPS Ecosystem section manually.
  - Never replace the entire file — always merge.

---


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


**File**: `gui2/main.py`
- **Category**: modified_upstream
- **Sync Rule**: DISCUSS
- **Why DISCUSS**: Imports `fast_api_utils_dps` (DPS-specific server launcher) instead of upstream's `fast_api_utils`, and adds `DpsView` and `AnalysisView` tabs. Blind porting removes DPS GUI entirely.
- **Local Changes**:
  1. `from tools.fast_api_utils_dps import start_dpd_server` (line ~11) replaces upstream's `fast_api_utils` import.
  2. `DpsView` tab (line ~91): `self.dps_view = DpsView(self.page, self.toolkit)`.
  3. `AnalysisView` tab (line ~92): `self.analysis_view = AnalysisView(...)`.
  4. Conditional imports for `DpsView`/`AnalysisView` inside the class body (lines ~26-27).
- **Watch For**:
  - Upstream GUI refactors that change the tab initialization pattern will break DPS tab injection — check constructor signature.
  - If upstream switches from `fast_api_utils` to another server module, `fast_api_utils_dps` must be updated to match the new API.
  - New upstream view tabs added to `main.py` should be reviewed to ensure DPS views are still appended correctly.

---


**File**: `gui2/pass2_add_view.py`
- **Category**: modified_upstream
- **Sync Rule**: PORT
- **Local Changes**:
  1. `from tools.fast_api_utils_dps import request_dpd_server` (line ~24) replaces upstream's `fast_api_utils` import for DPS server requests.
  2. All server request calls go through `request_dpd_server` from the DPS shadow module, ensuring DPS-specific server configuration (host/port/timeout) is used instead of upstream defaults.
- **Watch For**:
  - If upstream changes the function name in `fast_api_utils`, the `fast_api_utils_dps` shadow must be updated to match.
  - Upstream GUI refactors to `Pass2AddView` constructor or method signatures need manual review.

---


**File**: `tools/ai_manager.py`
- **Category**: modified_upstream
- **Sync Rule**: PORT
- **Local Changes**:
  1. No significant localized additions found — this file appears to be nearly identical to upstream. Track for future localized AI processing hooks.
  2. Monitor for any DPS-specific AI batch processing logic that may be added.
- **Watch For**:
  - If upstream restructures AI manager interfaces, verify DPS AI tools (`tools/ai_batch_processor.py`, `tools/ai_openai_manager.py`) still import correctly.

---


**File**: `.gitignore`
- **Category**: modified_upstream
- **Sync Rule**: DISCUSS
- **Why DISCUSS**: Contains a `# --- DPS / SBS / RU UNIQUE patterns ---` block (line ~114) listing DPS-specific build artifacts and generated JS/XHTML files. Blind porting would re-track these files in git.
- **Local Changes**:
  1. DPS/SBS/RU-specific block: excludes RU goldendict JS artifacts, kindle epub XHTML outputs, SBS-specific generated files (lines ~114-130).
  2. Any upstream `.gitignore` additions must be merged, not replaced.
- **Watch For**:
  - New upstream ignore patterns may conflict with DPS-specific entries — review the diff carefully.
  - The DPS block at the bottom must be preserved after every upstream merge.

---


**File**: `AGENTS.md`
- **Category**: modified_upstream
- **Sync Rule**: DISCUSS
- **Why DISCUSS**: Fork identity sections, shadow sync policy, and localized project rules are embedded here. Blind porting would overwrite fork-specific AI agent instructions with upstream defaults.
- **Local Changes**:
  1. "Localized Rules" section added with fork identity, local model additions, DPS GitHub issue mapping, shadow sync policy, and engineering standards.
  2. `kamma/upstream_sync/registry.json` references replace any upstream paths.
  3. Clean Root Folder Protocol and Shadow Files & Sync Templates sections are fork-specific.
- **Watch For**:
  - After any upstream AGENTS.md update, manually merge only the "Project Rules (from original upstream)" section — never replace the entire file.
  - Fork-local sections must be preserved verbatim.

---


**File**: `.github/workflows/ru_release.yml`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Adapted from `draft_release.yml` to build and release Russian dictionary artifacts.
  2. Release targets RU goldendict/mdict outputs; upload destinations are RU-specific GitHub release.
- **Watch For**:
  - Upstream changes to release workflow steps (artifact names, upload actions) need mirroring here.

---


**File**: `.github/workflows/ru_release_test.yml`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Test/dry-run variant of `ru_release.yml` — validates RU release build without publishing.
  2. Adapted from `draft_release.yml` with test-mode flags.
- **Watch For**:
  - Keep in sync with `ru_release.yml` — divergence causes test/prod environment drift.

---


**File**: `.github/workflows/ru_static.yml`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Adapted from `static.yml` to build and deploy RU static documentation/webapp.
  2. Deploy targets point to RU-specific GitHub Pages or hosting.
- **Watch For**:
  - Upstream static workflow changes (build commands, deploy steps) need porting here.

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
  1. Imports `rus_degree_of_completion`, `make_short_ru_meaning`, `ru_replace_abbreviations` from Russian utils.
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
  1. Imports `rus_degree_of_completion`, `make_short_ru_meaning`, `ru_replace_abbreviations` from Russian utils.
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
  1. Imports `rus_degree_of_completion`, `make_short_ru_meaning`, `ru_replace_abbreviations`, `populate_set_ru_and_check_errors`.
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
  1. Imports `rus_degree_of_completion`, `make_short_ru_meaning`, `ru_replace_abbreviations`.
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


**File**: `docs_rus/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Complete Russian translation of the `docs/` directory: features, install, webapp, integrations, contributing, technical sections.
  2. Served by `mkdocs_ru.yaml`; deployed to `devamitta.github.io/dpd.rus/`.
- **Watch For**:
  - No automated sync with English docs — all new upstream pages must be translated and added manually.
  - Navigation structure must be kept in sync with `mkdocs_ru.yaml`.

---


**File**: `exporter/deconstructor/deconstructor_exporter_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Custom `DeconstructorDataRu` subclass overrides dict name, author, and website info with Russian values.
  2. Jinja environment loaded from `exporter/goldendict/ru_components/templates/` (uses `deconstructor_header_ru.jinja`).
  3. Stores both `pth` and `rupth`; class renamed `ProgData` vs. upstream's `GlobalVars`.
  4. Dict info strings (name, author, website) point to Russian fork identifiers.
- **Watch For**:
  - If upstream changes `DeconstructorData` base class constructor or method signatures, `DeconstructorDataRu` subclass must update.
  - Template path `ru_components/templates/deconstructor_header_ru.jinja` must exist — missing template causes silent failure.

---


**File**: `exporter/goldendict/ru_components/javascript/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. JavaScript components for Russian GoldenDict export; mirrors upstream `templates/javascript/` with `ru_` prefixed variable names and loader classes.
  2. All GoldenDict JS object names use `rudata_` prefix to avoid namespace collisions with the upstream DPD dictionary loaded in the same GoldenDict instance.
- **Watch For**:
  - If upstream JS logic changes (new functions, renamed variables), Russian counterparts must be updated.
  - `ru_` prefix on all exported JS names is mandatory — removing it causes GoldenDict variable collision.

---


**File**: `exporter/goldendict/ru_components/templates/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Triple Shadow**: This directory, `exporter/goldendict/sbs_templates/`, and upstream `exporter/goldendict/templates/` are all related. New upstream templates need both shadow dirs.
- **Local Changes**:
  1. All HTML/Jinja2 templates use `ru_` prefixed IDs and CSS classes (e.g., `id="ru_grammar_..."`) to avoid GoldenDict namespace collisions.
  2. RU-specific data objects prefixed with `rudata_`; loader classes prefixed `ru_load_js`.
- **Watch For**:
  - Never blindly overwrite — all `id=`, `class=`, and JS variable names have `ru_` prefix that must be preserved.
  - Check for new upstream template files that have no RU counterpart yet.

---


**File**: `exporter/goldendict/export_dpd_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports `Russian` model; `DpdHeadwordDbParts` TypedDict includes `ru: Russian` field.
  2. Imports `data_classes_dps` instead of upstream's `data_classes`.
  3. Uses `RuPaths`; all render-data paths resolve to Russian output directories.
  4. Imports `read_set_ru_from_tsv` for Russian set name lookups.
- **Watch For**:
  - Any new upstream TypedDict fields must be added here AND `data_classes_dps.py` must be updated.
  - The `data_classes_dps` module is a dual-shadow (also used by `export_dpd_sbs.py`) — changes affect both variants.

---


**File**: `exporter/goldendict/export_help_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `Abbreviation` data class adds `ru_abbrev` and `ru_meaning` fields; `Help` data class adds `ru_help` and `ru_meaning`.
  2. Uses `RuPaths`; reads help/abbreviation TSVs from Russian data files.
  3. `generate_help_html()` signature includes `rupth: RuPaths` and `show_ru_data=False` parameters.
- **Watch For**:
  - If upstream adds new columns to the Abbreviation/Help TSV format, Russian fields must be added in parallel.
  - `show_ru_data` parameter must be threaded consistently through all call sites.

---


**File**: `exporter/goldendict/export_roots_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Uses `RuPaths`; `generate_root_html()` signature takes `rupth: RuPaths` parameter.
  2. Jinja env loaded from `exporter/goldendict/ru_components/templates/`; renders `root_headword_ru.jinja`.
  3. Imports `RootsData` from `data_classes_dps` instead of upstream's `data_classes`.
- **Watch For**:
  - Template `root_headword_ru.jinja` must stay in sync with upstream root data structure.
  - `RootsData` is shared with `export_roots_sbs.py` — changes to it affect both variants.

---


**File**: `exporter/goldendict/export_variant_spelling_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Uses `RuPaths`; `generate_variant_spelling_html()` takes `rupth: RuPaths` parameter.
  2. Jinja env loaded from `exporter/goldendict/ru_components/templates/`.
  3. Imports `VariantData`, `SpellingData` from `data_classes_dps` instead of upstream's `data_classes`.
- **Watch For**:
  - If upstream changes `VariantData`/`SpellingData` constructor or adds new fields, `data_classes_dps` must be updated.
  - Template directory must exist; wrong path causes all variant/spelling entries to fail.

---


**File**: `exporter/goldendict/main_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports from `_ru` exporter modules (`export_dpd_ru`, `export_help_ru`, `export_roots_ru`, `export_variant_spelling_ru`).
  2. Stores `rupth: RuPaths` alongside `pth`; sets `self.paths = self.rupth`.
  3. All exporter function calls route to Russian variants.
- **Watch For**:
  - New upstream exporter modules added to `main.py` must have `_ru` counterparts created and imported here.
  - If upstream changes the `self.paths` usage pattern, Russian path-switching logic must be updated.

---


**File**: `exporter/goldendict/data_classes_dps.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Dual Shadow Note**: This file serves BOTH russian_copies and sbs_copies. Changes must satisfy both RU and SBS data requirements.
- **Local Changes**:
  1. `HeadwordData.__init__` accepts `sbs: Optional[SBS]`, `show_sbs_data`, `show_ru_data` flags (lines ~45-65).
  2. `ru_pos`, `ru_plus_case`, `ru_meaning`, `ru_summary`, `ru_complete`, `ru_grammar`, `ru_base` fields from Russian table (lines ~78-84).
  3. Imports from `tools.tools_for_ru_exporter` (`ru_replace_abbreviations`, `make_ru_meaning_html`, `ru_make_grammar_line`).
  4. SBS column rendering: `self.sbs = self._convert_newlines_sbs(sbs)`.
- **Watch For**:
  - New upstream `HeadwordData` fields must be ported here AND both RU+SBS data rendering preserved.
  - `validate_registry.py` will warn about the cross-category overlap — this is expected and intentional.

---


**File**: `exporter/grammar_dict/grammar_dict_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Custom `GrammarDataRu` subclass overrides `_process_grammar()` to translate POS and grammar components via `ru_replace_abbreviations()`.
  2. Stores `rupth: RuPaths`; uses `load_abbreviations_dict` from Russian utils.
  3. Class renamed `ProgData` vs. upstream's `GlobalVars`.
- **Watch For**:
  - If upstream changes `GrammarData._process_grammar()` signature or internal processing steps, the Russian override must be updated.
  - Russian abbreviation table must be kept current — missing entries produce untranslated Russian grammar output.

---


**File**: `exporter/kindle/kindle_exporter_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports `RuPaths`, `make_ru_meaning_for_ebook`, `ru_replace_abbreviations`, `rus_degree_of_completion`.
  2. `render_dpd_xhtml()` takes both `pth: ProjectPaths` and `rupth: RuPaths` parameters.
  3. Eagerly loads `.ru` via `joinedload(DpdHeadword.ru)`.
  4. Uses Russian Jinja2 templates from `exporter/kindle/ru_components/templates/`.
- **Watch For**:
  - If upstream changes `render_dpd_xhtml()` signature, both `pth` and `rupth` params must be preserved.
  - Kindle/EPUB output paths resolve via `RuPaths` — ensure path class stays in sync.

---


**File**: `exporter/kindle/ru_components/cover/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Russian Kindle/EPUB cover image and metadata files.
  2. Cover design is fork-specific (Russian title, branding).
- **Watch For**:
  - Cover image dimensions must match Kindle requirements; any upstream change to cover specs needs Russian cover update.

---


**File**: `exporter/kindle/ru_components/epub/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Russian-language EPUB structural files (OPF manifest, NCX navigation, CSS).
  2. Metadata fields (title, author, language) set to Russian fork values.
- **Watch For**:
  - If upstream changes EPUB structure or adds new manifest items, Russian epub must be updated in parallel.

---


**File**: `exporter/kindle/ru_components/templates/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Jinja2 XHTML templates for Russian Kindle export; bind Russian meaning fields from the `Russian` model.
  2. CSS classes and HTML structure must be compatible with Kindle/EPUB readers.
- **Watch For**:
  - Template variable names must match `kindle_exporter_ru.py` data class fields exactly.
  - If upstream changes the upstream Kindle template structure, Russian templates must be updated to match.

---


**File**: `exporter/tbw/tbw_exporter_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports `RuPaths`, `make_ru_meaning_simpl`, `ru_replace_abbreviations`; stores both `pth` and `rupth` in `ProgData`.
  2. Outputs to Russian-specific export directories via `RuPaths`.
  3. Does NOT use `joinedload` for `.ru` — queries `DpdHeadword` without eager-loading Russian data (uses `.ru` relationship lazily or accesses it differently).
- **Watch For**:
  - Lazy-load of `.ru` relationship may cause N+1 queries if entry count grows significantly.
  - If upstream TBW format specification changes, Russian version must be updated to match.

---


**File**: `exporter/tpr/tpr_exporter_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports `RuPaths`; stores both `pth` and `rupth` in `GlobalVars`.
  2. Eagerly loads `.ru` via `joinedload(DpdHeadword.ru)`.
  3. Outputs to Russian-specific TPR export directories via `RuPaths`.
- **Watch For**:
  - If upstream changes `make_dpd_db()` method signature, Russian version must update call site.
  - TPR format is external dependency — verify compatibility when upstream updates TPR export logic.

---


**File**: `exporter/webapp/data_classes_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `HeadwordData.__init__` adds `ru_meaning`, `ru_grammar`, `ru_pos`, `ru_plus_case`, `ru_root_base`, `ru_phonetic`, `inflections_html_ru`, `rus_complete` fields.
  2. `convert_newlines()` explicitly handles `ru_meaning`, `ru_meaning_lit`, `ru_notes` string columns (avoids triggering lazy loads).
  3. Also passes `i.sbs` to `convert_newlines()` — converts newlines in SBS columns too.
  4. `RootsData` adds `root_info_ru` and `root_matrix_ru` fields via `ru_replace_abbreviations`.
- **Watch For**:
  - New upstream `HeadwordData` fields must be ported here AND the Russian-specific fields preserved.
  - `convert_newlines()` must whitelist new string columns if upstream adds them — missing columns are skipped silently.

---


**File**: `exporter/webapp/main_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Sync comment at top records last manual sync date against upstream `main.py`.
  2. Imports `RuPaths`, `make_dpd_html_ru`, `make_headwords_clean_set_ru`, `auto_translit_to_roman`.
  3. Stores `rupth: RuPaths` alongside `pth`; initializes `headwords_clean_set_ru` during startup.
  4. All HTML rendering routes through `make_dpd_html_ru()` instead of upstream's function.
- **Watch For**:
  - The sync comment date is the only indicator of drift — check it before every sync.
  - New upstream FastAPI routes or startup logic must be ported here manually.

---


**File**: `exporter/webapp/preloads_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `make_headwords_clean_set_ru()` extends the upstream headword set by also including entries where `Lookup.rpd != ""` (Russian EPD).
  2. Defers heavy columns (`inflections_html`, `freq_html`, `inflections_sinhala`, etc.) for performance.
- **Watch For**:
  - If upstream adds new deferred columns to improve performance, mirror them here.
  - The `rpd` filter is Russian-specific; if the column is renamed in the `Lookup` model, this breaks silently.

---


**File**: `exporter/webapp/toolkit_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `make_dpd_html_ru()` takes both `pth: ProjectPaths` and `rupth: RuPaths` parameters.
  2. Uses `data_classes_ru.HeadwordData`, `RootsData`, and other Russian data classes throughout.
  3. Shares a `VariantManager` singleton with upstream variant logic.
- **Watch For**:
  - If upstream changes the `make_dpd_html()` function signature, `make_dpd_html_ru()` must be updated to match.
  - All data class types are Russian-specific — new upstream data class fields must be ported to `data_classes_ru.py`.

---


**File**: `exporter/webapp/ru_templates/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Webapp Jinja2 templates with Russian-specific field bindings (RU meaning, RU grammar fields).
  2. `dpd_headword.html` in this dir is a complex merge of upstream layout plus RU column rendering — prone to merge errors on upstream structural refactors.
- **Watch For**:
  - `dpd_headword.html` has the highest merge risk; always diff carefully against upstream version.
  - Check sibling `exporter/webapp/sbs_templates/` in the same sync pass.

---


**File**: `scripts/bash/generate_components.sh`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Runs all upstream family builders first, then appends Russian family builders: `family_root_ru.py`, `family_word_ru.py`, `family_compound_ru.py`, `family_set_ru_update.py`, `family_set_ru.py`, `family_idiom_ru.py`.
  2. Also runs `version.py` and `config_uposatha_day.py` before inflection generation.
- **Watch For**:
  - If upstream adds new component scripts to its version of this file, they must be incorporated here before the Russian family section.
  - Order matters: Russian family scripts must run after their upstream counterparts.

---


**File**: `scripts/bash/make_dpd.sh`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Opens with `git checkout sbs-ru` to ensure correct branch.
  2. Build menu offers DPS-specific config presets: option 1 = `config_github_server_dpd_sbs.py`, option 2 = `config_github_local_dpd_sbs.py`.
  3. Calls `generate_components.sh` and DPS-specific exporter sequence.
- **Watch For**:
  - If upstream changes its build flow, DPS-specific config calls must be kept in sync.
  - The hardcoded branch name `sbs-ru` will fail if branch is renamed.

---


**File**: `scripts/bash/make_ru_dpd.sh`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Opens with `git checkout sbs-ru`.
  2. Build menu: option 1 = `config_github_release_dpd_rus.py`, option 2 = `config_github_local_dpd_rus.py`.
  3. When skipping `generate_components`, runs `families_to_json_ru.py` as a lightweight alternative.
  4. Entire script is Russian-export focused (no SBS config options).
- **Watch For**:
  - Hardcoded branch name `sbs-ru` and config script names — both must be updated if renamed.
  - Skipping `generate_components` skips upstream family builds too; ensure data is current before running.

---


**File**: `scripts/build/families_to_json_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Stores `rupth: RuPaths`; sets `self.paths = rupth` so all output paths resolve to Russian export directories.
  2. Otherwise structurally identical to upstream `families_to_json.py`.
- **Watch For**:
  - If upstream changes the family-to-JSON export logic or output format, this file must be updated to match before adding the path swap.
  - Output directory must exist via `RuPaths`; missing paths fail silently.

---


**File**: `scripts/rus_exporter/config_github_release_dpd_rus.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Sets `show_ru_data=yes`, `show_sbs_data=no` — Russian-only release profile.
  2. Enables `make_tbw=yes` and `make_tpr=yes` in addition to standard exporters.
  3. Disables `db_rebuild`, `inflections`, `transliterations`, `freq_maps` (uses pre-built data).
- **Watch For**:
  - If upstream adds new config keys, review whether they should be set for Russian releases.
  - `make_mdict=yes` must remain consistent with Russian release packaging scripts.

---


**File**: `scripts/rus_exporter/ru_config_github_release.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Full upstream-compatible release: `db_rebuild=yes`, `inflections=yes`, `transliterations=yes`, `freq_maps=yes`.
  2. `show_ru_data=no`, `show_sbs_data=no` — produces standard DPD export without localized data layers.
  3. Enables all exporters including `make_deconstructor=yes`, `tarball_db=yes`, `make_tbw=yes`, `make_tpr=yes`.
- **Watch For**:
  - This is the "full rebuild" config; if upstream adds new rebuild steps, add corresponding config keys here.
  - `deconstructor use_premade=yes` flag must stay set to avoid slow deconstructor rebuild during release.

---


**File**: `scripts/rus_exporter/ru_zip_goldendict_mdict.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Zips 4 Russian GoldenDict dirs into one package: `ru-dpd`, `ru-dpd-grammar`, `ru-dpd-deconstructor`, `dpd-variants`.
  2. Uses `RuPaths` for all input/output path resolution.
  3. Output file: `rupth.dpd_goldendict_zip_path`.
- **Watch For**:
  - If upstream changes its GoldenDict zip packaging (new dirs, different names), the Russian variant must match.
  - All 4 source dirs must exist before zipping; missing dirs cause silent empty archives.

---


**File**: `scripts/rus_exporter/zip_dpd_rus.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Zips combined DPD+RUS package: `dpd+rus-goldendict.zip` and `dpd+rus-mdict.zip`.
  2. Uses `ProjectPaths` (not `RuPaths`) — packages the upstream GoldenDict dir, which contains both DPD and Russian data after a combined export.
- **Watch For**:
  - Output filenames are hardcoded (`dpd+rus-goldendict.zip`) — update if naming convention changes.
  - Uses `pth.share_dir` as output destination; if `ProjectPaths` share dir is relocated, update here.

---


**File**: `scripts/rus_exporter/docs_add_indexes.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Reads `mkdocs_ru.yaml` nav structure and generates index pages for each Russian doc section.
  2. Uses `RuPaths` (`rupth.mk_docs_yaml`, `rupth.docs_dir`) for all path resolution.
- **Watch For**:
  - Depends on `mkdocs_ru.yaml` nav format; if nav structure changes, index generation may produce wrong paths.
  - `rupth.docs_dir` must point to `docs_rus/` — any `RuPaths` rename breaks this script.

---


**File**: `shared_data/help_ru/`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Russian translations of help content and abbreviation meanings, stored as TSV files.
  2. Read by `db/lookup/help_abbrev_add_to_lookup_ru.py` using hardcoded column indices.
- **Watch For**:
  - Column structure must match the indices hardcoded in `help_abbrev_add_to_lookup_ru.py` (help col 2, abbrev col 5).
  - If upstream adds new help entries, corresponding Russian translations must be added here.

---


**File**: `tools/degree_of_completion_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Wraps upstream `degree_of_completion()` with Russian-aware logic: removes the gray "incomplete" CSS class for words that have a `ru_meaning`.
  2. Falls back to the upstream function for words with no Russian data.
- **Watch For**:
  - Depends on `i.ru.ru_meaning` — if `Russian` model renames this field, wrapper logic silently breaks.
  - If upstream changes `degree_of_completion()` signature, wrapper must update its call.

---


**File**: `tools/paths_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Triple Shadow**: Both `tools/paths_ru.py` (class `RuPaths`) and `tools/paths_dps.py` (class `DPSPaths`) shadow `tools/paths.py`. Every new upstream path constant MUST be ported to BOTH shadow files.
- **Local Changes**:
  1. Defines `RuPaths` class (not `ProjectPaths`) with all upstream `ProjectPaths` constants remapped to Russian export directories.
  2. Adds RU-specific output paths (goldendict RU components, kindle RU components, webapp RU templates, etc.).
- **Watch For**:
  - New upstream `ProjectPaths` constants are silently ignored in both shadow files until manually added — check every upstream `paths.py` change against both shadows.
  - Class name is `RuPaths`, not `ProjectPaths` — importers use `from tools.paths_ru import RuPaths`.

---


**File**: `tools/ru_spelling.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `RuSpellChecker` singleton class using `SpellChecker(language="ru")` from the `pyspellchecker` library.
  2. Loads a custom word dictionary from `DPSPaths.ru_user_dict_path` on first initialization.
  3. Thread-safe with double-checked locking pattern.
  4. Sync comment at top records last sync date against upstream `spelling.py`.
- **Watch For**:
  - `DPSPaths.ru_user_dict_path` must point to a valid custom dictionary file; missing file creates empty dict silently.
  - If upstream changes `SpellChecker` usage pattern, Russian wrapper must match.

---


**File**: `tools/translit_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `auto_translit_to_roman()` uses `aksharamukha` library to transliterate non-Pali/non-Cyrillic/non-English text to IAST Pali Roman.
  2. `is_cyrillic()` helper short-circuits transliteration for Russian text (leaves Cyrillic untouched).
  3. Short-circuits for uppercase abbreviations (DN1, DHPa), pure Pali, and English too.
- **Watch For**:
  - Depends on `aksharamukha` library being installed — not in upstream dependencies.
  - If upstream's `pali_alphabet` or `english_alphabet` lists change, short-circuit conditions may need updating.

---


**File**: `tools/version_ru.py`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Generates `version_ru` string with `ru_` prefix; queries/updates `dpd_sbs_release_version` DB key (not upstream's `dpd_release_version`).
  2. Metadata fields (author, email, website, docs, github, license) all point to Russian fork URLs.
  3. Website: `ru.dpdict.net`; docs: `devamitta.github.io/dpd.rus/`; GitHub: `sasanarakkha/dpd-db-sbs`.
- **Watch For**:
  - Version string pattern must match upstream `major.minor.patch` format — divergence breaks release tooling.
  - DB key `dpd_sbs_release_version` is fork-specific; if upstream renames `dpd_release_version`, Russian key is unaffected but must remain distinct.

---


**File**: `mkdocs_ru.yaml`
- **Category**: russian_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Site name, docs dir (`docs_rus`), and repo URL all point to the Russian fork.
  2. Entire navigation structure translated to Russian.
  3. Alternate language link added for English version; social links point to Russian fork GitHub.
- **Watch For**:
  - Navigation structure must stay manually in sync with upstream `mkdocs.yaml` — new upstream pages need corresponding Russian entries.
  - `docs_dir: docs_rus` is hardcoded; if the Russian docs directory is renamed, update both here and `docs_add_indexes.py`.

---


**File**: `exporter/goldendict/sbs_templates/`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Triple Shadow**: See `exporter/goldendict/ru_components/templates/` — same pattern, SBS variant.
- **Local Changes**:
  1. All HTML/Jinja2 templates use `sbs_` prefixed IDs and CSS classes to avoid GoldenDict namespace collisions.
  2. SBS-specific data objects prefixed with `sbsdata_`; loader classes prefixed `sbs_load_js`.
- **Watch For**:
  - Never blindly overwrite — `sbs_` prefix must be preserved on all IDs and JS names.
  - Sync in parallel with RU templates to avoid divergence.

---


**File**: `exporter/goldendict/export_dpd_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports `DPSPaths` instead of `ProjectPaths`; all paths resolve to SBS output directories.
  2. Imports `data_classes_dps` (dual-shadow shared with Russian variant).
  3. Uses `joinedload` for eager loading; no Russian model fields (SBS-only variant).
- **Watch For**:
  - `data_classes_dps` is shared with the Russian exporter — changes to it affect both.
  - New upstream TypedDict fields must be ported here AND to `data_classes_dps`.

---


**File**: `exporter/goldendict/export_epd_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Custom `EpdDataSBS` subclass of `EpdData` with simplified constructor.
  2. Uses `DPSPaths`; Jinja env loaded from `exporter/goldendict/sbs_templates/` (renders `epd_sbs.jinja`).
  3. Includes Russian EPD lookup via `Lookup.rpd` filter alongside English `Lookup.epd`.
- **Watch For**:
  - If upstream changes `EpdData` base class, `EpdDataSBS` subclass must be updated.
  - Both `epd` and `rpd` columns are queried — if `Lookup.rpd` is renamed in the model, this breaks.

---


**File**: `exporter/goldendict/export_help_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `Abbreviation` data class includes `ru_abbrev` and `ru_meaning`; `Help` class includes `ru_help` and `ru_meaning`.
  2. Uses `DPSPaths`; imports `RenderedSizes`/`default_rendered_sizes` from `tools.utils_sbs` (not upstream's `tools.utils`).
  3. Jinja env from `exporter/goldendict/sbs_templates/`.
- **Watch For**:
  - `utils_sbs.RenderedSizes` is a fork-specific copy of `tools.utils.RenderedSizes` — if upstream adds new size fields, update `utils_sbs` too.
  - SBS templates directory must exist; missing templates cause entire help export to fail.

---


**File**: `exporter/goldendict/export_roots_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Uses `DPSPaths`; `generate_root_html()` signature has `show_ru_data=False` parameter.
  2. Jinja env loaded from `exporter/goldendict/sbs_templates/`; renders `root_headword_sbs.jinja`.
  3. Imports `RenderedSizes`/`default_rendered_sizes` from `tools.utils_sbs`.
- **Watch For**:
  - `root_headword_sbs.jinja` template must exist in `sbs_templates/`; sync in parallel with `root_headword_ru.jinja`.
  - `tools.utils_sbs.RenderedSizes` must stay structurally in sync with upstream `tools.utils`.

---


**File**: `exporter/goldendict/main_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Imports from `export_dpd_sbs`, `export_epd_sbs`, `export_help_sbs`, `export_roots_sbs`, `export_variant_spelling` (uses upstream variant spelling — no SBS-specific version).
  2. Stores only `pth: ProjectPaths`; no `rupth` (SBS uses standard paths for the shared GoldenDict output).
- **Watch For**:
  - If upstream adds new exporter modules to `main.py`, review whether SBS needs a dedicated `_sbs` variant.
  - `export_variant_spelling` is shared with upstream — any upstream change to it flows directly into SBS export.

---


**File**: `exporter/goldendict/data_classes_dps.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Dual Shadow Note**: Same file as russian_copy entry above. Serves both RU and SBS categories. All enrichment from that entry applies here.
- **Local Changes**:
  1. `HeadwordData.__init__` accepts `sbs: Optional[SBS]`, `show_sbs_data`, `show_ru_data` flags; SBS column rendering via `self._convert_newlines_sbs(sbs)`.
  2. Russian fields (`ru_pos`, `ru_meaning`, `ru_summary`, etc.) and SBS fields coexist in the same data class, so both sets of columns must be preserved on every upstream sync.
- **Watch For**:
  - New upstream `HeadwordData` fields must be ported here AND both RU+SBS data rendering preserved.
  - `validate_registry.py` will warn about the cross-category overlap — this is expected and intentional.

---


**File**: `exporter/webapp/sbs_templates/`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Webapp Jinja2 templates with SBS-specific field bindings (chant data, class mapping fields).
  2. `dpd_headword.html` here mirrors the RU version but binds SBS columns instead.
- **Watch For**:
  - Same high merge risk as `exporter/webapp/ru_templates/dpd_headword.html`.
  - Always update both template dirs in the same pass to stay structurally aligned.

---


**File**: `scripts/backup/backup_ru_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Backs up `Russian`, `SBS`, and `DpdRoot` (ru roots columns) tables to TSV via `DPSPaths`.
  2. Guards against empty tables before writing — aborts if `Russian` table is empty.
  3. No upstream equivalent; entirely fork-specific.
- **Watch For**:
  - If `DPSPaths` backup path attributes are renamed, backup destinations silently change.
  - Empty-table guard is on `Russian` only — `SBS` could be empty without aborting.

---


**File**: `scripts/build/db_rebuild_from_tsv_ru_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Populates `Russian`, `SBS`, and `DpdRoot` (ru root columns) tables from TSV files in `DPSPaths` backup locations.
  2. Validates for duplicate IDs in all three TSVs before importing; exits on first duplicate found.
  3. Validates that all Russian/SBS IDs exist in `DpdHeadword` — prompts user to remove orphaned rows.
- **Watch For**:
  - TSV column schema must match model field names exactly; silent data corruption if columns drift.
  - Duplicate-check logic uses `tools.duplicates.has_duplicate_values_in_column` — if that utility changes, validate behavior.

---


**File**: `scripts/fix/character_replacer_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Generic find-and-replace tool for SBS or Russian model columns; target table and column configured via top-level variables (`find_char`, `replace_char`, `table`, `column`).
  2. Uses `joinedload` for both `.sbs` and `.ru` relationships.
  3. Prompts for confirmation before committing changes to DB.
- **Watch For**:
  - `table` and `column` variables are hardcoded at the top of the file — must be edited before each use.
  - If `SBS` or `Russian` model column names change, the configured `column` value will silently match nothing.

---


**File**: `scripts/rus_exporter/config_github_release_dpd_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Sets `show_sbs_data=yes`, `show_ru_data=no` — SBS-only release profile.
  2. Disables most exporters except `make_dpd=yes`; no tbw/tpr/ebook.
  3. Disables `db_rebuild`, `inflections`, etc. (uses pre-built data).
- **Watch For**:
  - If upstream adds new config keys, review whether they should be enabled for SBS releases.
  - Contrast carefully with `config_github_release_dpd_rus.py` — the two profiles enable different exporter sets.

---


**File**: `scripts/rus_exporter/zip_dpd_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Zips combined DPD+SBS package: `dpd+sbs-goldendict.zip` and `dpd+sbs-mdict.zip`.
  2. Uses `ProjectPaths` — packages the standard GoldenDict output dir (same pattern as `zip_dpd_rus.py`).
- **Watch For**:
  - Output filenames are hardcoded (`dpd+sbs-goldendict.zip`) — update if naming convention changes.
  - Error message still says "no ru-dpd dir file found" (copy-paste from Russian version) — cosmetic but misleading.

---


**File**: `scripts/server/update-dpd-sbs.sh`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Server deployment script: pulls `dpd-db-sbs` repo, syncs deps, downloads `dpd.db` from `sasanarakkha/dpd-db-sbs` releases.
  2. Starts `exporter.webapp.main_ru:app` (Russian webapp) on port 8081.
  3. Kills any existing uvicorn process before restarting; logs to timestamped file in `logs/`.
- **Watch For**:
  - Hardcoded GitHub release URL (`sasanarakkha/dpd-db-sbs`) and port 8081 — both must match server configuration.
  - Script runs `generate_search_index.py` after DB download; if that script moves, update path here.

---


**File**: `tools/utils_sbs.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Provides `paragraphs_are_similar()` (used by `db/models.py` import) for fuzzy paragraph comparison.
  2. Contains `RenderedSizes` TypedDict and `default_rendered_sizes()` — a fork-specific copy of `tools/utils.py`'s equivalent, used by SBS exporters.
- **Watch For**:
  - `RenderedSizes` must stay structurally in sync with upstream `tools/utils.RenderedSizes` — SBS exporters that import from here will silently miss new size keys.
  - `paragraphs_are_similar` is imported in `db/models.py` — do not remove or rename it.

---


**File**: `tools/paths_dps.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Triple Shadow**: Both `tools/paths_ru.py` (class `RuPaths`) and `tools/paths_dps.py` (class `DPSPaths`) shadow `tools/paths.py`. Every new upstream path constant MUST be ported to BOTH shadow files.
- **Local Changes**:
  1. Defines `DPSPaths` class with all upstream `ProjectPaths` constants remapped to SBS/DPS export directories.
  2. Adds DPS-specific output paths (goldendict SBS templates, SBS backup TSVs, DPS anki outputs, etc.).
- **Watch For**:
  - Mirrored risk as `paths_ru.py`: new upstream constants silently absent until manually ported.
  - Class name is `DPSPaths` — importers use `from tools.paths_dps import DPSPaths`.

---


**File**: `tools/fast_api_utils_dps.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. `start_dpd_server()` launches `exporter.webapp.main_ru:app` on port 8080 (vs. upstream's `main:app`).
  2. `request_dpd_server()` opens `http://127.0.0.1:8080/sbs/` — the SBS-prefixed endpoint.
  3. `request_bold_def_server()` uses host `127.0.0.2:8080` (different host from main server).
- **Watch For**:
  - If upstream changes `fast_api_utils.py` function signatures, this shadow must match — `gui2/main.py` and `gui2/pass2_add_view.py` import from here.
  - Port 8080 is hardcoded — if server port changes, update here AND `update-dpd-sbs.sh`.

---


**File**: `scripts/export/dps_anki_updater.py`
- **Category**: sbs_copy
- **Sync Rule**: PORT
- **Local Changes**:
  1. Updates DPS Anki deck directly from the database using `anki` Python library.
  2. Uses `DPSPaths` for Anki collection path; eagerly loads both `.sbs` and `.ru` relationships.
  3. Supports optional `test` CLI argument to update a test field instead of production data.
- **Watch For**:
  - Depends on `anki` Python library (not in upstream dependencies) — must be in `uv` deps.
  - Anki collection path in `DPSPaths` must point to the actual Anki installation; breaks if Anki is moved.

---
