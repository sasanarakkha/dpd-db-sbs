# SMD: GUI

**File**: `gui2/main.py`
- **Category**: modified_upstream_files
- **Sync Rule**: DISCUSS
- **Why DISCUSS**: Imports `fast_api_utils_dps` (DPS-specific server launcher) instead of upstream's `fast_api_utils`, and adds `DpsView` tab. Blind porting removes DPS GUI entirely.
- **Local Changes**:
  1. `from tools.fast_api_utils_dps import start_dpd_server` (line ~11) replaces upstream's `fast_api_utils` import.
  2. `DpsView` tab (line ~91): `self.dps_view = DpsView(self.page, self.toolkit)`.
  3. Conditional import for `DpsView` inside the class body (line ~26).
  4. Runtime font scaling patch (module level, after all imports, before `class App`): patches `ft.Text.__init__`, `ft.TextStyle.__init__`, `ft.TextField.__init__`, and `ft.Dropdown.__init__` via `_make_font_scaler` to multiply `size=` / `text_size=` kwargs by `_DPS_FONT_SCALE = 1.4` (using `round()`). No exclusions — all tabs are scaled uniformly. Adjust `_DPS_FONT_SCALE` in `main.py` to retune the app-wide font size. Also patches `DpdTextField.__init__` (post-init): sets `text_size = round(14 * _DPS_FONT_SCALE)` when `text_size is None`, covering fields that omit an explicit `text_size`. DPS files (`dps_view.py`, `dps_fields.py`, `dps_field_mapping.py`) were normalized to upstream-matching explicit sizes (`text_size=14`, `size=12`, etc.) so the global scale renders them at a consistent visual size.
- **Watch For**:
  - Upstream GUI refactors that change the tab initialization pattern will break DPS tab injection — check constructor signature.
  - If upstream switches from `fast_api_utils` to another server module, `fast_api_utils_dps` must be updated to match the new API.
  - New upstream view tabs added to `main.py` should be reviewed to ensure DPS views are still appended correctly.
  - If upstream adds new text-bearing widgets with explicit `size=` / `text_size=` args that should scale, add them to the `_make_font_scaler` calls in `main.py`.
  - If DPS adds new widgets with explicit sizes, use upstream-matching values (e.g. `text_size=14`, `size=10`) so the global scale renders them correctly.

---


**File**: `gui2/pass2_add_view.py`
- **Category**: modified_upstream_files
- **Sync Rule**: PORT
- **Local Changes**:
  1. `from tools.fast_api_utils_dps import request_dpd_server` (line ~24) replaces upstream's `fast_api_utils` import for DPS server requests.
  2. All server request calls go through `request_dpd_server` from the DPS shadow module, ensuring DPS-specific server configuration (host/port/timeout) is used instead of upstream defaults.
- **Watch For**:
  - If upstream changes the function name in `fast_api_utils`, the `fast_api_utils_dps` shadow must be updated to match.
  - Upstream GUI refactors to `Pass2AddView` constructor or method signatures need manual review.

---

**File**: `gui2/dps_view.py`
- **Category**: inspired_by_upstream
- **Sync Rule**: inspired_only
- **Divergence Reason**: Implements the DPS RU/SBS editing tab; reuses upstream's View/Column/PopUpMixin shell but runs an independent Russian/SBS data model, navigation, filters, and DB-write path that have diverged for over a year.
- **Local Changes**:
  1. Imports the `Russian` and `SBS` models plus `fetch_ru`/`fetch_sbs` from `dps_db_helpers` to load and write the DPS-only `Russian` and `SBS` tables (`_click_edit_headword`, `_update_russian_table`, `_update_sbs_table`), with a bulk update for `class_example_translation`.
  2. DPS navigation buttons "Next Ru" / "Next Note": `_click_next_ru` → `_get_next_word_ru` (DpdHeadword JOIN Russian JOIN SBS) and `_click_next_note` → `_get_next_note_ru` (`Russian.ru_notes.like("%ИИ%")`).
  3. `_handle_filter_change` drives all/vib/class radio filters through `DpsFields.filter_fields()` (upstream uses all/root/compound/sutta/word/pass1).
  4. `_click_update_db` gated on `tests_passed` from `DpsTestManager`; builds the middle section with `DpsFields` + `DpsExampleField` and reads a DPS CSV/TSV in `_load_translation_examples` for the translation-hint tooltip; constructs `DPSPaths` and a DPS `HistoryManager`.
  5. Font-scale normalization: explicit `text_size=17 → 14` (3 occurrences) and hint `size=15 → 14` (2 occurrences) so the global `_DPS_FONT_SCALE` renders DPS fields at a consistent size with other tabs.
- **Watch For**:
  - If upstream changes the `request_dpd_server` signature in `fast_api_utils_dps`, the server calls in `_click_update_db` and related handlers must be updated to match.
  - Upstream `Pass2AddView` automation (clone/split/auto/new-word/X-queue/proofreader) is intentionally absent here; only re-evaluate porting if those workflows become relevant to the DPS RU/SBS tab.
  - Constructor/base-class changes to `ft.Column`/`PopUpMixin` or the `HistoryManager` API will require manual update of `__init__`.

