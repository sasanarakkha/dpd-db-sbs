# Upstream sync analysis: goldendict / grammar / deconstructor / tpr / families (be49bffe2c2c..c54f942ee3f6)

Method: `git diff` per file, local files read at HEAD, registry entries read, import symbols of every local target verified against `git show c54f942ee3f6:<path>` with an AST script. Nothing edited in the repo.

Verified import result: for all 12 local targets (+ roots/epd/variant shadows, paths_ru, paths_dps, utils_sbs, tools_for_ru_exporter, data_classes_dps), every `from tools.* / exporter.* / db.*` symbol still exists at NEW (only "missing" ones are local-only models Russian/SBS/Tamil, which is expected). So no ImportError from the shared modules in this domain. One breakage found OUTSIDE the listed targets (see "Cross-cutting").

## Cross-cutting findings

- BREAKAGE (verified): upstream `tools/tsv_read_write.py` REMOVES `append_tsv_list` and `read_tsv_as_dict_with_different_key`. Local `db/lookup/help_abbrev_add_to_lookup_ru.py` line 14 imports `read_tsv_as_dict_with_different_key` (used lines 31, 40). Pulling tools/tsv_read_write.py verbatim breaks that script (ImportError) unless the function is kept locally or the script is changed. Not used by any goldendict shadow.
- Upstream `tools/configger.py` removes `config_test_section` and `print_config_settings` (grep: no other local user). `config_test_option` stays. Adds DEFAULT_CONFIG keys `dictionary.show_tbw="no"`, `tpr.make_beta="no"`, etc. `config_test` auto-writes the default for missing keys, so a local config.ini lacking `show_tbw` does not crash.
- Upstream `tools/version.py` rewritten (AUTHOR="Bodhirasa Bhikkhu", DOI, EXAMPLE_ID, EXAMPLE_LEMMA, make_citation, make_permalink, ...). Local `tools/version_ru.py` exists (not in my domain). `export_help.add_citation` imports these from `tools.version`, which imports `db.db_helpers`, `tools.uposatha_day` etc. (heavy-ish imports).
- Upstream `tools/paths.py` adds `tpr_download_list_2_path` (resources/tpr_downloads/download_source_files/download_list_2.json). Local `tools/paths_ru.py` has only `tpr_with_rus_path`; RU tpr shadow uses `g.pth.tpr_download_list_path` (still exists upstream).
- Upstream `db/models.py`: new `SuttaInfo.s_4nt_link` cached_property (+ _S4NT_* constants); `dv_exists` no longer counts `dv_pts`; `dv_pts` column remains. Local `db/models.py` has NO `s_4nt_link` (grep). Templates referencing `d.su.s_4nt_link` need models.py synced first (domain of another analyst); without it the Jinja condition is just falsy (Jinja undefined), no crash.
- Upstream `tools/utils.py` only cast/typing changes (RenderedSizes sum) - runtime identical.
- Unchanged upstream (no diff in range): exporter/goldendict/data_classes.py, exporter/deconstructor/data_classes.py, exporter/grammar_dict/data_classes.py, exporter/goldendict/helpers.py, exporter/jinja2_env.py, export_epd.py, export_roots.py.

---

### exporter/goldendict/export_dpd.py -> export_dpd_ru.py, export_dpd_sbs.py (inspired_only)

1. Commits: 326612139 "#252 sutta info: add show_tbw config toggle for TBW Legacy links"; 6c3e91ef4 "#157 pyrefly ..." (cast->constructor change likely from here/other; UNCERTAIN which commit).
2. Changes:
   - `DpdHeadwordRenderDataBase` gains `show_tbw: bool`.
   - `_worker_init`: builds `jinja_env = get_jinja2_env(...)`, sets `jinja_env.globals["show_tbw"] = render_data["show_tbw"]` (with a pyrefly ignore comment), then `DpdHeadwordRenderData(**render_data, pth=path, jinja_env=jinja_env)` instead of the dict literal.
   - `generate_dpd_html`: `show_tbw: bool = config_test("dictionary", "show_tbw", "yes")` and `"show_tbw": show_tbw` in render_data dict.
