# 2a: gui2 / tools / scripts / workflows / docs / reference data (OLD be49bffe2c2c -> NEW c54f942ee3f6)

Read-only analysis. Confidence 8/10 on facts quoted from diffs; items marked UNCERTAIN were not empirically run.

## Cross-cutting findings (read first)

1. **Flet 0.28.3 -> 1.0.1 migration is the dominant change in the gui2 group.** `pyproject.toml` pins `flet[all]==1.0.1` at NEW (local pin: `flet[all]==0.28.3`). Upstream commit 099a5e4a1 (+ 7c01efb8e, f09930cf3, d6891c48c, ba4c952d5) migrated every gui2 file. It is all-or-nothing: if shared gui2 files + pyproject are pulled verbatim, every local `gui2/dps_*.py` file (still 0.28 style) breaks at runtime (static imports still pass). Mandatory 1.0 rewrites for local DPS files are listed per section. API deltas confirmed from upstream diffs:
   - `ft.ElevatedButton` -> `ft.Button` (UNCERTAIN whether the old name is removed or only deprecated in 1.0.1; upstream renamed all 141 uses).
   - `ft.padding.* / ft.border.* / ft.alignment.*` -> `ft.Padding.* / ft.Border.* / ft.Alignment.CENTER` (module-level helpers gone).
   - `page.open(x)` / `page.close(x)` -> `page.show_dialog(x)` / `page.pop_dialog()`.
   - `Control.focus()` is a coroutine; an un-awaited call is a silent no-op -> upstream added `gui2.ui_utils.request_focus(control)`.
   - `Control.page` is read-only and raises `RuntimeError` when unmounted; `self.page = ...` inside a Control subclass fails -> upstream added `page_of`, `is_mounted` and removed every `self.page: ft.Page = ui.page` in Column subclasses.
   - `Dropdown.on_change` -> `on_select` (item picked); `TextField.error_text` renamed `error`; `border_radius/border_color/border_width` -> `border=field_border(...)`; `ft.InputBorder.OUTLINE/NONE` -> `ft.OutlineInputBorder(...)/ft.NoInputBorder()`; `helper_text` -> `helper`; `ft.app(target=)` -> `ft.run()`; keyboard/clipboard/window.close handlers async.
   - `gui2/ui_utils.py` NEW adds `page_of, is_mounted, is_inside, request_focus, field_border, compact_button_style, set_error, is_dialog_open, cancel_top_dialog`; `show_global_snackbar` uses `page.show_dialog`. (File exists locally, upstream-owned, overwritten verbatim.)
   - `gui2/dpd_fields_classes.py` NEW: `DpdTextField` coerces `value=None` to `""`, forwards `error_text` property to `error`, recolours border in `before_update`; `DpdDropdown` takes `on_change` but wires `on_select=_handle_select`; adds `track_focus`/`get_last_focused_field`.
2. **Removed/moved shared symbols that break local-only files if upstream is pulled verbatim** (verified against `git show c54f942ee3f6:<path>`):
   - `gui2/dpd_fields_functions.py`: `clean_example, clean_speech_marks, clean_text, clean_commentary, remove_brackets, remove_bold_tags` MOVED to new `tools/example_cleaning.py` (same signatures). Local importer: `gui2/dps_example_field.py:7 from gui2.dpd_fields_functions import clean_example` -> ImportError. FIX: `from tools.example_cleaning import clean_example`. (`clean_lemma_1`, imported by `gui2/dps_view.py:9`, still exists.)
   - `tools/tsv_read_write.py`: removed `append_tsv_list` and `read_tsv_as_dict_with_different_key`. Local importer: `db/lookup/help_abbrev_add_to_lookup_ru.py:14` imports `read_tsv_as_dict_with_different_key` (used at lines 31, 40) -> ImportError. Not in my domain list but found; needs a local fix (inline helper in the RU file) when `tools/tsv_read_write.py` is taken. `append_tsv_list` has no remaining importers.
   - `tools/paths.py` attrs REMOVED: `gmail_credentials_path, gmail_token_path, maha_exceptions_list, kindlegen_path, deconstructor_output_dir, deconstructor_output_json, deconstructor_output_tar_path, newsletter_processed_json, extract_cpd_tsv_path, fix_synonym_entries_json_path, additions_tsv_path`. Repo-wide grep: the only readers are upstream-owned files that upstream itself deleted/changed (newsletter_scraper, test_maha_compounds, tarball_deconstructor_output, extract_cpd, fix_synonym_entries, addition_class, add_additions_to_db, tools/tarballer.py, deconstructor_output_add_to_db.py which now uses `go_deconstructor_output_json`). No local-only (`*_ru/_sbs/_dps`, `gui2/dps_*`) file reads a removed attr from `ProjectPaths`. `exporter/kindle/kindle_exporter_ru.py:364` reads `pth.kindlegen_path` from `RuPaths` (own attr, paths_ru.py line 41), unaffected.
   - `gui2/pass2_add_view.py` NEW no longer imports `request_dpd_server` at all (only `gui2/main.py` imports `start_dpd_server` from `tools.fast_api_utils`). See pass2_add_view section.
   - `tools/fast_api_utils.py` NEW: `request_bold_def_server` REMOVED (no importers outside archive/; local `tools/fast_api_utils_dps.py` has its own copy). `request_dpd_server`/`start_dpd_server` gain `is_headless_server()` guards + `DPD_API_PORT`, and drop `--reload`.