---

**File**: `gui2/dps_fields.py`
- **Category**: inspired_by_upstream
- **Sync Rule**: inspired_only
- **Divergence Reason**: Same field-manager pattern but a wholly different mapping-driven RU/SBS field set with AI translation and SBS chant logic, so it cannot share upstream's FieldConfig-driven implementation.
- **Local Changes**:
  1. Field construction is mapping-driven via `dps_field_mapping` (dict) rather than upstream's `field_configs: list[FieldConfig]`; `_build_fields` special-cases `DpsExampleField`, `DpsMeaningField`, and SBS chant `ft.Dropdown`s.
  2. Loads the SBS chant index (`_load_sbs_index` from `sbs_index_path` TSV) and auto-fills `chant_eng`/`chapter` via `_handle_sbs_chant_change`.
  3. AI integration: `_handle_ai_click` → `translate_with_ai_from_gui` (from `dps_ai_service`) for `dps_suggestion`/`dps_notes_suggestion`, plus `_handle_copy_split_click` splitting Russian suggestions on "досл."/"букв." delimiters and `_handle_copy_notes_click`.
  4. `populate_dps_tab(headword, ru_word, sbs_word)` reads `DpdHeadword` + `Russian` + `SBS` (root_ru_meaning, grammar assembly) over the entirely DPS `dps_*` field set; uses `RuSpellChecker` and `DpsExampleStashManager`.
  5. Font-scale normalization: label `size=15 → 12` in field rows; `text_size` skipped in the `setattr` loops for `DpsExampleField` and `DpsMeaningField` (scaling is handled by the `DpdTextField` post-init patch in `main.py`, not via `setattr`). `dps_field_mapping.py` `common_params["text_size"]` normalized `17 → 14` for the same reason.
- **Watch For**:
  - Upstream `DpdFields` carries a large field-automation surface (id_submit, lemma/root/family/construction handlers, etc.) that is deliberately not mirrored — port a handler only if the matching DPS field gains the same behavior.
  - If upstream changes `make_meaning_combo` or `read_tsv_dot_dict` signatures, `populate_dps_tab` / `_load_sbs_index` must follow.

---

**File**: `gui2/dps_fields_lists.py`
- **Category**: inspired_by_upstream
- **Sync Rule**: inspired_only
- **Divergence Reason**: Centralizes the DPS dps_* field names and Vibhanga/Class view groupings, which have no structural overlap with upstream's DPD filter and operational lists.
- **Local Changes**:
  1. Defines `ALL_DPS` (55 `dps_`-prefixed field names) in place of upstream's `ALL` (59 DPD field names).
  2. Provides DPS-only view groupings `VIB_FIELDS` (26) and `CLASS_FIELDS` (27); upstream's `ROOT_FIELDS`/`COMPOUND_FIELDS`/`SUTTA_FIELDS`/`WORD_FIELDS`/`PASS1_FIELDS` filter lists and `NO_CLONE_LIST`/`NO_SPLIT_LIST` operational lists are absent.
- **Watch For**:
  - Any new `dps_*` field added to `dps_field_mapping` must also be appended to `ALL_DPS` and the relevant `VIB_FIELDS`/`CLASS_FIELDS` group, or filtering in `DpsView`/`DpsFields` silently breaks.
  - Upstream adding a new filter group does not transfer here; the DPS Vibhanga/Class split is maintained independently.

---

**File**: `gui2/dps_test_manager.py`
- **Category**: inspired_by_upstream
- **Sync Rule**: inspired_only
- **Divergence Reason**: Runs the same PopUpMixin test-runner pattern against DpsView and a string-values dict with DPS-only test loading/saving, diverging from upstream's toolkit-delegated DpdHeadword-based manager.
- **Local Changes**:
  1. `DpsTestManager.__init__(self, db)` loads tests directly from `DPSPaths().internal_tests_path` via `load_tests`, instead of delegating to a toolkit `DbTestManager`.
  2. `run_all_tests(self, ui: DpsView, values: dict[str, str])` operates on a string-values dict and `DpsView`, not a `DpdHeadword` object / `Pass2AddView`; `integrity_check` validates tests against `dps_field_mapping` keys.
  3. Adds methods absent upstream: `save_tests`, `add_exception`, `sort_tests_by_name`, plus backward-compat shims `load_tests_compat` / `run_tests` / `show_failures_compat`.
  4. Defines `IntegrityFailure` / `TestFailure` as local `NamedTuple`s (upstream imports them from `db_tests.db_tests_manager`); `_handle_open_test_file` opens with VSCode `code` rather than LibreOffice.
