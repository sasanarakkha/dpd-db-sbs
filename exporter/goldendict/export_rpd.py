"""Compile HTML data for Russian to Pāḷi dictionary."""

from mako.template import Template
from minify_html import minify
from sqlalchemy.orm import Session
from typing import List, Tuple

from db.models import Lookup
from tools.css_manager import CSSManager
from tools.paths_ru import RuPaths
from tools.printer import printer as pr
from tools.utils import RenderedSizes, default_rendered_sizes, squash_whitespaces
from tools.goldendict_exporter import DictEntry


def generate_epd_html(
    db_session: Session,
    pth: RuPaths, # Keep this for compatibility with main_ru.py
    rupth: RuPaths,
) -> Tuple[List[DictEntry], RenderedSizes]:
    """generate html for russian to pali dictionary using lookup table data"""

    size_dict = default_rendered_sizes()

    pr.green("generating rpd html from lookup")

    header_templ = Template(filename=str(rupth.dpd_header_plain_templ_path))
    header = str(header_templ.render(css="", js=""))

    css_manager = CSSManager()
    header = css_manager.update_style(header, "primary")

    lookup_db = db_session.query(Lookup).filter(Lookup.rpd != "").all()

    epd_data_list: List[DictEntry] = []

    for lookup_entry in lookup_db:
        rpd_entries = lookup_entry.rpd_unpack

        html_entries = []
        for lemma_clean, pos, meaning_plus_case in rpd_entries:
            entry_html = f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"
            html_entries.append(entry_html)

        html_string = "<br>".join(html_entries)

        html = ""
        html += "<body>"
        html += f"<div class ='dpd'><p>{html_string}</p></div>"
        html += "</body></html>"

        html = squash_whitespaces(header) + minify(html)

        res = DictEntry(
            word=lookup_entry.lookup_key,
            definition_html=html,
            definition_plain="",
            synonyms=[],
        )

        epd_data_list.append(res)
        size_dict["epd"] += len(html)

    pr.yes(len(epd_data_list))
    return epd_data_list, size_dict