3. **Upstream pass2_add_view NEW depends on modules that must also arrive**: `gui2.contributor_proposal, gui2.pass2_eg_manager, gui2.preview, gui2.save_router, gui2.pass2x.in_commentary_exceptions, tools.dharmamitra_client, scripts.find.missing_meanings, tools.server_mode`, `gui2.paths.Gui2Paths`. (Other domains presumably own these; flagged because the file is not self-contained.)

---

### gui2/dpd_fields.py -> gui2/dps_fields.py (inspired_only)

1. Commits: 450049d82 hover help per field; 3b41eb18f fix crash when grammar unset; 2050c6ede pass1add ai suggestions go to _add column; e8918c36f example tools hide on other-field focus; 099a5e4a1 flet 1.0 migration; 7752df052 strip synonym/var_text dupes when var_phonetic gains a word; f3684ead6 skip synonym autofill for metre names; a5d077671 #144 variant moved to var_text; 9e143f3e7 skip synonym suggestions for "name of"; 63edcd973 cached corpus load, off-thread init.
2. Changes: `variant` field removed (FieldConfig, `variant_field_change`, `variant_blur`, `synonym_variant_check`, `synonym_field_change` deleted; new `var_phonetic_blur`, `_strip_var_phonetic_dupes` using `tools.synonym_variant.assign_relationship_dict/split_field`); `page` now a lazy `@property` returning `self.ui.page` (no cached `self.page`); `request_focus`/`is_mounted` replace `.focus()` / `.page is None`; `self.db.all_*` None-guards; `CustomSpellChecker(toolkit.paths.user_dictionary_path)`; `gui2.field_help.get_field_help` tooltip on labels; `_collapse_example_tools_on_focus` wrapper.
3. Local equivalents: DPS uses `dps_field_mapping`-driven fields; no `variant`, `synonym`, lemma or `all_*` logic. SKIP: variant/synonym/db-None guards (no anchor), spellcheck constructor (local `RuSpellChecker()` no-arg), hover help (feature, DPS field set has no help text).
   PORT (forced by flet 1.0, `gui2/dps_fields.py`): `ft.ElevatedButton` x5 (lines ~183-220) -> `ft.Button`; line 126 `params["on_change"] = self._handle_sbs_chant_change` on an `ft.Dropdown` -> `params["on_select"]`. `self.view.page.update()` calls are fine (view mounted at use). `DpdTextField` used by DpsFields gains None->"" coercion for free.
4. Structural refactor check: YES - (a) lazy `page` property replacing cached `self.page` (affects `DpdFields` only; `DpsFields` is not a Control); (b) `variant` -> `var_text`/`var_phonetic` data-model refactor (no DPS impact: string `variant` absent from all `gui2/dps_*.py`).
5. Breakage if upstream pulled and local not updated: `dps_fields.py` imports `DpdTextField` (still exists, constructor unchanged), `make_meaning_combo` (tools/meaning_construction.py unchanged in range), `read_tsv_dot_dict` (unchanged). Runtime breaks only from flet 1.0 items (Dropdown `on_change` kwarg; ElevatedButton UNCERTAIN).

### gui2/dpd_fields_examples.py -> gui2/dps_example_field.py (dps copy, subclass of `DpdExampleField`)

1. Commits: 302981c50 share one example stash saver; e8918c36f tools hide on other-field focus; bf4496352 keep focus in bold box; 0044fd64d shrink buttons; f09930cf3, 7c01efb8e, 099a5e4a1 flet 1.0; 6c41156a9 import from concrete modules; d0c58287e; 5875fdc0e.
2. Changes: imports `clean_example/remove_bold_tags/remove_brackets` from `tools.example_cleaning`; `CstSourceSuttaExample`/`find_cst_source_sutta_example` imported from `tools.cst_source.models` / `.extractor` (upstream has NO `tools/cst_source/__init__.py`; local has a locally materialized one, so `from tools.cst_source import CstSourceSuttaExample` still works locally); `self.stash_manager = self.ui.toolkit.example_stash_manager`; removed `self.page = ui.page`; `border=field_border()` on all fields; `shift_enter=True,max_lines=1` on bold field; `ft.Button(style=compact_button_style())`; new `collapse_tools()`; `_handle_last_control_blur` no longer hides tools; `if clean_word:` guard before `speech_marks_manager.update_variants`; `set_error()`; `request_focus`; dialogs via `show_dialog`; counter no longer sets `border_color`.
3. Local anchors and decisions:
   - PORT (breakage): `dps_example_field.py:7` `clean_example` import -> `tools.example_cleaning`.
   - PORT (flet 1.0): line 56 `self.page: ft.Page = ui.page` in an `ft.Column` subclass -> delete (AttributeError on 1.0; `_active_page` at ~line 190 already reads `self.page`); lines 99-101 `border_color/border_radius/border_width` and 111 `border_radius` -> `border=field_border(...)`; 7x `ft.ElevatedButton` (lines 135-147) -> `ft.Button` (optional `compact_button_style()`); line 330 `self.word_to_find_field.focus()` -> `request_focus(...)`. `book_dropdown` (`ft.Dropdown`, line 91): check whether it passes `on_change` (not inspected) -> `on_select`.
   - PORT (small bug-fix parity): `if clean_word:` guard in local `_handle_last_control_blur` (anchor: its `update_variants` loop).
   - SKIP: `collapse_tools()` (only called by the `DpdFields` wrapper), shift_enter bold behaviour (DPS has no bold field), `toolkit.example_stash_manager` (DPS supplies `DpsExampleStashManager`), registry-documented intentional omissions ([] / <b> buttons) unchanged.
