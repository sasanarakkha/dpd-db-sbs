# Upstream Sync Preparation Report

## Upstream Range
- From: `0ea5883380f56b682cf8574043afb8e66cca3260`
- To: `518672a65fa3ea7c36c4c754dc5276bb41f92da7`

## Registry Validation Status
OK: Registry is valid.

## SMD Coverage Status
OK: SMD coverage is complete and rubric-compliant.

## Modified - Tracked Files
- AGENTS.md
- db/models.py
- exporter/webapp/data_classes.py
- pyproject.toml

## Modified - Shadow Sources
- `db/backup_tsv/backup_dpd_headwords_and_roots.py` -> shadows: scripts/backup/backup_dps.py
- `db/epd/epd_to_lookup.py` -> shadows: db/rpd/rpd_to_lookup.py, db/tpd/tpd_to_lookup.py
- `db/families/family_compound.py` -> shadows: db/families/family_compound_ru.py
- `db/families/family_idiom.py` -> shadows: db/families/family_idiom_ru.py
- `db/families/family_root.py` -> shadows: db/families/family_root_ru.py
- `db/families/family_set.py` -> shadows: db/families/family_set_ru.py
- `db/families/family_word.py` -> shadows: db/families/family_word_ru.py
- `db/lookup/help_abbrev_add_to_lookup.py` -> shadows: db/lookup/help_abbrev_add_to_lookup_ru.py
- `exporter/deconstructor/deconstructor_exporter.py` -> shadows: exporter/deconstructor/deconstructor_exporter_ru.py
- `exporter/goldendict/data_classes.py` -> shadows: exporter/goldendict/data_classes_dps.py
- `exporter/goldendict/export_epd.py` -> shadows: exporter/goldendict/export_rpd.py
- `exporter/goldendict/templates/dpd_header.jinja` -> shadows: exporter/goldendict/ru_components/templates/, exporter/goldendict/sbs_templates/
- `exporter/goldendict/templates/dpd_headword.jinja` -> shadows: exporter/goldendict/ru_components/templates/, exporter/goldendict/sbs_templates/
- `exporter/goldendict/templates/dpd_root.jinja` -> shadows: exporter/goldendict/ru_components/templates/, exporter/goldendict/sbs_templates/
- `exporter/goldendict/templates/dpd_see.jinja` -> shadows: exporter/goldendict/ru_components/templates/, exporter/goldendict/sbs_templates/
- `exporter/goldendict/templates/dpd_spelling_mistake.jinja` -> shadows: exporter/goldendict/ru_components/templates/, exporter/goldendict/sbs_templates/
- `exporter/goldendict/templates/dpd_variant_reading.jinja` -> shadows: exporter/goldendict/ru_components/templates/, exporter/goldendict/sbs_templates/
- `exporter/goldendict/templates/epd.jinja` -> shadows: exporter/goldendict/ru_components/templates/, exporter/goldendict/sbs_templates/
- `exporter/goldendict/templates/help_abbrev.jinja` -> shadows: exporter/goldendict/ru_components/templates/, exporter/goldendict/sbs_templates/
- `exporter/goldendict/templates/help_abbrev_other.jinja` -> shadows: exporter/goldendict/ru_components/templates/, exporter/goldendict/sbs_templates/
- `exporter/goldendict/templates/help_help.jinja` -> shadows: exporter/goldendict/ru_components/templates/, exporter/goldendict/sbs_templates/
- `exporter/grammar_dict/grammar_dict.py` -> shadows: exporter/grammar_dict/grammar_dict_ru.py
- `exporter/kindle/epub/OEBPS/Text/titlepage.xhtml` -> shadows: exporter/kindle/ru_components/epub/
- `exporter/kindle/kindle_exporter.py` -> shadows: exporter/kindle/kindle_exporter_ru.py
- `exporter/tbw/tbw_exporter.py` -> shadows: exporter/tbw/tbw_exporter_ru.py
- `exporter/tpr/tpr_exporter.py` -> shadows: exporter/tpr/tpr_exporter_ru.py
- `exporter/webapp/data_classes.py` -> shadows: exporter/webapp/data_classes_ru.py
- `exporter/webapp/main.py` -> shadows: exporter/webapp/main_ru.py
- `exporter/webapp/preloads.py` -> shadows: exporter/webapp/preloads_ru.py
- `gui2/dpd_fields_examples.py` -> shadows: gui2/dps_example_field.py
- `scripts/build/db_rebuild_from_tsv.py` -> shadows: scripts/build/db_rebuild_from_tsv_dps.py
- `scripts/build/families_to_json.py` -> shadows: scripts/build/families_to_json_ru.py
- `tools/spelling.py` -> shadows: tools/ru_spelling.py
- `tools/utils.py` -> shadows: tools/utils_sbs.py
- `tools/version.py` -> shadows: tools/version_ru.py