3. Local:
   - export_dpd_ru.py: `DpdHeadwordRenderDataBase` line 61-65 (show_id), `_worker_init` line 171-190 (uses `cast(DpdHeadwordRenderData, {**render_data, "pth":..., "jinja_env": get_jinja2_env("exporter/goldendict/ru_components/templates")})`), `generate_dpd_html` show_id at line 316, render_data dict at 338-342. PORT: add `show_tbw` to TypedDict, config read, render_data dict, and set `jinja_env.globals["show_tbw"]` in `_worker_init` (keep local template dir and keep/adjust the cast; upstream switched to the TypedDict constructor, optional).
   - export_dpd_sbs.py: same anchors (TypedDict line 63-67, `_worker_init` 188-205 with sbs_templates, `show_id` line 340, render_data 357-361). PORT same.
   - NOTE: without the template change, the global is unused; with only the template change and no global, `show_tbw` is undefined -> falsy -> TBW Legacy row silently disappears. Port both together.
4. Structural refactor: none found (small additive). The cast->constructor swap is typing-only.
5. Breakage if shadow not updated: none (nothing removed/renamed upstream in export_dpd.py; shadows do not import it).

### exporter/goldendict/export_help.py -> export_help_ru.py, export_help_sbs.py (inspired_only)

1. Commits: 01cae9412 "#262 citations: how to cite docs, generated cff, cite entry"; df11da4e2 "#262 cite: short permalinks..."; 4b6579c66 "#262 citations: zenodo doi as a constant" (touch version constants); a5249fd37 "#262 citation: feedback how-to-cite link..." (UNCERTAIN exactly which touched export_help.py; the net diff is one feature).
2. Change: new imports (`tools.configger.config_read`; `tools.version` AUTHOR, DOI, EXAMPLE_ID, EXAMPLE_LEMMA, make_citation, make_permalink); `generate_help_html` calls `citation = add_citation(header)`, extends `help_data_list`, adds size; new function `add_citation(header) -> list[DictEntry]` building a "cite" entry (word="cite", synonyms ["dpd cite","cite","citation","how to cite","version"]) with English HTML ("How to Cite DPD", example entry citation, permalink hint, how_to_cite link).
3. Local:
   - export_help_ru.py: `generate_help_html` extends at lines 79-99 (abbrev, help, bibliography, thanks, abbrev_other); no citation. Imports lines 3-20.
   - export_help_sbs.py: same structure lines 73-93.
   - Decision: PORT-or-SKIP is a product call. Citation text names Bodhirasa and DPD English version/DOI and describes the English feedback block's permalink line; for RU the feedback has no ID/permalink line, so the text would be inaccurate. Recommend SKIP for RU (or port with RU-translated text and localized version via `version_ru`, UNCERTAIN - needs owner decision). SBS: PORT is straightforward (SBS feedback is English and mirrors upstream), if SBS feedback also gets the Permalink line (see JS section).
4. Structural refactor: none found.
5. Breakage if not updated: none (shadows do not import export_help). Note `tools.version` import chain only matters if ported.

### exporter/goldendict/main.py -> main_ru.py, main_sbs.py (inspired_only)

1. Commits: part of the author-name sweep (commit(s) changing "Bodhirasa" -> "Bodhirasa Bhikkhu"; exact subject not isolated, UNCERTAIN).
2. Change: `prepare_export_to_goldendict_mdict`: description "by Bodhirasa" -> "by Bodhirasa Bhikkhu"; `DictInfo.author` "Bodhirasa" -> "Bodhirasa Bhikkhu".
3. Local:
   - main_ru.py line ~157: author="Дост. Бодхираса, переведено Бхиккху Дэвамитта" (Russian, no English description). Name change: SKIP or optional RU wording change ("Бхиккху" suffix) - owner decision; UNCERTAIN.
   - main_sbs.py lines 178-187: `<p>Digital Pāḷi Dictionary by Bodhirasa</p>` and author="Bodhirasa, SBS fork by Devamitta". PORT (-> "Bodhirasa Bhikkhu" in both description and author).