4. Structural refactor check: YES - cleaning helpers moved from `gui2/dpd_fields_functions.py` to `tools/example_cleaning.py`; `tools/cst_source` imports split to concrete modules (local `__init__.py` re-export keeps the local import valid); `tools/cst_source/*` parsers rewritten upstream (other domain).
5. Breakage if verbatim and local unchanged: ImportError at `from gui2.dpd_fields_functions import clean_example` (certain); `self.page` assignment AttributeError and old border kwargs on 1.0 (certain if flet 1.0 installed). Inherited base methods not overridden by the DPS subclass (`click_book_and_word`, `choose_example`, `click_choose_example_ok`) now call `set_error`, `request_focus`, `page.show_dialog`; should work since DPS builds the attrs they read, UNCERTAIN until run.

### gui2/dpd_fields_lists.py -> gui2/dps_fields_lists.py (inspired_only)

1. Commits: a5d077671 #144 variant removal.
2. Changes: `"variant"` removed from docstring numbering, `ALL`, `ROOT_FIELDS`, `COMPOUND_FIELDS`, `WORD_FIELDS`, `NO_SPLIT_LIST`.
3. Local file defines `ALL_DPS`, `VIB_FIELDS`, `CLASS_FIELDS` of `dps_*` names; no `variant`. SKIP.
4. Structural refactor check: none found (data-model rename only).
5. Breakage: none (nothing local imports `ALL/ROOT_FIELDS/...` from the upstream list module; dps files import from `gui2.dps_fields_lists`).

### gui2/dpd_fields_meaning.py -> gui2/dps_meaning_field.py (dps copy)

1. Commits: d6891c48c phase 4 threading; 7c01efb8e rounded borders; 099a5e4a1 flet 1.0.
2. Changes: `import asyncio`; `ui_utils` imports; removed `self.page: ft.Page = self.ui.page`; add-to-dict field gets `border=field_border()`; `meaning_field.focus()` -> `request_focus`; `_handle_on_focus/_handle_on_blur/_handle_spell_check` now `async`, spell check via `asyncio.to_thread`; `if self.page:` -> `is_mounted(self)`.
3. Local anchors: `dps_meaning_field.py:27` `self.page: ft.Page = self.ui.page` in a Column subclass (AttributeError on 1.0) -> PORT delete; line 90 `self.meaning_field.focus()` -> PORT `request_focus`; lines 89/107 `self.page.update()` -> PORT `is_mounted(self)` guard; add `border=field_border()` to the add-to-dict field (PORT, cosmetic: 1.0 squares corners otherwise). SKIP async + `to_thread` spellcheck (optional perf; registry already says do not port `_skip_spell_check` / incremental removal).
4. Structural refactor check: YES - handlers turned async (flet 1.0 awaits only coroutine handlers); lazy page.
5. Breakage: `self.page = ...` assignment fails on 1.0 (certain). Other imports (`DpdTextField`, `RuSpellChecker`) valid.

### gui2/pass2_add_view.py -> gui2/dps_view.py (inspired_only) AND gui2/pass2_add_view.py (modified_upstream_files)

1. Commits (31): 5497d80c9 preview before save; b504d4861 contrib server; 0092beb4b atomic contributor json writes; 3024200bf alt+x clear, ctrl+s save, alt+? shortcuts; ebd39b5d4; 6f88c0280; e1c0a1858 queue component words; 05e97f51b; 6fc9cc1dd restore last-used field on tab return; b663ccfb4; 773ac29b3; f09930cf3; ba4c952d5; 7c01efb8e; 099a5e4a1; c967a5b99; 5ccc017b9; 9292434a9 x button json import queue; 5a2309024 dharmamitra gloss; 1f60be359; b3b54e026 proofreader prompts; 3d2214acc; ee4655240 web-mode multi-user; 256249571; 5474b8763; 72a6aab2b; c196c6d45; 0369b0f3f; f3766320f.
2. Upstream changes (+779/-127): Eg queue + missing-words dialog (`Pass2EgManager`, `_show_missing_words_dialog`, `_find_missing_eg_words`, `_find_missing_component_words`, `_click_eg_*`); preview-before-save (`gui2.preview.preview_and_confirm`, `_save_previewed_word`, `test_and_add_to_db`, `gui2.save_router.save_headword`); contributor workflow (`_click_reject`, `_has_own_edit`, `_discard_own_edit`, `contributor_proposal`); X queue (`_click_x_button` async, `Pass2XManager(self.toolkit)`); `on_tab_focus` + `get_last_focused_field`/`track_focus`; action `PopupMenuButton` replacing separate buttons; async handlers; history dropdown `_update_history_dropdown(page)` + `on_select`; flet 1.0 renames; `request_dpd_server` import REMOVED.
3. dps_view.py decisions:
   - SKIP (upstream-only automation, per registry watch_for): Eg queue, missing words, X queue, reject/contributor flow, dharmamitra, shortcuts page, preview/save_router, PopupMenuButton, count tooltips.
   - PORT (forced by flet 1.0; local anchors): lines 73-75, 89-90, 107 `border_color/border_radius/border=ft.InputBorder.OUTLINE` -> `border=field_border(color=ft.Colors.BLUE_200)` (message + id fields) and `field_border()` (history dropdown); line 109 history `ft.Dropdown(on_change=...)` -> `on_select=` (line 172 is a RadioGroup: keep `on_change`); lines 118, 137, 227 `ft.padding.all(...)` -> `ft.Padding.all(...)`; line 199 `ft.alignment.center` -> `ft.Alignment.CENTER`; `ft.ElevatedButton` at 141, 148, 155, 212, 217 -> `ft.Button`. dps_view stores `self._page` (not `self.page`) so no 1.0 assignment error there; no `.focus()` / `page.open` use found by grep.
   - PORT (optional UX): `on_tab_focus` last-field restoration; wiring lives in `gui2/main.py` (other domain). UNCERTAIN whether main.py calls `view.on_tab_focus()` on every tab view (would need a DPS no-op or hasattr guard).
   - `_update_history_dropdown(self, page=None)`: `gui2/history.py` unchanged upstream; local registered callback signature stays valid. SKIP.
