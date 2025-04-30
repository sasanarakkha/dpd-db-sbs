"""All file paths that get used in the russian exporter related codes."""

import os
from typing import Optional
from pathlib import Path


class RuPaths:
    def __init__(self, base_dir: Optional[Path] = None, create_dirs=True):
        if base_dir is None:
            # The current working directory of the shell.
            base_dir = Path(os.path.abspath("."))

        # /tsvs/
        self.sets_ru_path = (
            base_dir / "dps/rus/sets_ru.tsv"
        )

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
        self.ebook_title_page_templ_path = (
            base_dir / "exporter/kindle/ru_components/templates/ebook_ru_titlepage.html"
        )
        #  exporter/goldendict/javascript/
        self.buttons_js_path = base_dir / "exporter/goldendict/javascript/buttons.js"
        self.family_compound_json = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/family_compound_json.js"
        )
        self.family_compound_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/family_compound_template.js"
        )
        self.family_idiom_json = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/family_idiom_json.js"
        )
        self.family_idiom_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/family_idiom_template.js"
        )
        self.family_root_json = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/family_root_json.js"
        )
        self.family_root_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/family_root_template.js"
        )
        self.family_set_json = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/family_set_json.js"
        )
        self.family_set_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/family_set_template.js"
        )
        self.family_word_json = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/family_word_json.js"
        )
        self.family_word_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/family_word_template.js"
        )
        self.feedback_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/feedback_template.js"
        )
        self.frequency_template_js = (
            base_dir
            / "exporter/goldendict/ru_components/javascript/frequency_template.js"
        )
        self.main_js_path = (
            base_dir / "exporter/goldendict/ru_components/javascript/main.js"
        )

        # exporter/share
        self.dpd_deconstructor_goldendict_dir = (
            base_dir / "exporter/share/ru-dpd-deconstructor/"
        )
        self.dpd_epub_path = base_dir / "exporter/share/ru-dpd-kindle.epub"
        self.dpd_goldendict_dir = base_dir / "exporter/share/ru-dpd/"
        self.dpd_goldendict_zip_path = base_dir / "exporter/share/ru-dpd-goldendict.zip"
        self.dpd_grammar_goldendict_dir = base_dir / "exporter/share/ru-dpd-grammar/"
        self.dpd_mdict_zip_path = base_dir / "exporter/share/ru-dpd-mdict.zip"
        self.dpd_mobi_path = base_dir / "exporter/share/ru-dpd-kindle.mobi"
        self.dpd_variants_goldendict_dir = base_dir / "exporter/share/dpd-variants/"
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
        self.dpd_mdd_path = base_dir / "exporter/share/ru-dpd-mdict.mdd"
        self.dpd_mdx_path = base_dir / "exporter/share/ru-dpd-mdict.mdx"
        self.dpd_variants_mdd_path = base_dir / "exporter/share/dpd-variants-mdict.mdd"
        self.dpd_variants_mdx_path = base_dir / "exporter/share/dpd-variants-mdict.mdx"

        # exporter/deconstructor/templates
        self.deconstructor_header_templ_path = (
            base_dir / "exporter/deconstructor/deconstructor_header.html"
        )
        self.deconstructor_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/deconstructor.html"
        )

        # exporter/templates
        self.button_box_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_button_box.html"
        )
        self.dpd_definition_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_definition.html"
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
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_family_set.html"
        )
        self.family_word_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_family_word.html"
        )
        self.feedback_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_feedback.html"
        )
        self.frequency_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_frequency.html"
        )
        self.grammar_dict_header_templ_path = (
            base_dir / "exporter/goldendict/templates/grammar_dict_header.html"
        )
        self.grammar_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/dpd_grammar.html"
        )
        self.inflection_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_inflection.html"
        )
        self.root_header_templ_path = (
            base_dir / "exporter/goldendict/ru_components/templates/root_header.html"
        )
        self.sbs_example_templ_path = (
            base_dir / "exporter/goldendict/templates/sbs_example.html"
        )
        self.spelling_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_spelling_mistake.html"
        )
        self.templates_dir = base_dir / "exporter/goldendict/ru_components/templates"
        self.variant_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/dpd_variant_reading.html"
        )

        # exporter/goldendict/templates - root
        self.root_button_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/root_buttons.html"
        )
        self.root_definition_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/root_definition.html"
        )
        self.root_families_templ_path = (
            base_dir
            / "exporter/goldendict/ru_components/templates/root_families.html"
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
        self.fdg_dpd_ebts_js_ru_path = base_dir / "resources/fdg_dpd/assets/standalone-dpd/ru/dpd_ebts.js"

        # ru_docs
        self.mk_docs_yaml = base_dir / "mkdocs_ru.yaml"
        self.docs_css_path = base_dir / "docs_rus/stylesheets/extra.css"
        self.docs_css_variables_path = base_dir / "docs_rus/stylesheets/dpd-variables.css"
        self.docs_dir = base_dir / "docs_rus/"
        self.docs_bibliography_md_path = base_dir / "docs_rus/bibliography.md"
        self.docs_abbreviations_md_path = base_dir / "docs_rus/abbreviations.md"
        self.docs_changelog_md_path = base_dir / "docs_rus/changelog.md"
        self.docs_thanks_md_path = base_dir / "docs_rus/thanks.md"
        
        if create_dirs:
            self.create_dirs()

    def create_dirs(self):
        for d in [
            self.templates_dir,
            self.share_dir,
            self.epub_dir,
            self.epub_text_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)
