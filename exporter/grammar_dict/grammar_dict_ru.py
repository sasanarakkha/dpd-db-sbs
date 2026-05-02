#!/usr/bin/env python3

"""Compile HTML table of all grammatical possibilities of every inflected word-form."""

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.configger import config_read, config_test
from tools.goldendict_exporter import DictInfo, DictVariables, DictEntry
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.paths_ru import RuPaths
from tools.printer import printer as pr
from exporter.jinja2_env import get_jinja2_env
from exporter.grammar_dict.data_classes import GrammarData

from tools.tools_for_ru_exporter import (
    ru_replace_abbreviations,
    load_abbreviations_dict,
)


class GrammarData_ru(GrammarData):
    def _process_grammar(self, grammar_data_list):
        processed_rows = super()._process_grammar(grammar_data_list)

        # Translate components to Russian
        for row in processed_rows:
            row["pos"] = ru_replace_abbreviations(row["pos"])
            for i in range(len(row["components"])):
                if row["components"][i]:
                    row["components"][i] = ru_replace_abbreviations(
                        row["components"][i], kind="gram"
                    )

        return processed_rows


class ProgData_ru:
    def __init__(self) -> None:
        if config_test("dictionary", "make_mdict", "yes"):
            self.make_mdict = True
        else:
            self.make_mdict = False

        self.make_slob = config_read("goldendict", "make_slob", "no") == "yes"

        self.pth = ProjectPaths()
        self.rupth = RuPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)

        # the grammar dictionaries
        self.html_dict: dict[str, str] = {}

        # goldendict and mdict data_list
        self.dict_data: list[DictEntry] = []

    def close_db(self):
        self.db_session.close()

    def commit_db(self):
        self.db_session.commit()


def main():
    pr.tic()
    pr.yellow_title("exporting grammar dictionary (ru)")

    if not config_test("exporter", "make_grammar", "yes"):
        pr.green_tmr("disabled in config.ini")
        pr.toc()
        return

    g = ProgData_ru()

    generate_html_from_lookup(g)

    g.close_db()

    make_data_lists(g)
    prepare_gd_mdict_and_export(g)

    pr.toc()


def generate_html_from_lookup(g: ProgData_ru):
    """Generate HTML grammar tables from Lookup table data."""
    pr.green_tmr("querying database")

    lookup_results = (
        g.db_session.query(Lookup)
        .filter(Lookup.grammar.is_not(None), Lookup.grammar != "")
        .all()
    )

    pr.yes(f"{len(lookup_results)}")

    pr.green_tmr("compiling html")

    # Preload abbreviations dictionary
    load_abbreviations_dict(g.rupth.abbreviations_tsv_path)

    jinja_env = get_jinja2_env("exporter/grammar_dict")
    template = jinja_env.get_template("grammar.jinja")

    html_dict = {}
    grammar_cache: dict[str, str] = {}

    for lookup_entry in lookup_results:
        inflected_word = lookup_entry.lookup_key
        grammar_data = lookup_entry.grammar

        if grammar_data in grammar_cache:
            entry_html = grammar_cache[grammar_data]
        else:
            # Use ViewModel
            data = GrammarData_ru(lookup_entry, g.pth, jinja_env)
            entry_html = template.render(data=data)

            # Since the Jinja template hardcodes "of", we need to replace it with "для"
            # It also hardcodes the column headers in English, so we replace them.
            entry_html = entry_html.replace("<td>of</td>", "<td>для</td>")
            entry_html = entry_html.replace(
                "<th id='col1'>pos ⇅</th>", "<th id='col1'>чр ⇅</th>"
            )
            entry_html = entry_html.replace(
                "<th id='col6'>word ⇅</th>", "<th id='col6'>слово ⇅</th>"
            )

            grammar_cache[grammar_data] = entry_html

        html_dict[inflected_word] = entry_html

    g.html_dict = html_dict
    pr.yes(len(html_dict))


def make_data_lists(g: ProgData_ru):
    """Make the data_lists to be consumed by GoldenDict and MDict"""
    pr.green_tmr("making data lists")

    dict_data: list[DictEntry] = []
    for word, html in g.html_dict.items():
        synonyms = add_niggahitas([word])

        dict_data += [
            DictEntry(
                word=word, definition_html=html, definition_plain="", synonyms=synonyms
            )
        ]

    g.dict_data = dict_data
    pr.yes("ok")


def prepare_gd_mdict_and_export(g: ProgData_ru):
    """Prepare the metadata and export to goldendict & mdict."""

    dict_info = DictInfo(
        bookname="DPD Грамматика",
        author="Дост. Бодхираса, переведено Дэвамитта Бхиккху",
        description="<h3>DPD Грамматика</h3><p>Таблица всех грамматических возможностей, которыми может обладать определенное слово в склонении или спряжении. Для получения дополнительной информации посетите <a href='https://devamitta.github.io/dpd.rus/features/grammardict/' target='_blank'>веб-сайт DPD</a>.</p>",
        website="https://devamitta.github.io/dpd.rus/features/grammardict/",
        source_lang="pi",
        target_lang="ru",
    )
    dict_name = "ru-dpd-grammar"

    dict_vars = DictVariables(
        css_paths=[g.pth.dpd_css_and_fonts_path],
        js_paths=[g.pth.sorter_js_path],
        gd_path=g.pth.share_dir,
        md_path=g.pth.share_dir,
        dict_name=dict_name,
        icon_path=g.pth.dpd_logo_svg,
        font_path=g.pth.fonts_dir,
        zip_up=False,
        delete_original=False,
    )

    export_to_goldendict_with_pyglossary(
        dict_info, dict_vars, g.dict_data, include_slob=g.make_slob
    )

    if g.make_mdict:
        export_to_mdict(dict_info, dict_vars, g.dict_data)

if __name__ == "__main__":
    main()