4. Structural refactor: none found.
5. Breakage: none.

### exporter/goldendict/templates/dpd_headword.jinja -> ru_components/templates/dpd_headword_ru.jinja, sbs_templates/dpd_headword_sbs.jinja

NOTE: local filenames are `dpd_headword_ru.jinja` / `dpd_headword_sbs.jinja` (not `dpd_headword.jinja`).

1. Commits: 326612139 (#252 show_tbw), 9ab176943 "#251 sutta info: add s.4nt.org link to sutta central section", 1ca07cae2 "suttas: pts refs from pts-cst concordance, drop dv pts source".
2. Changes:
   - `{% if d.su.tbw_legacy %}` -> `{% if d.su.tbw_legacy and show_tbw %}`.
   - New block after the SC Voice block, before the BJT block: `{% if d.su.s_4nt_link %}` row with th "s.4nt.org" and td link `{{ d.su.s_4nt_link }}`.
   - DV section reorganized: comment "<!-- DV catalogue -->" -> "<!-- PTS concordance -->"; inside `{% if not is_vagga and not is_samyutta %}`, the PTS row now has its own heading row "Pali Text Society" under `{% if d.su.dv_pts %}`; then a separate "<!-- DV catalogue -->" `{% if d.su.dv_exists %}` heading "Dhamma Vinaya Tools: Sutta Catalogue" (heading no longer wraps the PTS row).
3. Local:
   - dpd_headword_ru.jinja: `tbw_legacy` line 425; SC Voice block ends ~line 466, bjt line ~469 (insert s_4nt there); DV block at lines 662-690 (dv_exists heading 666, dv_pts 674). PORT all three. Headings here are English/untranslated already (the RU template keeps "Dhamma Vinaya Tools: Sutta Catalogue", "General Theme"), so new strings "s.4nt.org" (a proper name, no translation) and "Pali Text Society" can stay English for consistency (or translate -> "Общество Пали Текст"; optional, owner call).
   - dpd_headword_sbs.jinja: `tbw_legacy` line 440; SC Voice ends ~line 483, bjt ~486; DV block at lines 681-700. PORT all three, English as is.
   - The `show_tbw` condition needs the export_dpd_*.py port above.
   - `s_4nt_link` needs db/models.py sync (not present locally).
4. Structural refactor: none; DV/PTS reordering is local to the block.
5. Breakage if template not updated: none (additive; stale template just lacks new rows and TBW Legacy stays always-on).

### exporter/goldendict/javascript/{family_compound,family_idiom,family_root,family_set,feedback}_template.js -> ru_components/javascript/ru_*_template.js (RU) [+ sbs_templates/javascript/sbs_*_template.js for SBS]

NOTE: local names are `ru_family_*_template.js`, `ru_feedback_template.js`; SBS: `sbs_family_*_template.js`, `sbs_feedback_template.js`. Function names are prefixed (`ru_makeFeedback`, `ru_superScripter`, `sbs_makeFeedback`).

1. Commits: 904891e2f "families: headings agree in number with each family's count"; 3ae112bf9 "feedback: sync wording across web and goldendict, add cross-refs"; df11da4e2 (permalink in feedback); a5249fd37 (how-to-cite link); 196f0e734 "#271 contributions: add offer-help form, repoint get-involved links".
2. Changes:
   - family_compound: `const compounds = fc.count == 1 ? "compound which contains" : "compounds which contain";` used in both branches; single-item branch now also closes `</p>` (previously missing).
   - family_idiom: same with `fi.count == 1 ? "idiomatic expression which contains" : "idiomatic expressions which contain"`, plus `</p>` fix in single branch.
   - family_root: `${fr.count == 1 ? "word belongs" : "words belong"} to the root family`.
   - family_set: single branch closes `</p>` (`...<b>${setName}</b></p>`); no wording change.
   - feedback_template.js: header comment (wording lives in 3 places); new line after ID: `<p>Permalink <a class="dpd-link" href="https://dpdict.net/${data.id}" target="_blank">https://dpdict.net/${data.id}</a></p>`; "Visit the DPD docs website" -> "Read the docs" with text ". Get more detailed information about installation on your devices, upgrades, advanced settings and features."; "Help with coding" and "Help with Pāḷi" mailto blocks REPLACED by "How to cite" (https://digitalpalidictionary.github.io/how_to_cite/, ". DPD is revised every month, so please cite the version you used.") and "Contribute to DPD" (https://digitalpalidictionary.github.io/contributing/#offer-your-help, ". Contribute your time, skills or resources to the project. Please use the form.").
3. Local RU (ru_components/javascript):
   - ru_family_compound_template.js lines 25 and 31: Russian text, singular/plural selection is by list length not count ("составных слов(а) содержат" / "составное слово содержащее"); both branches lack closing `</p>` in single branch (same latent bug upstream fixed). PORT the `</p>` fix. Number-agreement: PORT requires RU wording (needs translation): choose Russian forms by `count` (1 / 2-4 / 5+), e.g. current "(а)" hack. Needs RU translation, suggest owner approval.
   - ru_family_idiom_template.js lines 25/31: same ("идиом(ы) содержат" / "идиома содержащая"). PORT `</p>` fix; wording needs RU translation.
   - ru_family_root_template.js lines 9-12: "слов(а) принадлежат к семье корня" - agreement wording needs RU translation; Russian already uses "(а)" hack; effectively SKIP or translate.
   - ru_family_set_template.js lines 27/33: "слов в группе" - PORT `</p>` fix (no wording).
   - ru_feedback_template.js: already fully divergent Russian text (no ID line, no Help-with-coding/Pāḷi blocks; has own "Помощь проекту" mailto to devamitta@sasanarakkha.org, "Читать документацию" link to devamitta.github.io/dpd.rus). Upstream feedback changes: SKIP (permalink dpdict.net/<id> and how-to-cite point at upstream DPD English version, not RU). Optional: RU "How to cite"/permalink - UNCERTAIN/owner decision.
4. Local SBS (sbs_templates/javascript):
   - sbs_family_compound_template.js lines 25/31, sbs_family_idiom_template.js 27/34, sbs_family_root_template.js line 10, sbs_family_set_template.js 27/32: English identical to old upstream. PORT all four verbatim (count-based agreement + `</p>`). `sbs_family_word_template.js` unchanged upstream.
   - sbs_feedback_template.js lines 5 (ID), 46 (Visit the DPD docs website), 51 (Help with coding), 56 (Help with Pāḷi): PORT with sbs_ naming preserved; check the SBS file's own local-only content is retained (UNCERTAIN: I did not diff the SBS feedback against upstream line by line beyond those anchors).
5. Structural refactor: none; note unclosed-`</p>` fix is a real HTML correctness fix.
   Breakage if not updated: none (JS is self-contained).

### exporter/grammar_dict/grammar_dict.py -> grammar_dict_ru.py

1. Commits: author-name sweep (exact subject not isolated, UNCERTAIN).
2. Change: `DictInfo.author="Bodhirasa"` -> `"Bodhirasa Bhikkhu"` in `prepare_gd_mdict_and_export`.
3. Local: grammar_dict_ru.py line 156 author="Дост. Бодхираса, переведено Дэвамитта Бхиккху". SKIP (Russian literal, intentionally localized); optional RU wording tweak is owner's call.
4. Structural: none. 5. Breakage: none.

### exporter/deconstructor/deconstructor_exporter.py -> deconstructor_exporter_ru.py

1. Commits: author-name sweep (UNCERTAIN subject).
2. Change: `DECONSTRUCTOR_DESCRIPTION` "by Bodhirasa" -> "by Bodhirasa Bhikkhu"; `_make_dict_info` author likewise.
3. Local: deconstructor_exporter_ru.py lines 114 and 145 author="Дост. Бодхираса" (Russian); no `DECONSTRUCTOR_DESCRIPTION` constant in RU (own strings). SKIP (localized literals).
4. Structural: none. 5. Breakage: none (data_classes.py unchanged).

### exporter/tpr/tpr_exporter.py -> tpr_exporter_ru.py

1. Commits: f4ce2ba4e "tpr: use jsdelivr mirror URL, fix stale list-index lookup"; 49f027efa "tpr exporter: make daily beta opt-in, skip pipeline when disabled"; 6c3e91ef4 pyrefly typing. Commit 788e92046 "#279 tpr: stop monthly export, keep code until year end" touches ONLY workflows/docs/kamma (draft_release.yml, docs/integrations/tpr.md, kamma/tech.md): it does NOT change tpr_exporter.py code.
2. Changes in tpr_exporter.py:
   - `tpr_data_list: list[dict[str, str | int]]` typing.
   - New `_tpr_download_url(filename)` -> `https://cdn.jsdelivr.net/gh/bksubhuti/tpr_downloads@master/release_zips/<file>` (jsdelivr, since raw.githubusercontent is blocked in Myanmar).
   - New `_update_download_list(list_path, entry_info, url_suffix)`: finds entry by `url.endswith(url_suffix)` instead of hard-coded `download_list[12]` / `[33]` indices; skips with pr.red if missing.
   - `copy_zip_to_tpr_downloads(g, version)`: signature now takes `version`; updates both `g.pth.tpr_download_list_path` and new `g.pth.tpr_download_list_2_path`; early return after `pr.no("no repo")`.
   - `main()`: decides `version` up front: `UposathaManger.uposatha_today()` -> "release", elif `config_test("tpr","make_beta","yes")` -> "beta", else prints "no release today, beta disabled in config.ini" and returns before the pipeline.
3. Local tpr_exporter_ru.py: `copy_zip_to_tpr_downloads(g)` (line 333) has its own RU logic: only one asset "DPD with Russian" via `update_tpr_download_list_ru(download_list, info)` (line 326; removes entries named "DPD with Russian", then appends - NO index-based lookup, so the "stale list-index" bug does not exist here); writes only `tpr_download_list_path`; `main()` (line 381) has no uposatha/beta logic, only `make_tpr` gate and `tpr_release_path.exists()`.
   - SKIP: beta/uposatha version decision, `_update_download_list`, index fix (not applicable; RU appends by name).
   - PORT candidate (UNCERTAIN, owner decision): jsdelivr URL for the RU asset URL (check `dpd_with_rus_info["url"]` at ~line 360-372 - I did not read what host it uses), and `list[dict[str, str | int]]` typing if pyright demands it. Also optionally writing `download_list_2.json` - would require adding `tpr_download_list_2_path` use (exists in upstream `tools/paths.py`, comes for free when paths.py is pulled).
4. Structural refactor check: YES (moderate): `copy_zip_to_tpr_downloads` restructured (version param, helper functions, two list files), `main()` flow change. Not applicable to RU logic as described, but registry watch_for should note the new signature.
5. Breakage if shared modules pulled and RU shadow not updated: none (RU shadow imports verified; only uses `g.pth.tpr_download_list_path`, `tpr_sql_file_path`, which remain). Upstream `make_tpr` stays config-gated; with #279 upstream stopped running TPR in CI, RU only runs it locally (config.ini has `make_tpr = no`).

### scripts/build/families_to_json.py -> families_to_json_ru.py

1. Commits: 00308c19f "#157 scripts: freshen build/ dir, archive dead script, fix bugs"; 6c3e91ef4 pyrefly.
2. Changes: expanded module docstring; `from collections.abc import Mapping`; `json_dumper(filepath, data: Mapping[str, object])` now serializes `json.dumps(dict(data), ...)` with comment; one-line docstrings on `export_family_compound/idiom/root/set/word`. No logic change.
3. Local families_to_json_ru.py: docstring line 3 "Export family data to JSON."; `json_dumper(filepath, data: dict[str, object])` line 52 (same code as old upstream). Optional PORT of Mapping signature only if local pyright/pyrefly flags dict invariance on callers (upstream did it for covariance); docstrings optional. Behavior-neutral. No RU wording involved.
4. Structural: none. 5. Breakage: none.

### db/families/family_set.py -> db/families/family_set_ru.py

1. Commits: 904891e2f "families: headings agree in number with each family's count" (UNCERTAIN: family_set change could be a different commit; diff is one hunk).
2. Changes: new module constant `SMALL_SET_EXCEPTIONS: tuple[str, ...] = ("vaggas of Saṃyutta Nikāya",)` above `add_sf_to_db`; condition `if count < 3:` -> `if count < 3 and not sf.startswith(SMALL_SET_EXCEPTIONS):` (short saṃyuttas legitimately have 1-2 vaggas).
3. Local family_set_ru.py: `add_sf_to_db`-equivalent near lines 200-221, with `if count < 3: errors_list.append(sf)` at lines 213-214 (in-place update variant). PORT both (constant + condition). Caveat: `sf` keys in the RU flow are the English set names from `sets_dict` (same keys as upstream - the loop uses `sets_dict[sf]["set_ru"]` as RU name), so prefix match applies unchanged; verify empirically (UNCERTAIN).
4. Structural: none. 5. Breakage: none (family_set_ru does not import family_set).

### tools/degree_of_completion.py -> tools/degree_of_completion_ru.py

1. Commits: 5875fdc0e "#157 tools: clean up and refactor tools/ folder".
2. Change: module docstring added only; no code change. (Same for tools/exporter_functions.py: docstring only.)
3. Local degree_of_completion_ru.py imports `degree_of_completion` from `tools.degree_of_completion` and does `.replace(' class="gray"', "")`. SKIP (docstring only; behavior unchanged, regex still valid).
4. Structural: none. 5. Breakage: none.

### Other shared upstream modules (breakage check)

- tools/goldendict_exporter.py (commit 49396e109 "#157 goldendict: force per-glossary tmp dir to fix slob cleanup race", 5875fdc0e): `from pyglossary import Glossary` -> `from pyglossary.glossary_v2 import Glossary`; `create_glossary` now `Glossary()` + `glos.setInfo(key, value)` loop + `_ = glos.tmpDataDir`; `copy_dir`: `goldendict_pth: Path | None`. Public symbols imported by shadows (`DictEntry`, `DictInfo`, `DictVariables`, `export_to_goldendict*` etc.) unchanged (verified). Requires pyglossary version supporting `glossary_v2` (UNCERTAIN: check uv.lock/pyproject pyglossary pin when syncing dependencies; if lock not pulled, import may fail).
- tools/exporter_functions.py: docstring only.
- exporter/goldendict/data_classes.py, exporter/deconstructor/data_classes.py, exporter/grammar_dict/data_classes.py: no change in range.
- tools/utils.py: typing-only; `RenderedSizes`, `default_rendered_sizes`, `sum_rendered_sizes`, `squash_whitespaces`, `extract_body` etc. still present.
- tools/tsv_read_write.py: see BREAKAGE in Cross-cutting (db/lookup/help_abbrev_add_to_lookup_ru.py).