4. Structural refactor check: YES - save path rerouted through `gui2.preview` + `gui2.save_router.save_headword` (DPS `_click_update_db` writes RU/SBS tables directly via `dps_db_helpers`, unaffected); handlers async; button groups collapsed into a PopupMenu.
5. Breakage if upstream verbatim and dps_view not updated: `ft.alignment.center`, `ft.padding.all`, `ft.InputBorder.OUTLINE`, Dropdown `on_change` fail on flet 1.0 (certain). `gui2.toolkit.ToolKit`, `gui2.history.HistoryManager`, `gui2.mixins.PopUpMixin`, `tools.paths_dps` still resolve. `PopUpMixin.__init__` NEW calls `field_border()` and `page.show_dialog` (1.0-only).

**modified_upstream_files entry `gui2/pass2_add_view.py`:** registered local edit = `from tools.fast_api_utils_dps import request_dpd_server` replacing `tools.fast_api_utils`. NEW upstream file has NO `request_dpd_server` reference, so nothing to re-apply: the local edit is obsolete and upstream's diff does not textually conflict with it beyond that import line (removed upstream). Also, local HEAD file is stale vs OLD (`git diff be49bffe2c2c HEAD`: +54/-192; lacks OLD features: stash/unstash, `_update_count_tooltip`, `_current_addition_origin`/`_key`; has local-only `_require_page` and a coding header), so it is not "OLD + one edit". Recommendation: take NEW verbatim, then delete the `modified_upstream_files` registry entry for `gui2/pass2_add_view.py`. `tools/fast_api_utils_dps.request_dpd_server` stays in use by `dps_view.py:18/502` (keep). UNCERTAIN why HEAD lags OLD (earlier partial sync?) - check before overwrite.

### gui2/test_manager.py -> gui2/dps_test_manager.py (inspired_only)

