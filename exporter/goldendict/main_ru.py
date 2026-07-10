#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Export DPD for GoldenDict and MDict."""

import csv
import pickle
from dataclasses import dataclass, field
from typing import List

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session

from exporter.goldendict.export_dpd_ru import generate_dpd_html
from exporter.goldendict.export_rpd import generate_epd_html
from exporter.goldendict.export_help_ru import generate_help_html
from exporter.goldendict.export_roots_ru import generate_root_html
from exporter.goldendict.export_variant_spelling_ru import (
    generate_variant_spelling_html,
)
from exporter.goldendict.helpers import make_roots_count_dict
from tools.cache_load import load_cf_set, load_idioms_set
from tools.configger import config_read, config_test
from tools.goldendict_exporter import (
    DictEntry,
    DictInfo,
    DictVariables,
    export_to_goldendict_with_pyglossary,
)
from tools.mdict_exporter import export_to_mdict
from tools.paths import ProjectPaths
from tools.paths_ru import RuPaths
from tools.printer import printer as pr
from tools.speech_marks import SpeechMarkManager, SpeechMarksDict
from tools.utils import RenderedSizes, sum_rendered_sizes


@dataclass
class GlobalVars:
    pth: ProjectPaths
    rupth: RuPaths
    db_session: Session
    speech_marks: SpeechMarksDict
    cf_set: set[str]
    idioms_set: set[str]
    roots_count_dict: dict[str, int]
    data_limit: int
    make_mdict: bool
    make_slob: bool
    paths: RuPaths
    rendered_sizes: List[RenderedSizes] = field(default_factory=list)
    dict_data: list[DictEntry] = field(default_factory=list)


def build_global_vars() -> GlobalVars:
    pth = ProjectPaths()
    rupth = RuPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # config tests
    make_mdict: bool = False
    if config_test("dictionary", "make_mdict", "yes"):
        make_mdict = True

    return GlobalVars(
        pth=pth,
        rupth=rupth,
        db_session=db_session,
        speech_marks=SpeechMarkManager().get_speech_marks(),
        cf_set=load_cf_set(),  # type: ignore[arg-type]
        idioms_set=load_idioms_set(),  # type: ignore[arg-type]
        roots_count_dict=make_roots_count_dict(db_session),
        data_limit=int(config_read("dictionary", "data_limit") or "0"),
        make_mdict=make_mdict,
        make_slob=config_read("goldendict", "make_slob", "no") == "yes",
        paths=rupth,
    )


def main():
    pr.tic()
    pr.yellow_title("exporting dpd to goldendict and mdict (ru)")

    if not config_test("exporter", "make_dpd", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    g = build_global_vars()

    dpd_data_list, sizes = generate_dpd_html(
        g.db_session,
        g.rupth,
        g.speech_marks,
        g.cf_set,
        g.idioms_set,
        g.data_limit,
    )
    g.rendered_sizes.append(sizes)

    if g.data_limit == 0:
        root_data_list, sizes = generate_root_html(
            g.db_session, g.pth, g.roots_count_dict, g.rupth
        )
        g.rendered_sizes.append(sizes)

        variant_spelling_data_list, sizes = generate_variant_spelling_html(
            g.pth, g.rupth
        )
        g.rendered_sizes.append(sizes)

        epd_data_list, sizes = generate_epd_html(g.db_session, g.pth, g.rupth)
        g.rendered_sizes.append(sizes)

        help_data_list, sizes = generate_help_html(g.db_session, g.pth, g.rupth)
        g.rendered_sizes.append(sizes)

        g.db_session.close()

    else:
        root_data_list = []
        variant_spelling_data_list = []
        epd_data_list = []
        help_data_list = []

    g.dict_data = (
        dpd_data_list
        + root_data_list
        + variant_spelling_data_list
        + epd_data_list
        + help_data_list
    )

    write_limited_datalist(g)
    write_size_dict(g.pth, sum_rendered_sizes(g.rendered_sizes))
    prepare_export_to_goldendict_mdict(g)

    pr.toc()


def prepare_export_to_goldendict_mdict(g: GlobalVars) -> None:
    """Prepare info and variables for export."""

    description = """
    <p>Электронный Словарь Пали Дост. Бодхираса</p>
    <p>Переведен на русский Бхиккху Дэвамитта</p>
    <p>Для более детальной информации можено посетить
    <a href=\"https://devamitta.github.io/dpd.rus/\">
    сайт Пали Словаря</a></p>
    и оригинальный сайт <a href=\"https://digitalpalidictionary.github.io\">
    Digital Pāḷi Dictionary</a></p>
    """

    dict_info = DictInfo(
        bookname="Электронный Словарь Пали",
        author="Дост. Бодхираса, переведено Бхиккху Дэвамитта",
        description=description,
        website="https://devamitta.github.io/dpd.rus/",
        source_lang="pi",
        target_lang="ru",
    )

    dict_name = "ru-dpd"

    dict_var = DictVariables(
        css_paths=[g.paths.dpd_css_and_fonts_path],
        js_paths=[
            g.paths.family_compound_json,
            g.paths.family_compound_template_js,
            g.paths.family_idiom_json,
            g.paths.family_idiom_template_js,
            g.paths.family_root_json,
            g.paths.family_root_template_js,
            g.paths.family_set_json,
            g.paths.family_set_template_js,
            g.paths.family_word_json,
            g.paths.family_word_template_js,
            g.paths.feedback_template_js,
            g.paths.frequency_template_js,
            g.paths.main_js_path,
        ],
        gd_path=g.paths.share_dir,
        md_path=g.paths.share_dir,
        dict_name=dict_name,
        icon_path=g.paths.dpd_logo_svg,
        font_path=g.paths.fonts_dir,
        zip_up=False,
        delete_original=False,
    )

    export_to_goldendict_with_pyglossary(
        dict_info,
        dict_var,
        g.dict_data,
        include_slob=g.make_slob,
    )

    if g.make_mdict and g.data_limit == 0:
        export_to_mdict(dict_info, dict_var, g.dict_data)


def write_size_dict(pth: ProjectPaths, size_dict):
    pr.green_tmr("writing size_dict")
    filename = pth.temp_dir.joinpath("size_dict.tsv")

    with filename.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter="\t")
        for key, value in size_dict.items():
            writer.writerow([key, value])

    pr.yes("ok")


def write_limited_datalist(g: GlobalVars):
    """A limited dataset for troubleshooting purposes"""

    limited_data = [item for item in g.dict_data if item.word.startswith("ab")]

    with open("temp/limited_data_list", "wb") as file:
        pickle.dump(limited_data, file)


if __name__ == "__main__":
    main()
