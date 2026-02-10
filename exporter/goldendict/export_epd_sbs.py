"""Compile HTML data for English to Pāḷi dictionary."""

from mako.template import Template
from minify_html import minify
from sqlalchemy.orm import Session
from typing import List, Tuple

from db.models import Lookup
from tools.css_manager import CSSManager
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr
from tools.utils import squash_whitespaces
from tools.utils_sbs import RenderedSizes, default_rendered_sizes
from tools.goldendict_exporter import DictEntry


def generate_epd_html(
    db_session: Session,
    pth: DPSPaths,
    show_ru_data=False,
) -> Tuple[List[DictEntry], RenderedSizes]:
    """generate html for english to pali dictionary using lookup table data"""

    size_dict = default_rendered_sizes()

    pr.green("generating epd html from lookup")

    header_templ = Template(filename=str(pth.dpd_header_plain_templ_path))
    header = str(header_templ.render(css="", js=""))

    css_manager = CSSManager()
    header = css_manager.update_style(header, "primary")

    # Final data dictionary
    epd_dict: dict = {}

    # 1. Process English EPD
    lookup_db = db_session.query(Lookup).filter(Lookup.epd != "").all()
    for lookup_entry in lookup_db:
        word = lookup_entry.lookup_key
        epd_entries = lookup_entry.epd_unpack
        html_entries = []
        for lemma_clean, pos, meaning_plus_case in epd_entries:
            entry_html = f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"
            html_entries.append(entry_html)
        
        epd_dict[word] = html_entries

    # 2. Process Russian RPD if enabled
    if show_ru_data:
        rpd_lookup_db = db_session.query(Lookup).filter(Lookup.rpd != "").all()
        for lookup_entry in rpd_lookup_db:
            word = lookup_entry.lookup_key
            rpd_entries = lookup_entry.rpd_unpack
            html_entries = []
            for lemma_clean, pos, meaning_plus_case in rpd_entries:
                entry_html = f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"
                html_entries.append(entry_html)
            
            if word in epd_dict:
                epd_dict[word].extend(html_entries)
            else:
                epd_dict[word] = html_entries

    epd_data_list: List[DictEntry] = []

    for word, html_entries in epd_dict.items():
        html_string = "<br>".join(html_entries)

        html = ""
        html += "<body>"
        html += f"<div class ='dpd'><p>{html_string}</p></div>"
        html += "</body></html>"

        html = squash_whitespaces(header) + minify(html)

        res = DictEntry(
            word=word,
            definition_html=html,
            definition_plain="",
            synonyms=[],
        )

        epd_data_list.append(res)
        size_dict["epd"] += len(html)

    pr.yes(len(epd_data_list))
    return epd_data_list, size_dict