1. Commits: 3024200bf (alt+x, ctrl+s, shortcuts page).
2. Changes: new `open_test_file(ui)` that sets `self.ui`/`self.page` then calls `_handle_open_test_file(None)`; `_handle_open_test_file(e: ControlEvent | None)`.
3. Local `_handle_open_test_file(self, e)` (line 429) is wired only to the failure-dialog button after `run_all_tests` set `self.ui` (guarded by `if self.ui`). SKIP new method (needed only by upstream's keyboard-shortcut path in main.py). PORT (flet 1.0, small): line 457 `field.focus()  # type: ignore` -> `request_focus(field)` (silent no-op on 1.0). `self.page` is a plain attribute on a non-Control (PopUpMixin) so assignment is fine; `field.error_text = ...` works on `DpdTextField` via the forwarding property but would be a dead attribute on bare `ft.TextField` (UNCERTAIN which classes `dps_field_mapping` uses).
4. Structural refactor check: none found.
5. Breakage: none at import. `InternalTestRow` import from `db_tests.db_tests_manager` (file changed in range) was not checked: UNCERTAIN, verify `git show c54f942ee3f6:db_tests/db_tests_manager.py | grep InternalTestRow`.

### tools/paths.py -> tools/paths_ru.py (RuPaths), tools/paths_dps.py (DPSPaths) (inspired_only)

1. Commits (28): 67b12b82d, 2133ed944, 34ea86748, a56f3762b, a1feba818, 0274c91ee, 37b1b363d, f77774a81, 1b975a640, a373228cf, a5265faaf, a441f918c (kindling), 01cae9412, ac0251128, f4ce2ba4e, 1ca07cae..., eda134f5c, 3d2214acc, 696eb7564, 92c1446d7, acd85c539, d0c58287e, 872495a87, 25b7a6fc4, 3946bb9c3, c0a2d7720, 26981c3f6, 897aa25ea.
2. Changes - REMOVED attrs: see cross-cutting #2. VALUE-CHANGED: `inflection_templates_path` -> `misc/inflection_templates_legacy.xlsx` (new `inflection_templates_index_path`, `inflection_templates_dir`), db_tests json paths moved to `db_tests/single/` and `fixme/`, `sya_dir` -> `resources/tipitaka.rte`, `kindlegen_path` replaced by `kindling_path = exporter/kindle/kindling-cli`. ADDED: `pts_concordance_tsv_path, citation_cff_path, docs_how_to_cite_md_path, webapp_cc_icons_path`, wordnet/nyanatiloka/pts/peu source paths, `epitaka_*`, `tpr_download_list_2_path`, `proofreader_*`, many db_tests exception paths.
3. Local: `RuPaths` and `DPSPaths` are standalone slim classes (not subclasses of `ProjectPaths`). No removed attr is read via them except `kindlegen_path` (own copy). SKIP all prunes/db_tests/epitaka/proofreader. PORT conditionally: `kindling_path = base_dir / "exporter/kindle/kindling-cli"` in `RuPaths` only if `kindle_exporter_ru.py` is ported to kindling (it still shells to kindlegen at line 364); keep `kindlegen_path` until then. `webapp_cc_icons_path` only if RU webapp shadows are ported. Decide at port time of the owning exporter.
4. Structural refactor check: YES - db_tests files regrouped (`db_tests/single/fixme/`); deconstructor tarball paths retired in favour of `go_deconstructor_output_*` (already present in OLD paths.py).
5. Breakage: pulling `tools/paths.py` verbatim does not break `RuPaths`/`DPSPaths` consumers. It breaks anything still reading `ProjectPaths().deconstructor_output_json/...` (only upstream-deleted/changed files). `resources/deconstructor_output` submodule retired upstream: local workflows still reference it (see workflows).

### tools/spelling.py -> tools/ru_spelling.py

1. Commits: 2a2c7ac27 crash when a cleared field is spell checked; 546557a2c per-user spelling file; 4f0fdd4f3 skip pali diacritic words; 4cf837809 preserve apostrophes; 5875fdc0e; 79d11c3a3.
2. Changes: `CustomSpellChecker(user_dict: Path | None)`; module `_english_words()` tokenizer (`_WORD_RE`, drops non-ASCII words, handles None); `check_sentence(sentence: str | None)`; new `has_misspellings()`; `add_to_dictionary` tolerates missing dict file.
3. Local `RuSpellChecker` is an independent class. PORT (1-line, flet 1.0 forced): `check_sentence` must accept None (`"".join(... for c in sentence)` raises TypeError on None; upstream fixed this crash) -> `sentence or ""`. `DpdTextField.__setattr__` coerces None to "" but a bare `ft.TextField` (e.g. `meaning_field`) may still hold None (UNCERTAIN). SKIP: ASCII-only tokenizer (Russian needs non-ASCII), apostrophe regex, `has_misspellings` (db tab only).
4. Structural refactor check: none for the ru file (upstream added module-level helpers only).
5. Breakage: none (`RuSpellChecker` does not import `tools/spelling.py`).

### tools/translit.py -> tools/translit_ru.py

1. Commits: 0fd5cd922 skip transliteration for text with no letters; 5875fdc0e (docstring only).
2. Change: new early-return clause `or not any(char.isalpha() for char in text)` in `auto_translit_to_roman` (numbers/punctuation-only strings returned unchanged, avoids aksharamukha warnings).
3. Local `translit_ru.py` has the same condition chain plus `or is_cyrillic(text)  # if Cyrillic`. PORT: add the `not any(char.isalpha() ...)` clause after the `is_cyrillic` line. Purely additive.
4. Structural refactor check: none found.
5. Breakage: none (standalone local file).

### tools/utils.py -> tools/utils_sbs.py

1. Commits: 6c3e91ef4 pyrefly typecheck gate; 5875fdc0e.
2. Change: module docstring; `from typing import List, TypedDict, cast`; `sum_rendered_sizes` rewritten with `cast(dict[str,int], ...)` (typing only, same runtime). `RenderedSizes` keys unchanged.
3. Local `utils_sbs.py` is a trimmed copy (adds `paragraphs_are_similar_sbs`, `sbs_example`, `see_synonyms`; omits `list_into_batches`). PORT (optional, lint gate): the `cast` version of `sum_rendered_sizes` fixes the TypedDict variable-key type error (touch-a-file-own-its-lint rule). Otherwise SKIP.
4. Structural refactor check: none found.
5. Breakage: none.

### tools/version.py -> tools/version_ru.py

1. Commits: 4b6579c66 zenodo doi constant; df11da4e2 short permalinks; b808547dd regenerate citation files on uposatha days only; 01cae9412 citations; 5875fdc0e.
2. Changes: new constants (`AUTHOR, EMAIL, WEBSITE, DOCS, GITHUB, LATEST_RELEASE, LICENSE, SHORT_WEBSITE, DOI, EXAMPLE_*`), `make_permalink`, `make_citation`, `make_db_metadata`, `update_db_version(db_path: Path, version, doi=None)` (SIGNATURE CHANGE: first arg was `ProjectPaths`; now upserts every metadata key incl. `citation`, `doi`), `release_date`, `make_citation_cff`, `update_citation_cff` (uposatha-gated). `main()` calls `update_citation_cff(pth.citation_cff_path, ...)`.
3. Local `version_ru.py` keeps its own `update_db_version(pth, version)` writing `dpd_sbs_release_version` and RU endpoints. SKIP (citation/CFF/Zenodo is DPD-specific). No importers of `tools.version.update_db_version` outside `tools/version.py` and upstream `tests/tools/test_version.py`, so the signature change is safe.
4. Structural refactor check: YES - version module split into constants + builder functions (upstream-only).
5. Breakage: none for local (`ru_release*.yml` call `tools/version_ru.py`). Side effect: `generate_components.sh` and several workflows still call upstream `tools/version.py`; NEW version also rewrites tracked `CITATION.cff` on uposatha days (needs `pth.citation_cff_path`, `UposathaManger`, both present at NEW).

### db/backup_tsv/backup_dpd_headwords_and_roots.py -> db/backup_tsv/backup_dps.py

1. Commits: b504d4861 contrib server; add2c78d1 block duplicate lemma_1; dd41af7e3 deps (drop unused pkgs); f09930cf3; ba4c952d5.
2. Changes: `check_no_duplicate_lemma_1`/`find_duplicate_lemma_1` (abort before any write); `git_commit()` rewritten from GitPython `Repo.index.add + index.commit` to `subprocess.run(["git","commit","-m","pali update","--",*files])` (path-limited so unrelated staged files are not swept in); also commits `Gui2Paths` additions/corrections/merged-lines logs.
3. Local `backup_dps.py` `git_commit_dps()` (line 167) still does `Repo.index.add([...]) + index.commit("backup russian & sbs")` which commits the WHOLE index (the hazard upstream fixed); `from git import Repo` at line 7. PORT (recommended): replace with path-limited `subprocess.run(["git","commit","-m","backup russian & sbs","--","db/backup_tsv/russian.tsv","db/backup_tsv/sbs.tsv","db/backup_tsv/ru_roots.tsv"], check=True, ...)`. Check whether upstream dd41af7e3 dropped GitPython from `pyproject.toml` at NEW (not checked: UNCERTAIN); if so `from git import Repo` breaks at import. SKIP the duplicate-lemma_1 check (DPS tables keyed by id) and the Gui2Paths logs.
4. Structural refactor check: YES - git operations moved from GitPython to subprocess.
5. Breakage: local file is standalone; breaks only if GitPython was removed (UNCERTAIN, above).

### scripts/build/db_rebuild_from_tsv.py -> scripts/build/db_rebuild_from_tsv_dps.py

1. Commits: 00308c19f freshen build/ dir.
2. Changes: typing modernization only (`list`/`tuple`/`collections.abc.Iterator`, `-> None`), dropped coding header and a commented-out confirm prompt.
3. Local file has `from typing import Iterator, List, Tuple` (line 7) and `List[...]` annotations (lines 150, 170). PORT optional (project rule: modern type hints when file is touched; behaviour-neutral). Otherwise SKIP.
4. Structural refactor check: none found.
5. Breakage: none.

### scripts/fix/character_replacer.py -> scripts/fix/character_replacer_sbs.py

1. Commits: 4d5ef2ce6 data update; acd85c539 triage find/fix/add dirs.
2. Changes: docstring rewritten; `pr.yellow_title("character replacer")`; counter incremented before print and each match prints `[green]{counter}.`; `main() -> None`; sample find/replace values (data only).
3. Local has the `joinedload`/table switch (SBS/Russian) upstream lacks. PORT optional cosmetic: match numbering + `-> None`. SKIP sample values, title. Low value.
4. Structural refactor check: none found.
5. Breakage: none.

### scripts/bash/generate_components.py -> scripts/bash/generate_components.sh (inspired_only)

1. Commits: 93bc7c456 refreshed bash scripts; 0bee25cca fast db load path, lazy corpus, decon cache; e31bdfebf; 24eed2925 wire go-generate + python add-to-db.
2. Changes: step `scripts/build/tarball_deconstructor_output.py` REPLACED by `scripts/build/deconstructor_output_add_to_db.py` (tarball script deleted upstream; add-to-db now reads `go_deconstructor_output_json`); NEW step `scripts/build/decon_cache_update.py` between `db/epd/epd_to_lookup.py` and `exporter/webapp/generate_search_index.py` (rebuilds `all_decon_no_headwords` DbInfo cache from `lookup` for fast gui2 startup); `main()` wrapper (structure only).
3. Local anchors in `generate_components.sh`: line 43 `uv run python scripts/build/tarball_deconstructor_output.py` -> PORT replace with `uv run python scripts/build/deconstructor_output_add_to_db.py` (BREAKS otherwise: script deleted upstream). PORT add `uv run python scripts/build/decon_cache_update.py` after `db/epd/epd_to_lookup.py`. Caveat: RU lookup writers (`help_abbrev_add_to_lookup_ru.py`; RPD/TPD run only in CI) should precede it; UNCERTAIN how gui2 behaves with a stale cache. SKIP `uv run pytest tests/`, `tools/logo.py`, `audio/*`, anki (local script already deviates).
4. Structural refactor check: YES - deconstructor flow changed from tarball-in-submodule to go-generate + python add-to-db; script converted to `main()`.
5. Breakage: `.sh` references the deleted `scripts/build/tarball_deconstructor_output.py` (certain after pull). `ru_release*.yml` have the equivalent problem (see workflows).

### scripts/bash/makedict.py -> scripts/bash/make_dpd.sh, scripts/bash/make_ru_dpd.sh (inspired_only)

1. Commits: 788e92046 #279 tpr stop monthly export; 93bc7c456; 1b975a640 epitaka export; 01cae9412 citations; b6c1498ce newsletter manual only; f0602dec5 #227 PEU/WordNet in every mobile release; 644c344cd.
2. Changes: `exporter/mobile/mobile_exporter.py --cone`; `exporter/tpr/tpr_exporter.py` REMOVED; `exporter/epitaka/epitaka_exporter.py` added; `scripts/build/newsletter_scraper.py` removed; `tools/docs_update_how_to_cite.py` added; `main()` wrapper.
3. Local scripts run no mobile / docs-update / newsletter steps. SKIP all additions. Owner decision (not a code port): `tpr_exporter_ru.py` is still invoked by `make_dpd.sh`, `make_ru_dpd.sh` and `ru_release.yml` ("Run TPR Exporter"); upstream stopped its monthly TPR export (#279, "keep code until year end"). UNCERTAIN whether RU/SBS TPR distribution should also stop. No symbol referenced by either local script was removed upstream.
4. Structural refactor check: none beyond `main()` wrapper.
5. Breakage: none; both reference `generate_components.sh` and local `*_ru` / `main_sbs` exporters.

### scripts/server/update-dpd.sh -> scripts/server/update-dpd-sbs.sh  ** BLOCKER **

1. Commits: b7901183b split dpdict and contrib dirs, clean up update temp files; 37912132f docs site update in script; 42ddec776 pull docs site, just ssh recipe; acd85c539.
2. Upstream: `scripts/server/update-dpd.sh` DELETED and re-added as `scripts/server_dpdict/update-dpd.sh`. It IS a move with modifications (`git diff -M30%`: `scripts/{server => server_dpdict}/update-dpd.sh`, 27+/17-); sibling dir `scripts/server_contrib/` is new. Local `scripts/server/update-dpd.sh` is identical to the OLD upstream file, is tracked, and is referenced only by `kamma/upstream_sync/registry.json:1199` (the SBS shadow's `upstream`) and kamma thread files; nothing executes it.
3. Content changes in the new file and decisions (anchors in `update-dpd-sbs.sh`):
   - `set -e` -> `set -euo pipefail`: PORT.
   - Step 1 `cd digitalpalidictionary.github.io; git pull; cd ..` (docs website): SKIP (SBS server has no docs-site checkout; RU docs deploy via `ru_static.yml`).
   - `rm -rf update_tmp; mkdir update_tmp; trap 'rm -rf update_tmp' EXIT`: PORT.
   - `uv cache prune` after `uv sync`: PORT (optional).
   - Download to `update_tmp/dpd.db.tar.xz`, `tar -xJf ... -C update_tmp`, headword-count sanity check via `uv run python -c "import sqlite3 ... SELECT COUNT(*) FROM dpd_headwords"` (exit if 0), `uv run tools/prepare_webapp_lookup.py update_tmp/dpd.db`, then atomic `mv update_tmp/dpd.db dpd.db` (replaces local `wget -qO- | tar -xJ` straight into the live path plus `[ ! -f dpd.db ]` check): PORT temp-dir + count check + atomic mv, keeping URL `https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/download/dpd.db.tar.xz`. `tools/prepare_webapp_lookup.py` (indexed case-insensitive lookup, upstream #277, commit 08035b066) does NOT exist locally: PORT that line only together with the webapp #277 change (UNCERTAIN whether `main_ru` adopts the index; if not, omit; script is idempotent).
   - Keep local specifics: `dpd-db-sbs` dir, submodule-fallback block (2b), `main_ru:app`, port 8081, local `scp`/`cp` trailer.
4. Structural refactor check: YES - server scripts reorganised into `scripts/server_dpdict/` + `scripts/server_contrib/` (+ justfile recipes `dpdict-push`, `just ssh`).
5. Recommendation: (a) repoint registry `sbs_copies["scripts/server/update-dpd-sbs.sh"].upstream` to `scripts/server_dpdict/update-dpd.sh` and refresh `local_changes`/`watch_for` (docs-site step intentionally omitted; temp-dir/atomic mv ported); (b) `git rm` local `scripts/server/update-dpd.sh` (identical to the deleted upstream file); keep `update-dpd-sbs.sh` in `scripts/server/` (no `git mv` needed; moving into `server_dpdict/` is optional and would need registry + trailer-comment updates); (c) re-run `validate_registry.py` and grep for `scripts/server/update-dpd.sh` (expect hits only in kamma/threads).

### .github/workflows/draft_release.yml -> ru_release.yml, ru_release_test.yml, ru_release_kindle.yml (inspired_only)

1. Commits (11): 788e92046 tpr stop; 5bb2af801 DPD release wording and bdhrs as author; ce0683c0e submodule push job behind uposatha gate; befcebd76 kindling warnings; ffc74fd02 releases use personal token, macos-latest; a441f918c kindling; 238d741cc audio authenticate api calls; 812588f3f release pipeline audit; e31bdfebf; cca539dd3 builds dispatched ref; 24eed2925.
2. Upstream changes and RU relevance:
   - Deconstructor: REMOVED "Unzip deconstructor_output" step (submodule `resources/deconstructor_output` retired, 897aa25ea); "Run Deconstructor" split into "Generate Deconstructor" (`go run go_modules/deconstructor/main.go`) + "Add Deconstructor to db" (`scripts/build/deconstructor_output_add_to_db.py`). Local `ru_release.yml`, `ru_release_test.yml`, `ru_release_kindle.yml` lines ~53-60 still `cd resources/deconstructor_output; tar -xzvf ...` and line ~155-162 only run add-to-db (setup-go step already present, line ~77-80). PORT in all three: delete Unzip step; add Generate Deconstructor go-run step before add-to-db (required once `.gitmodules` drops the submodule and add-to-db reads `go_deconstructor_output_json`).
   - Audio index: `env: GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}` added to "Download Audio Index" (238d741cc). PORT in all three (ru_release.yml ~line 224).
   - Kindle: NEW "Install kindling" step (pinned v0.45.6, sha256-checked `kindling-cli-linux` download to `exporter/kindle/kindling-cli`) before Export Kindle & ePub. PORT only together with a kindling-based `kindle_exporter_ru.py` (currently kindlegen), in `ru_release.yml` and `ru_release_kindle.yml`. SKIP until then.
   - Removed "Set up Python" (setup-python@v6, 3.12): optional (uv manages python); low value.
   - Actions bumps (upload-artifact v6->v7, download-artifact v6->v8, softprops/action-gh-release v2->v3, macos-14 -> macos-latest): SKIP; RU workflows have no macOS job and use `actions/create-release@v1` / `upload-release-asset@v1` (different structure; modernising is out of sync scope).
   - Release author token: RU already passes `GITHUB_TOKEN: ${{ secrets.GH_PAT }}` to create-release/upload steps: nothing to port.
   - New dispatch inputs `push_submodules`/`push_dry_run` and submodule gate/sync/collect/push job (fdg_dpd, bw2, sc-data, uposatha-only): SKIP (RU has its own "Sync all submodules"/"Update All Submodules" steps).
   - "Check all release assets exist" step: SKIP (asset names differ: `ru-dpd-*`, `dpd+sbs-*`).
   - TPR exporter step removed upstream (#279): RU keeps "Run TPR Exporter" (owner decision, see makedict).
3. Structural refactor check: YES - release workflow gained submodule push job and gating; deconstructor produced in CI via go instead of unzipped from the submodule.
4. Breakage if ignored: RU workflows fail at "Unzip deconstructor_output" once the sync removes the submodule (certain); add-to-db reads the wrong/missing json until the go-run step is added.

### mkdocs.yaml -> mkdocs_ru.yaml (inspired_only)

1. Commits: 6af221412, dc1b1b703, 455d4176e, 196f0e734, 1566873cc, ee8f289eb, 01cae9412.
2. Nav additions (6 lines): Install `KOReader: install/koreader.md`; Integrations `ePitaka: integrations/epitaka.md`, `Sutamaya: integrations/sutamaya.md`, `Add Your App: integrations/add_your_app.md`; Contributing `Resources: contributing/resources.md`; top-level `How to Cite: how_to_cite.md`.
3. Local `mkdocs_ru.yaml` (docs_dir `docs_rus`) has none and `docs_rus/` has none of these pages (all six are pending in `kamma/upstream_sync/docs_translation_queue.md`). PORT nav entries (Russian labels) only as each page lands in `docs_rus` (translation or no-translate redirect), otherwise mkdocs reports missing nav files. Do not add nav before the pages exist.
4. Structural refactor check: none found.
5. Breakage: none; upstream `mkdocs.yaml` is not used by the local build.

### shared_data/reference/{abbreviations.tsv, abbreviations_other.tsv, bibliography.tsv} -> shared_data/reference_ru/ (RU data copies)

Computed by parsing both revisions as TSV (csv module, quote-agnostic).
1. Commits: f1b108053 (normalize ṁ to ṃ), 4d5ef2ce6 (data update), 1abb97180 (restore Malalasekera row), 532677892 (add Levman and Oberlies).
2. `abbreviations.tsv`: same 225 rows, same 7 columns (`abbrev, meaning, pāli, example, explanation, ru_abbrev, ru_meaning`; headers match local). Only semantic change: row `nt`, column `pāli`: `napuṃsaka; napuṁsakaliṅga` -> `napuṃsaka; napuṃsakaliṅga`. The 225+/225- git diff is mostly quoting style (OLD fully quoted, NEW unquoted). RU translation scope: none (ru_abbrev/ru_meaning unchanged). Local file still has that one old `ṁ`.
3. `abbreviations_other.tsv`: 1090 rows, 5 columns, no RU columns locally. Only change: ṁ->ṃ in `meaning` for 34 rows, 3 of which also change the key `abbreviation` (`PTS Gavaṁ->Gavaṃ`, `PTS Saṁy.->Saṃy.`, `PTS Vaṁs. Br.->Vaṃs. Br.`). Verified no non-ṁ change. RU translation scope: none; local has 34 `ṁ` meaning cells to normalise.
4. `bibliography.tsv`: 80 -> 85 data rows, same 13 columns. Added 5 rows: Levman x2 (`Pāli and Buddhism: Language and Lineage`; `Pāli, the Language: The Medium and Message`), Malalasekera (`Dictionary of Pāli Proper Names`, restored), Oberlies x2 (`Pāli Grammar ... Vol. I` and `Vol. II`); category heading row renamed `Academic Papers (incomplete)` -> `Academic Books & Papers (incomplete)` (Deokar row). No rows removed. No RU columns: English data copied as-is, so RU translation scope = none (local heading is also English).
5. Decision PORT via local text manipulation (no LLM, per Economy rule): in `reference_ru/abbreviations.tsv` ṁ->ṃ in the `pāli` column of `nt`; in `reference_ru/abbreviations_other.tsv` ṁ->ṃ (and Ṁ->Ṃ if any) in `abbreviation` and `meaning` columns (34 cells, 3 keys); in `reference_ru/bibliography.tsv` append the 5 rows and rename the Deokar category heading. Do not touch `ru_abbrev`/`ru_meaning`. Keep local quoting. Watch: `db/lookup/help_abbrev_add_to_lookup_ru.py` keys by abbreviation columns, so normalising English `abbreviation` keys matches upstream's own normalisation. Structural refactor check: none found. Breakage: none.

---
## Summary of PORT items
- Mandatory (flet 1.0 / removed symbols): dps_example_field (import `clean_example` from `tools.example_cleaning`; drop `self.page=`; border kwargs; Button; request_focus), dps_meaning_field (drop `self.page=`; request_focus; is_mounted), dps_fields (Button x5; Dropdown `on_select`), dps_view (Button, Padding, Alignment, border kwargs, Dropdown `on_select`), dps_test_manager (`request_focus`). Also `gui2/dps_field_mapping.py` `border_color/border_radius` (outside my list, found in grep).
- Mandatory scripts/CI: `generate_components.sh` (tarball -> add_to_db; add decon_cache_update), `ru_release*.yml` (remove Unzip deconstructor_output; add go-run Generate Deconstructor).
- Recommended: translit_ru `not any(isalpha)`; ru_spelling None guard; backup_dps path-limited commit; update-dpd-sbs.sh temp-dir/atomic mv/headword check/pipefail; reference_ru data (ṁ->ṃ, 5 bibliography rows, Deokar category rename); Audio Index GITHUB_TOKEN env.
- Registry: repoint `scripts/server/update-dpd-sbs.sh` upstream; delete `modified_upstream_files` entry for `gui2/pass2_add_view.py` after taking NEW verbatim; `git rm` local `scripts/server/update-dpd.sh`.
- Extra breakage found outside domain: `db/lookup/help_abbrev_add_to_lookup_ru.py` imports `read_tsv_as_dict_with_different_key` (removed upstream).
