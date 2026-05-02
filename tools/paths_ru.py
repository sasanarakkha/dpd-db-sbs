"""All file paths that get used in the russian exporter related codes."""

import os
from typing import Optional
from pathlib import Path


class RuPaths:
    def __init__(self, base_dir: Optional[Path] = None, create_dirs=True):
        if base_dir is None:
            # The current working directory of the shell.
            base_dir = Path(os.path.abspath("."))

        # shared_data/help_ru/
        self.abbreviations_tsv_path = base_dir / "shared_data/help_ru/abbreviations.tsv"
        self.abbreviations_other_tsv_path = (
            base_dir / "shared_data/help_ru/abbreviations_other.tsv"
        )
        self.bibliography_tsv_path = base_dir / "shared_data/help_ru/bibliography.tsv"
        self.help_tsv_path = base_dir / "shared_data/help_ru/help.tsv"
        self.thanks_tsv_path = base_dir / "shared_data/help_ru/thanks.tsv"

        # /tsvs/
        self.sets_ru_path = base_dir / "shared_data/rus/sets_ru.tsv"

        # db/suttas
        self.dv_catalogue_suttas_tsv_path = (
            base_dir / "db/suttas/dv_catalogue_suttas.tsv"
        )

        # tools
        self.uposatha_day_ini = base_dir / "tools/uposatha_day.ini"
        self.tpr_codes_json_path = base_dir / "tools/tpr_codes.json"

        # exporter/kindle/
        self.epub_dir = base_dir / "exporter/kindle/ru_components/epub/"
        self.kindlegen_path = base_dir / "exporter/kindle/kindlegen"

        # exporter/kindle/ru_epub
        self.epub_abbreviations_path = (
            base_dir
            / "exporter/kindle/ru_components/epub/OEBPS/Text/abbreviations.xhtml"
        )
        self.epub_content_opf_path = (
            base_dir / "exporter/kindle/ru_components/epub/OEBPS/content.opf"
        )
        self.epub_text_dir = base_dir / "exporter/kindle/ru_components/epub/OEBPS/Text"
        self.epub_titlepage_path = (
            base_dir / "exporter/kindle/ru_components/epub/OEBPS/Text/titlepage.xhtml"
        )

        # exporter/kindle/ru_templates
        self.ebook_abbrev_entry_templ_path = (
            base_dir
            / "exporter/kindle/ru_components/templates/ebook_ru_abbreviation_entry.html"
        )
        self.ebook_content_opf_templ_path = (
            base_dir
            / "exporter/kindle/ru_components/templates/ebook_ru_content_opf.html"
        )
        self.ebook_deconstructor_templ_path = (
            base_dir
            / "exporter/kindle/ru_components/templates/ebook_ru_deconstructor_entry.html"
        )
        self.ebook_entry_templ_path = (
            base_dir / "exporter/kindle/ru_components/templates/ebook_ru_entry.html"
        )
        self.ebook_example_templ_path = (
            base_dir / "exporter/kindle/ru_components/templates/ebook_ru_example.html"
        )
        self.ebook_grammar_templ_path = (
            base_dir / "exporter/kindle/ru_components/templates/ebook_ru_grammar.html"
        )
        self.ebook_letter_templ_path = (
            base_dir / "exporter/kindle/ru_components/templates/ebook_ru_letter.html"
        )
        self.ebook_rpd_entry_templ_path = (
            base_dir / "exporter/kindle/ru_components/templates/ebook_ru_rpd_entry.html"
        )
        self.ebook_rpd_letter_templ_path = (
            base_dir
            / "exporter/kindle/ru_components/templates/ebook_ru_rpd_letter.html"
        )
        self.ebook_title_page_templ_path = (
            base_dir / "exporter/kindle/ru_components/templates/ebook_ru_titlepage.html"
        )
        #  exporter/goldendict/javascript/
        self.buttons_js_path = base_dir / "exporter/goldendict/javascript/buttons.js"
        self.family_compound_json = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_family_compound_json.js"
        )
        self.family_compound_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_family_compound_template.js"
        )
        self.family_idiom_json = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_family_idiom_json.js"
        )
        self.family_idiom_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_family_idiom_template.js"
        )
        self.family_root_json = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_family_root_json.js"
        )
        self.family_root_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_family_root_template.js"
        )
        self.family_set_json = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_family_set_json.js"
        )
        self.family_set_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_family_set_template.js"
        )
        self.family_word_json = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_family_word_json.js"
        )
        self.family_word_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_family_word_template.js"
        )
        self.feedback_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_feedback_template.js"
        )
        self.frequency_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/ru_frequency_template.js"
        )
        self.main_js_path = (
            base_dir / "exporter/goldendict/ru_components/javascript/ru_main.js"
        )

        # exporter/share
        self.dpd_deconstructor_goldendict_dir = (
            base_dir / "exporter/share/ru-dpd-deconstructor/"
        )
        self.dpd_epub_path = base_dir / "exporter/share/ru-dpd-kindle.epub"
        self.dpd_goldendict_dir = base_dir / "exporter/share/ru-dpd/"
        self.dpd_goldendict_zip_path = base_dir / "exporter/share/ru-dpd-goldendict.zip"
        self.dpd_grammar_goldendict_dir = base_dir / "exporter/share/ru-dpd-grammar/"
        self.dpd_variants_goldendict_dir = base_dir / "exporter/share/dpd-variants/"
        self.dpd_mdict_zip_path = base_dir / "exporter/share/ru-dpd-mdict.zip"
        self.dpd_mobi_path = base_dir / "exporter/share/ru-dpd-kindle.mobi"
        self.share_dir = base_dir / "exporter/share"

        # exporter/share/mdict
        self.dpd_deconstructor_mdd_path = (
            base_dir / "exporter/share/ru-dpd-deconstructor-mdict.mdd"
        )
        self.dpd_deconstructor_mdx_path = (
            base_dir / "exporter/share/ru-dpd-deconstructor-mdict.mdx"
        )
        self.dpd_grammar_mdd_path = base_dir / "exporter/share/ru-dpd-grammar-mdict.mdd"
        self.dpd_grammar_mdx_path = base_dir / "exporter/share/ru-dpd-grammar-mdict.mdx"
        self.dpd_variants_mdd_path = base_dir / "exporter/share/dpd-variants-mdict.mdd"
        self.dpd_variants_mdx_path = base_dir / "exporter/share/dpd-variants-mdict.mdx"
        self.dpd_mdd_path = base_dir / "exporter/share/ru-dpd-mdict.mdd"
        self.dpd_mdx_path = base_dir / "exporter/share/ru-dpd-mdict.mdx"

        # exporter/deconstructor/templates
        self.deconstructor_header_templ_path = (
            base_dir / "exporter/deconstructor/deconstructor_header.html"
        )
        self.deconstructor_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/deconstructor.html"
        )

        # exporter/templates
        self.button_box_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/dpd_button_box.html"
        )
        self.dpd_definition_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/dpd_definition.html"
        )
        self.dpd_header_plain_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_header_plain.html"
        )
        self.dpd_header_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/dpd_header.html"
        )
        self.example_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/dpd_example.html"
        )
        self.family_compound_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_family_compound.html"
        )
        self.family_idiom_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_family_idiom.html"
        )
        self.family_root_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_family_root.html"
        )
        self.family_set_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/dpd_family_set.html"
        )
        self.family_word_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_family_word.html"
        )
        self.feedback_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/dpd_feedback.html"
        )
        self.frequency_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/dpd_frequency.html"
        )
        self.grammar_dict_header_templ_path = (
            base_dir / "exporter/goldendict/templates/grammar_dict_header.html"
        )
        self.grammar_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/dpd_grammar.html"
        )
        self.inflection_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/dpd_inflection.html"
        )
        self.root_header_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/root_header.html"
        )
        self.see_templ_path = base_dir / "exporter/goldendict/templates/dpd_see.jinja"
        self.spelling_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_spelling_mistake.html"
        )
        self.templates_dir = base_dir / "exporter/goldendict/ru_components/templates"
        self.variant_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_variant_reading.html"
        )
        self.sutta_info_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/dpd_sutta_info.html"
        )

        # exporter/goldendict/templates - root
        self.root_button_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/root_buttons.html"
        )
        self.root_definition_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/root_definition.html"
        )
        self.root_families_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/root_families.html"
        )
        self.root_info_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/root_info.html"
        )
        self.root_matrix_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/root_matrix.html"
        )

        # exporter/goldendict/templates - other
        self.abbrev_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/help_abbrev.html"
        )
        self.epd_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/rpd.html"
        )
        self.help_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/help_help.html"
        )

        # exporter/webapp
        self.webapp_css_path = base_dir / "exporter/webapp/static/dpd.css"
        self.webapp_ru_templates_dir = base_dir / "exporter/webapp/ru_templates"
        self.webapp_sbs_templates_dir = base_dir / "exporter/webapp/sbs_templates"
        self.webapp_static_dir = base_dir / "exporter/webapp/static"
        self.webapp_js_path = base_dir / "exporter/webapp/static/dpd.js"
        self.webapp_home_simple_css_path = (
            base_dir / "exporter/webapp/static/home_simple.css"
        )
        self.webapp_home_css_path = base_dir / "exporter/webapp/static/home.css"
        self.webapp_bold_definitions_js_path = (
            base_dir / "exporter/webapp/static/bold_definitions.js"
        )
        self.webapp_logo_svg_path = base_dir / "exporter/webapp/static/dpd-logo.svg"
        self.webapp_logo_dark_svg_path = (
            base_dir / "exporter/webapp/static/dpd-logo-dark.svg"
        )
        self.webapp_app_js_path = base_dir / "exporter/webapp/static/app.js"
        self.webapp_switch_css_path = base_dir / "exporter/webapp/static/switch.css"

        # webapp template names as constants
        self.template_dpd_summary = "dpd_summary.html"
        self.template_dpd_headword = "dpd_headword.html"
        self.template_root_summary = "root_summary.html"
        self.template_root = "root.html"
        self.template_abbreviations_summary = "abbreviations_summary.html"
        self.template_abbreviations = "abbreviations.html"
        self.template_abbreviations_other_summary = "abbreviations_other_summary.html"
        self.template_abbreviations_other = "abbreviations_other.html"
        self.template_deconstructor_summary = "deconstructor_summary.html"
        self.template_deconstructor = "deconstructor.html"
        self.template_grammar_summary = "grammar_summary.html"
        self.template_grammar = "grammar.html"
        self.template_help_summary = "help_summary.html"
        self.template_help = "help.html"
        self.template_epd_summary = "epd_summary.html"
        self.template_epd = "epd.html"
        self.template_rpd_summary = "rpd_summary.html"
        self.template_rpd = "rpd.html"
        self.template_variant_summary = "variant_summary.html"
        self.template_variant = "variant.html"
        self.template_see_summary = "see_summary.html"
        self.template_see = "see.html"
        self.template_manual_variant = "manual_variant.html"
        self.template_manual_variant_summary = "manual_variant_summary.html"
        self.template_spelling_summary = "spelling_summary.html"
        self.template_spelling = "spelling.html"

        # tpr
        self.tpr_with_rus_path = (
            base_dir / "resources/tpr_downloads/release_zips/dpd_with_rus.zip"
        )

        # identity/
        self.dpd_css_path = base_dir / "identity/css/dpd.css"
        self.dpd_variables_css_path = base_dir / "identity/css/dpd-variables.css"
        self.dpd_fonts_css_path = base_dir / "identity/css/dpd-fonts.css"
        self.dpd_css_and_fonts_path = base_dir / "identity/css/dpd-css-and-fonts.css"

        # identity/logo
        self.dpd_logo_svg = base_dir / "identity/logo/dpd-logo.svg"
        self.dpd_logo_dark_svg = base_dir / "identity/logo/dpd-logo-dark.svg"
        self.dpd_logo_dark_bmp = base_dir / "identity/logo/dpd-logo-dark.bmp"

        # identity/fonts
        self.fonts_dir = base_dir / "identity/fonts"

        # resources/fdg_dpd
        self.fdg_dpd_ebts_js_ru_path = (
            base_dir / "resources/fdg_dpd/assets/standalone-dpd/ru/dpd_ebts.js"
        )

        # ru_docs
        self.mk_docs_yaml = base_dir / "mkdocs_ru.yaml"
        self.docs_css_path = base_dir / "docs_rus/stylesheets/extra.css"
        self.docs_css_variables_path = (
            base_dir / "docs_rus/stylesheets/dpd-variables.css"
        )
        self.docs_dir = base_dir / "docs_rus/"
        self.docs_bibliography_md_path = base_dir / "docs_rus/bibliography.md"
        self.docs_abbreviations_md_path = base_dir / "docs_rus/abbreviations.md"
        self.docs_changelog_md_path = base_dir / "docs_rus/changelog.md"
        self.docs_thanks_md_path = base_dir / "docs_rus/thanks.md"

        # temp
        self.temp_dir = base_dir / "temp/"

        if create_dirs:
            self.create_dirs()

    def create_dirs(self):
        for d in [
            self.templates_dir,
            self.share_dir,
            self.epub_dir,
            self.epub_text_dir,
            self.temp_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)