## Modified - Inspired Sources
- `.github/workflows/draft_release.yml` -> inspired: .github/workflows/ru_release.yml, .github/workflows/ru_release_test.yml
- `docs/technical/quick_start.md` -> inspired: docs_rus/
- `exporter/goldendict/export_dpd.py` -> inspired: exporter/goldendict/export_dpd_ru.py, exporter/goldendict/export_dpd_sbs.py
- `exporter/goldendict/export_epd.py` -> inspired: exporter/goldendict/export_epd_sbs.py
- `exporter/goldendict/export_help.py` -> inspired: exporter/goldendict/export_help_ru.py, exporter/goldendict/export_help_sbs.py
- `exporter/goldendict/export_roots.py` -> inspired: exporter/goldendict/export_roots_ru.py, exporter/goldendict/export_roots_sbs.py
- `exporter/goldendict/export_variant_spelling.py` -> inspired: exporter/goldendict/export_variant_spelling_ru.py
- `exporter/goldendict/main.py` -> inspired: exporter/goldendict/main_ru.py, exporter/goldendict/main_sbs.py
- `gui2/dpd_fields.py` -> inspired: gui2/dps_fields.py
- `gui2/dpd_fields_lists.py` -> inspired: gui2/dps_fields_lists.py
- `scripts/bash/generate_components.py` -> inspired: scripts/bash/generate_components.sh

