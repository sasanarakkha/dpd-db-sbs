"""Compile HTML data for Russian to Pāḷi dictionary."""

import re

from mako.template import Template
from minify_html import minify
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
from typing import List, Tuple

from db.db_helpers import get_db_session

from db.models import DpdHeadword, DpdRoot
from tools.css_manager import CSSManager
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.paths_ru import RuPaths
from tools.printer import printer as pr
from tools.utils import RenderedSizes, default_rendered_sizes, squash_whitespaces
from tools.goldendict_exporter import DictEntry
from tools.tools_for_ru_exporter import (
    ru_replace_abbreviations,
)


def generate_epd_html(
    db_session: Session,
    pth: ProjectPaths,
    rupth: RuPaths,
) -> Tuple[List[DictEntry], RenderedSizes]:
    """generate html for russian to pali dictionary"""

    size_dict = default_rendered_sizes()

    pr.green("generating epd html")

    dpd_db: list[DpdHeadword] = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.ru)).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    roots_db: list[DpdRoot] = db_session.query(DpdRoot).all()

    epd: dict = {}
    pos_exclude_list = ["abbrev", "cs", "letter", "root", "suffix", "ve"]

    header_templ = Template(filename=str(rupth.dpd_header_plain_templ_path))

    header = str(header_templ.render())

    # Add Variables and fonts
    css_manager = CSSManager()
    header = css_manager.update_style(header, "primary")

    for counter, i in enumerate(dpd_db):
        # generate ru-pali
        if (
            i.ru
            and i.ru.ru_meaning
            and i.pos not in pos_exclude_list
        ):
            i.ru.ru_meaning = re.sub(r"\?\?", "", i.ru.ru_meaning)

            # remove all space brackets
            ru_meanings_clean = re.sub(r" \(.+?\)", "", i.ru.ru_meaning)
            # remove all brackets space
            ru_meanings_clean = re.sub(r"\(.+?\) ", "", ru_meanings_clean)
            # remove space at start and fin
            ru_meanings_clean = re.sub(r"(^ | $)", "", ru_meanings_clean)
            # remove double spaces
            ru_meanings_clean = re.sub(r"  ", " ", ru_meanings_clean)
            # remove space around ;
            ru_meanings_clean = re.sub(r" ;|; ", ";", ru_meanings_clean)
            # remove т.д.
            ru_meanings_clean = re.sub(r"т\.д\. ", "", ru_meanings_clean)
            # remove !
            ru_meanings_clean = re.sub(r"!", "", ru_meanings_clean)
            # remove ?
            ru_meanings_clean = re.sub(r"\\?", "", ru_meanings_clean)
            ru_meanings_list = ru_meanings_clean.split(";")

            pos: str = ru_replace_abbreviations(i.pos)

            for ru_meaning in ru_meanings_list:
                if ru_meaning in epd.keys():
                    epd_string = f"{epd[ru_meaning]}<br><b class='epd'>{i.lemma_clean}</b> {pos}. {i.ru.ru_meaning}"
                    epd[ru_meaning] = epd_string

                if ru_meaning not in epd.keys():
                    epd_string = (
                        f"<b class='epd'>{i.lemma_clean}</b> {pos}. {i.ru.ru_meaning}"
                    )
                    epd.update({ru_meaning: epd_string})

    for counter, i in enumerate(roots_db):
            root_ru_meanings_list: list = i.root_ru_meaning.split(", ")

            for root_ru_meaning in root_ru_meanings_list:
                if root_ru_meaning in epd.keys():
                    epd_string = f"{epd[root_ru_meaning]}<br><b class='epd'>{i.root}</b> корень. {i.root_ru_meaning}"
                    epd[root_ru_meaning] = epd_string

                if root_ru_meaning not in epd.keys():
                    epd_string = (
                        f"<b class='epd'>{i.root}</b> корень. {i.root_ru_meaning}"
                    )
                    epd.update({root_ru_meaning: epd_string})

    epd_data_list: List[DictEntry] = []

    for counter, (word, html_string) in enumerate(epd.items()):
        html = ""
        html += "<body>"
        html += f"<div class ='dpd'><p>{html_string}</p></div>"
        html += "</body></html>"

        size_dict["epd"] += len(html)
        size_dict["epd_header"] += len(squash_whitespaces(header))

        html = squash_whitespaces(header) + minify(html)

        res = DictEntry(
            word=word,
            definition_html=html,
            definition_plain="",
            synonyms=[],
        )

        epd_data_list.append(res)

    pr.yes(len(epd_data_list))

    return epd_data_list, size_dict


if __name__ == "__main__":
    pth = ProjectPaths()
    rupth = RuPaths()
    db_session = get_db_session(pth.dpd_db_path)
    generate_epd_html(db_session, pth, rupth)
