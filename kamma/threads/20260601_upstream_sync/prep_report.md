# Upstream Sync Preparation Report

## Upstream Range
- From: `44a8a00556cce9bd3874a94efb5dfaceaaf20a66`
- To: `40083765d770a68b93bfc5e7227b5973e3faf414`

## Registry Validation Status
OK: Registry is valid.

## SMD Coverage Status
OK: SMD coverage is complete and rubric-compliant.

## Modified - Tracked Files
- .gitignore
- AGENTS.md
- db/models.py
- gui2/pass2_add_view.py

## Modified - Shadow Sources
- `db/families/family_compound.py` -> shadows: db/families/family_compound_ru.py
- `db/families/family_root.py` -> shadows: db/families/family_root_ru.py
- `db/families/family_word.py` -> shadows: db/families/family_word_ru.py
- `exporter/goldendict/templates/dpd_headword.jinja` -> shadows: exporter/goldendict/ru_components/templates/, exporter/goldendict/sbs_templates/
- `exporter/webapp/main.py` -> shadows: exporter/webapp/main_ru.py
- `exporter/webapp/templates/dpd_headword.html` -> shadows: exporter/webapp/ru_templates/, exporter/webapp/sbs_templates/
- `exporter/webapp/templates/home.html` -> shadows: exporter/webapp/ru_templates/, exporter/webapp/sbs_templates/
- `shared_data/help/abbreviations.tsv` -> shadows: shared_data/help_ru/

## Modified - Inspired Sources
- `.github/workflows/draft_release.yml` -> inspired: .github/workflows/ru_release.yml, .github/workflows/ru_release_test.yml
- `.github/workflows/static.yml` -> inspired: .github/workflows/ru_static.yml
- `docs/abbreviations.md` -> inspired: docs_rus/
- `docs/changelog.md` -> inspired: docs_rus/
- `docs/install/anki.md` -> inspired: docs_rus/
- `docs/install/chromebook.md` -> inspired: docs_rus/
- `docs/newsletters.md` -> inspired: docs_rus/
- `exporter/goldendict/export_dpd.py` -> inspired: exporter/goldendict/export_dpd_ru.py, exporter/goldendict/export_dpd_sbs.py
- `mkdocs.yaml` -> inspired: mkdocs_ru.yaml
- `scripts/bash/generate_components.py` -> inspired: scripts/bash/generate_components.sh
- `tools/paths.py` -> inspired: tools/paths_ru.py, tools/paths_dps.py

## New Or Unmapped Upstream Changes
- .gitattributes
- .gitmodules
- audio/bhashini/bhashini_class.py
- audio/bhashini/generate_dpd.py
- db/backup_tsv/dpd_headwords_part_001.tsv
- db/backup_tsv/dpd_headwords_part_002.tsv
- db/backup_tsv/dpd_headwords_part_003.tsv
- db/backup_tsv/dpd_roots_part_001.tsv
- db/backup_tsv/sutta_info.tsv
- db/db_helpers.py
- db/inflections/inflection_templates.xlsx
- db/sanskrit/root_families_sanskrit.tsv
- db_tests_gui/add_antonyms_sync_dict.json
- docs/install/anki.md
- gui2/ai_search.py
- gui2/daily_log.py
- gui2/database_manager.py
- gui2/dpd_fields.py
- gui2/dpd_fields_examples.py
- gui2/dpd_fields_flags.py
- gui2/dpd_fields_lists.py
- gui2/example_stash_manager.py
- gui2/filter_component.py
- gui2/global_tab_view.py
- gui2/history.py
- gui2/pass1_auto_controller.py
- gui2/pass2_auto_control.py
- gui2/pass2_pre_controller.py
- gui2/pass2_pre_view.py
- gui2/sandhi_find_replace_view.py
- gui2/wordfinder_popup.py
- justfile
- pyproject.toml
- resources/bw2
- resources/deconstructor_output
- resources/dpd_submodules
- resources/fdg_dpd
- resources/sc-data
- resources/tpr_downloads
- scripts/build/deconstructor_extract_archive.py
- scripts/build/ebt_counter.py
- scripts/build/newsletter_processed.json
- scripts/cl/dpd-anki
- shared_data/deconstructor/checked.csv
- shared_data/deconstructor/manual_corrections.tsv
- shared_data/deconstructor/see.tsv
- shared_data/deconstructor/spelling_mistakes.tsv
- shared_data/deconstructor/variant_readings.tsv
- shared_data/user_dictionary.txt
- tools/ai_manager.py
- tools/compound_type_manager.tsv
- tools/cst_source_sutta_example.py
- tools/docs_changelog_and_release_notes.py
- tools/phonetic_changes.tsv
- tools/sutta_codes.py
- tools/uposatha_day.ini
- tools/zip_up.py
- uv.lock

## Stage 1 Blocker Paths
_No Stage 1 blockers._