## New Or Unmapped Upstream Changes
- audio/archive/generate_audio_11_labs.py
- audio/bhashini/generate_dpd.py
- audio/db_create.py
- audio/db_release_upload.py
- audio/error_check/delete_silent_files.py
- audio/error_check/trim_audio.py
- db/backup_tsv/dpd_headwords_part_001.tsv
- db/backup_tsv/dpd_headwords_part_002.tsv
- db/backup_tsv/dpd_headwords_part_003.tsv
- db/backup_tsv/dpd_roots_part_001.tsv
- db/bold_definitions/extract_bold_definitions.py
- db/db_helpers.py
- db/grammar/grammar_to_lookup.py
- db/inflections/create_inflection_templates.py
- db/inflections/generate_inflection_tables.py
- db/inflections/inflections_to_headwords.py
- db/inflections/transliterate_inflections.py
- db/lookup/see.py
- db/lookup/spelling_mistakes.py
- db/lookup/transliterate_lookup_table.py
- db/sanskrit/root_families_sanskrit.tsv
- db/suttas/suttas_to_lookup.py
- db/suttas/suttas_update.py
- db/variants/add_to_db.py
- db/variants/extract_variants_from_bjt.py
- db/variants/extract_variants_from_cst.py
- db/variants/extract_variants_from_sc.py
- db/variants/extract_variants_from_sya.py
- db/variants/find_examples.py
- db/variants/main.py
- db/variants/variants_modules.py
- db_tests_gui/add_antonyms.py
- db_tests_gui/add_antonyms_sync.py
- db_tests_gui/add_hyphenations.py
- exporter/analysis/README.md
- exporter/analysis/ai_response.py
- exporter/analysis/analyzer.py
- exporter/analysis/example_bolding.py
- exporter/analysis/prompts.py
- exporter/analysis/ranking.py
- exporter/analysis/rendering.py
- exporter/analysis/retry.py
- exporter/analysis/scoring.py
- exporter/analysis/study_passage.py
- exporter/analysis/translate_core.py
- exporter/goldendict/helpers.py
- exporter/tpr/templates/tpr_headword.jinja
- exporter/txt/export_txt.py
- exporter/variants/variants_exporter.py
- exporter/webapp/generate_search_index.py
- exporter/webapp/scripts/process_logs.py
- go_modules/frequency/main.go
- gui2/additions_manager.py
- gui2/ai_search.py
- gui2/corrections_manager.py
- gui2/daily_log.py
- gui2/data/pass2_exceptions.json
- gui2/database_manager.py
- gui2/dpd_fields_commentary.py
- gui2/filter_presets_manager.py
- gui2/global_tab_view.py
- gui2/mixins.py
- gui2/pass1_auto_controller.py
- gui2/pass1_auto_view.py
- gui2/pass2_auto_control.py
- gui2/pass2_auto_view.py
- gui2/sandhi_files_manager.py
- gui2/utilities/find_words_with_examples.py
- resources/deconstructor_output
- resources/fdg_dpd
- resources/other-dictionaries
- resources/tpr_downloads
- scripts/build/api_ca_eva_iti_iva_hi.py
- scripts/build/config_github_release.py
- scripts/build/config_quick_profile.py
- scripts/build/config_uposatha_day.py
- scripts/build/cst4_xml_to_txt.py
- scripts/build/dealbreakers.py
- scripts/build/deconstructor_extract_archive.py
- scripts/build/deconstructor_output_add_to_db.py
- scripts/build/docs_add_indexes.py
- scripts/build/ebt_counter.py
- scripts/build/newsletter_scraper.py
- scripts/build/root_has_verb_updater.py
- scripts/build/sanskrit_root_families_updater.py
- scripts/build/tarball_db.py
- scripts/build/tarball_deconstructor_output.py
- scripts/build/transliterate_bjt.py
- scripts/build/zip_goldendict_mdict.py
- scripts/export/sanskrit_export.py
- scripts/extractor/_output.py
- scripts/extractor/extract_cone.py
- scripts/extractor/extract_cpd.py
- scripts/fix/fix_synonym_entries.py
- scripts/onboarding/desktop_shortcut.py
- shared_data/deconstructor/manual_corrections.tsv
- shared_data/user_dictionary.txt
- tools/ai_antigravity_cli.py
- tools/ai_deepseek_manager.py
- tools/ai_gpt_manager.py
- tools/ai_manager.py
- tools/ai_models.json
- tools/all_tipitaka_words.py
- tools/bjt.py
- tools/bold_definitions_search.py
- tools/cache_load.py
- tools/compound_type_manager.tsv
- tools/configger.py
- tools/css_manager.py
- tools/cst_sc_text_sets.py
- tools/cst_source_sutta_example.py
- tools/docs_changelog_and_release_notes.py
- tools/docs_update_abbreviations.py
- tools/docs_update_bibliography.py
- tools/docs_update_thanks.py
- tools/phonetic_changes.tsv
- tools/script_runner.py
- tools/speech_marks.json
- tools/tsv_read_write.py
- tools/uposatha_day.py
- tools/wordfinder_manager.py
- uv.lock

## Deleted Files
- exporter/kindle/tests/test_epd.py
- tools/update_test_add.py

## Needs Classification (Stage 2)
These upstream additions have no local collision. Register them in `registry.json` during Stage 2.
- .github/workflows/mobile_release.yml
- exporter/analysis/_base.py
- exporter/analysis/analysis_types.py
- scripts/fix/sanskrit_sutra_bsk.py
- scripts/project_management/project_health_check.py
- tools/ai_antigravity_cli_models.py
- tools/lookup_sync.py

## Stage 1 Blocker Paths
Resolve these paths before running `execute_sync.py`; rerun prep after registry/SMD or run-specific scope changes.
- exporter/analysis/ai_response.py (exists in local worktree)
- exporter/analysis/prompts.py (exists in local worktree)
- exporter/analysis/ranking.py (exists in local worktree)
- exporter/analysis/rendering.py (exists in local worktree)
- exporter/analysis/retry.py (exists in local worktree)
- exporter/analysis/scoring.py (exists in local worktree)
- exporter/kindle/tests/test_epd.py
- tools/ai_antigravity_cli.py (exists in local worktree)
- tools/update_test_add.py