- **Watch For**:
  - Upstream changes to `InternalTestRow` or the `db_tests_manager` test schema must be reflected in `load_tests` / `integrity_check`.
  - Upstream failure-dialog UI changes (`_create_failure_dialog`, `_show_current_failure`, `_handle_next_failure`) are candidates for porting since the dialog flow is shared in spirit.

---

**File**: `gui2/dps_example_field.py`
- **Category**: dps_copies
- **Sync Rule**: PORT
- **Local Changes**:
  1. `DpsExampleField(DpdExampleField)` subclass: `__init__` takes a shared `stash_manager` (`DpsExampleStashManager`), adds `archived_example_index`, and bypasses `super().__init__()` by calling `ft.Column.__init__` directly.
  2. `get_fields()` is fully replaced to return a dict parsing DPS multi-type field names (`dps_sbs_example_1`, `dps_dhp_example`, …) into source/sutta/example/chant/chapter; stash/reload/last all operate in dict format (`_handle_last_control_blur`, `_click_stash_example`, `_click_reload_example`, `_click_last_example`).
  3. New SBS archive flow: `_click_arch_example` + `_handle_archive_example` (reads the `sbs_archive` TSV) + `paragraphs_are_similar_sbs` (SequenceMatcher), plus the `_swap_examples` helper.
  4. Action buttons differ (adds "Clean" and "Arch"); `clean_text` / `click_clean_example` strip `<b>`/`</b>` tags and drop upstream's THA/THI expansions and "Add '-" logic.
- **Watch For**:
  - This subclasses `DpdExampleField`, so any upstream change to `DpdExampleField.__init__` signature or to inherited methods (value/field/error_text, base parts of `click_choose_example_ok`) can break it — re-check on every upstream `dpd_fields_examples.py` change.
  - Upstream changes to `find_cst_source_sutta_example` / `CstSourceSuttaExample` should be ported, since both files depend on them.
  - Upstream adds dedicated `click_remove_brackets()` / `click_remove_bold_tags()` methods plus `[]` / `<b>` toolbar buttons (via `remove_brackets`/`remove_bold_tags` in `dpd_fields_functions`). DPS intentionally omits these — the single `Clean` button (`click_clean_example`) already strips `<b>`/`</b>`, and adding them is out of sync scope (new DPS-tab feature). Re-evaluate only if the user requests bracket/bold tooling.
  - Upstream's example I/O (`get_fields`, stash/reload/last, swap, `clean_text` THA/THI) is tuple-based `(source, sutta, example)`. DPS replaced the entire interface with a `dict[str, ft.TextField | None]` keyed on multi-type DPS field names (sbs/dhp/pat/vib/class/discourses). Any upstream change to these signatures must NOT be ported verbatim — adapt to the DPS dict interface or skip.

---

**File**: `gui2/dps_example_stash_manager.py`
- **Category**: dps_copies
- **Sync Rule**: PORT
- **Local Changes**:
  1. `__init__` drops the required `toolkit: ToolKit` dependency (optional `toolkit=None`) and sources the path directly from `Gui2Paths().example_stash_json_path` instead of `toolkit.paths.example_stash_json_path`.
  2. `stash(key, fields_dict: dict[str, str])` stores a many-field dict, and `reload` / `last_example` return `Optional[dict[str, str]]` instead of upstream's `(source, sutta, example)` tuple.
- **Watch For**:
  - Upstream changes to `_load` / `_save` / `stash_shared_example` / `reload_shared_example` logic should be ported, adapting the tuple↔dict payload difference.
  - If upstream relocates `example_stash_json_path` on `Gui2Paths` / `toolkit.paths`, update the direct `Gui2Paths()` access here.

---

**File**: `gui2/dps_meaning_field.py`
- **Category**: dps_copies
- **Sync Rule**: PORT
- **Local Changes**:
  1. Swaps `CustomSpellChecker` → `RuSpellChecker`; `add_to_dict` calls `add_to_ru_dictionary(word)` and the add-field label is "Add Russian spelling ".
  2. Spell suggestions are written to `field.error_text` directly rather than into a separate `spell_suggestions: ft.Text` widget.
- **Watch For**:
  - Upstream `DpdMeaningField` has gained `_skip_spell_check`, `on_focus_callback`/`on_blur_callback`, `_handle_on_focus`/`_handle_on_blur`, `_remove_word_from_spell_errors`, and `color`/`helper_text` properties — evaluate porting these (adapted to `RuSpellChecker`) on the next sync.
  - If `DpdTextField` focus/blur wiring changes upstream, the direct on_focus/on_blur wiring here must follow.
  - Upstream's `_skip_spell_check` optimization + `_remove_word_from_spell_errors()` assume a separate `spell_suggestions` `ft.Text` widget and incremental error removal. DPS uses inline `field.error_text` and relies on a full re-check after add-to-dict to clear stale errors. Do NOT port `_skip_spell_check` — skipping the re-check would leave a stale misspelling error visible. Re-evaluate only if DPS migrates to a separate suggestions widget.

---
