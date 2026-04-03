"""All file paths that get used in the dps related codes."""

import os
from typing import Optional
from pathlib import Path


class DPSPaths:
    def __init__(self, base_dir: Optional[Path] = None, create_dirs=True):
        if base_dir is None:
            # The current working directory of the shell.
            base_dir = Path(os.path.abspath("."))

        # exporter/sbs_templates
        self.button_box_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_button_box.jinja"
        )
        self.dpd_definition_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_definition.jinja"
        )
        self.dpd_header_plain_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_header_plain.jinja"
        )
        self.dpd_header_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_header.jinja"
        )
        self.example_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_example.jinja"
        )
        self.sbs_example_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/sbs_example.jinja"
        )
        self.family_compound_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_family_compound.jinja"
        )
        self.family_idiom_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_family_idiom.jinja"
        )
        self.family_root_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_family_root.jinja"
        )
        self.family_set_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_family_set.jinja"
        )
        self.family_word_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_family_word.jinja"
        )
        self.feedback_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_feedback.jinja"
        )
        self.frequency_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_frequency.jinja"
        )
        self.grammar_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_grammar.jinja"
        )
        self.inflection_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_inflection.jinja"
        )
        self.root_header_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/root_header.jinja"
        )
        self.spelling_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_spelling_mistake.jinja"
        )
        self.templates_dir = base_dir / "exporter/goldendict/sbs_templates"
        self.variant_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_variant_reading.jinja"
        )
        self.sutta_info_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/dpd_sutta_info.jinja"
        )

        # exporter/goldendict/sbs_templates - root
        self.root_button_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/root_buttons.jinja"
        )
        self.root_definition_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/root_definition.jinja"
        )
        self.root_families_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/root_families.jinja"
        )
        self.root_info_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/root_info.jinja"
        )
        self.root_matrix_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/root_matrix.jinja"
        )

        # exporter/goldendict/sbs_templates - other
        self.abbrev_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/help_abbrev.jinja"
        )
        self.epd_templ_path = base_dir / "exporter/goldendict/sbs_templates/epd.jinja"
        self.help_templ_path = (
            base_dir / "exporter/goldendict/sbs_templates/help_help.jinja"
        )

        # shared_data/help_ru/
        self.abbreviations_tsv_path = base_dir / "shared_data/help_ru/abbreviations.tsv"
        self.bibliography_tsv_path = base_dir / "shared_data/help_ru/bibliography.tsv"
        self.help_tsv_path = base_dir / "shared_data/help_ru/help.tsv"
        self.thanks_tsv_path = base_dir / "shared_data/help_ru/thanks.tsv"

        # db/suttas
        self.dv_catalogue_suttas_tsv_path = (
            base_dir / "db/suttas/dv_catalogue_suttas.tsv"
        )

        # tools
        self.uposatha_day_ini = base_dir / "tools/uposatha_day.ini"
        self.tpr_codes_json_path = base_dir / "tools/tpr_codes.json"

        # shared_data
        self.sbs_index_path = base_dir.joinpath(
            Path("shared_data/sbs_csvs/sbs_index.csv")
        )
        self.class_index_path = base_dir.joinpath(
            Path("shared_data/sbs_csvs/class_index.csv")
        )
        self.sutta_index_path = base_dir.joinpath(
            Path("shared_data/sbs_csvs/sutta_index.csv")
        )
        self.ru_user_dict_path = base_dir.joinpath(
            Path("shared_data/russian_words_user_dict.txt")
        )
        self.translation_example_path = base_dir.joinpath(
            Path("shared_data/sbs_csvs/translation_examples.csv")
        )
        self.sbs_archive = base_dir.joinpath(
            Path("shared_data/sbs_csvs/sbs_archive.tsv")
        )
        self.pat_links_path = base_dir.joinpath(
            Path("shared_data/sbs_csvs/pat_links.tsv")
        )
        self.ru_total_root_path = base_dir.joinpath(
            Path("shared_data/rus/ru_total_roots.tsv")
        )
        self.ru_total_comp_path = base_dir.joinpath(
            Path("shared_data/rus/ru_total_comps.tsv")
        )

        self.pali_class_vocab_dir = base_dir.joinpath(
            Path("shared_data/pali_class/vocab/")
        )
        self.pali_class_output_dir = base_dir.joinpath(Path("shared_data/pali_class/"))

        self.discourses_vocab_dir = base_dir.joinpath(
            Path("shared_data/discourses/vocab/")
        )
        self.discourses_output_dir = base_dir.joinpath(Path("shared_data/discourses/"))

        self.internal_tests_path = base_dir.joinpath(
            Path("db_tests/dps_internal_tests.tsv")
        )

        # backup_tsv folder
        self.for_compare_dir = base_dir.joinpath(Path("db/backup_tsv/for_compare/"))
        self.ru_root_path = base_dir / "db/backup_tsv/ru_roots.tsv"
        self.russian_path = base_dir / "db/backup_tsv/russian.tsv"
        self.sbs_path = base_dir / "db/backup_tsv/sbs.tsv"

        # temp
        self.temp_dir = base_dir / "temp/"
        self.text_to_add_path = base_dir.joinpath(Path("temp/text.txt"))
        self.temp_csv_backup_dir = base_dir.joinpath(Path("temp/backup_csv/"))
        self.temp_csv_path = base_dir.joinpath(Path("temp/temp.csv"))
        self.id_to_add_path = base_dir.joinpath(Path("temp/id_to_add.csv"))
        self.id_temp_list_path = base_dir.joinpath(Path("temp/id_temp_list.csv"))
        self.csvs_for_audio_dir = base_dir.joinpath(Path("temp/csvs_for_audio/"))
        self.ai_translated_dir = base_dir.joinpath(Path("temp/ai_translated"))
        self.sbs_example_corrections = base_dir.joinpath(
            Path("temp/sbs_example_corrections.tsv")
        )
        self.ru_apply_path = base_dir.joinpath(Path("temp/ru_apply.csv"))
        self.total_words_path = base_dir.joinpath(Path("temp/total_words.tsv"))
        self.total_words_meaning = base_dir.joinpath(
            Path("temp/total_words_meaning.txt")
        )
        self.total_roots_path = base_dir.joinpath(Path("temp/total_roots.tsv"))
        self.sbs_class_vocab_dir = base_dir.joinpath(Path("temp/vocab/"))
        self.for_compare_csv_dir = base_dir.joinpath(Path("temp/for_compare/"))
        self.dps_internal_tests_replaced_path = base_dir.joinpath(
            Path("temp/dps_internal_tests_replaced.tsv")
        )
        self.dps_test_1_path = base_dir.joinpath(Path("temp/dps_test_1.tsv"))
        self.dps_test_2_path = base_dir.joinpath(Path("temp/dps_test_2.tsv"))

        # /temp/anki csvs
        self.anki_csvs_dir = base_dir.joinpath(Path("temp/anki_csvs/"))
        self.pali_class_dir = base_dir.joinpath(Path("temp/anki_csvs/pali_class/"))
        self.pali_class_grammar_dir = base_dir.joinpath(
            Path("temp/anki_csvs/pali_class/grammar/")
        )

        # /temp/ai-related
        self.ai_ru_suggestion_history_path = base_dir.joinpath(
            Path("temp/ai_ru_suggestion_history.csv")
        )
        self.ai_ru_notes_suggestion_history_path = base_dir.joinpath(
            Path("temp/ai_ru_notes_suggestion_history.csv")
        )
        self.ai_en_suggestion_history_path = base_dir.joinpath(
            Path("temp/ai_en_suggestion_history.csv")
        )

        self.ai_for_batch_api_dir = base_dir.joinpath(Path("temp/ai_for_batch_api/"))
        self.ai_from_batch_api_dir = base_dir.joinpath(Path("temp/ai_from_batch_api/"))
        self.ai_processed_ids_json = base_dir.joinpath(
            Path("temp/ai_from_batch_api/processed_ids.json")
        )

        self.ai_meaning_checked = base_dir.joinpath(
            Path("temp/ai_meaning_check/checked_ids.json")
        )
        self.ai_meaning_raw_checked = base_dir.joinpath(
            Path("temp/ai_meaning_raw_check/checked_ids.json")
        )
        self.ai_meaning_ru_raw_checked = base_dir.joinpath(
            Path("temp/ai_meaning_ru_raw_check/checked_ids.json")
        )
        self.ai_meaning_lit_checked = base_dir.joinpath(
            Path("temp/ai_meaning_lit_check/checked_ids.json")
        )
        self.ai_notes_checked = base_dir.joinpath(
            Path("temp/ai_notes_check/checked_ids.json")
        )
        self.ai_notes_raw_checked = base_dir.joinpath(
            Path("temp/ai_notes_raw_check/checked_ids.json")
        )

        self.ai_meaning_report_dir = base_dir.joinpath(Path("temp/ai_meaning_check/"))
        self.ai_meaning_raw_report_dir = base_dir.joinpath(
            Path("temp/ai_meaning_raw_check/")
        )
        self.ai_meaning_ru_raw_report_dir = base_dir.joinpath(
            Path("temp/ai_meaning_ru_raw_check/")
        )
        self.ai_meaning_lit_report_dir = base_dir.joinpath(
            Path("temp/ai_meaning_lit_check/")
        )
        self.ai_notes_report_dir = base_dir.joinpath(Path("temp/ai_notes_check/"))
        self.ai_notes_raw_report_dir = base_dir.joinpath(
            Path("temp/ai_notes_raw_check/")
        )

        # /gui/stash
        self.dps_stash_path = base_dir.joinpath(Path("gui/stash/dps_stash.json"))
        self.dps_save_state_path = base_dir.joinpath(Path("gui/stash/dps_gui_state"))

        # /gui2
        self.history_json_path: Path = base_dir.joinpath(
            Path("gui2/data/dps_history.json")
        )
        self.example_stash_json_path: Path = base_dir.joinpath(
            Path("gui2/data/dps_example_stash.json")
        )
        self.addition_replaced_json_path: Path = base_dir.joinpath(
            Path("gui2/data/addition_replaced.json")
        )
        self.addition_processed_json_path: Path = base_dir.joinpath(
            Path("gui2/data/addition_processed.json")
        )
        self.corrections_processed_json_path: Path = base_dir.joinpath(
            Path("gui2/data/corrections_processed.json")
        )

        # .. external
        self.sbs_anki_style_dir = base_dir.joinpath(
            Path("../sasanarakkha/study-tools/anki-style/")
        )
        self.pali_class_vocab_html_dir = base_dir.joinpath(
            Path("../sasanarakkha/study-tools/pali-class/vocab/")
        )
        self.local_downloads_dir = base_dir.joinpath(Path("../../Downloads/"))

        if create_dirs:
            self.create_dirs()

    def create_dirs(self):
        for d in [
            self.anki_csvs_dir,
            self.pali_class_dir,
            self.pali_class_grammar_dir,
            self.for_compare_dir,
            self.for_compare_csv_dir,
            self.temp_csv_backup_dir,
            self.csvs_for_audio_dir,
            self.ai_for_batch_api_dir,
            self.ai_from_batch_api_dir,
            self.sbs_class_vocab_dir,
            self.ai_translated_dir,
            self.temp_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)
