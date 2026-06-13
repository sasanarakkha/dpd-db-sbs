"""Compile HTML data for English to Pāḷi dictionary."""

from minify_html import minify
from sqlalchemy.orm import Session
from typing import List, Tuple

from db.models import Lookup
from tools.goldendict_exporter import DictEntry
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr
from tools.utils import (
    RenderedSizes,
    default_rendered_sizes,
    extract_body,
    squash_whitespaces,
)
from exporter.jinja2_env import get_jinja2_env
from exporter.goldendict.data_classes_dps import EpdData


class EpdDataSBS(EpdData):
    def __init__(self, lookup_key, html_entries, pth, jinja_env):
        self.lookup_key = lookup_key
        self.html_string = "<br>".join(html_entries)
        self.pth = pth
        self.jinja_env = jinja_env
        self.header = self._generate_header()


def generate_epd_html(
    db_session: Session,
    pth: DPSPaths,
    show_ru_data=False,
    show_ta_data=False,
) -> Tuple[List[DictEntry], RenderedSizes]:
    """generate html for english to pali dictionary using lookup table data"""

    size_dict = default_rendered_sizes()

    pr.green_tmr("generating epd html from lookup")

    jinja_env = get_jinja2_env("exporter/goldendict/sbs_templates")
    template = jinja_env.get_template("epd_sbs.jinja")

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
                entry_html = (
                    f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"
                )
                html_entries.append(entry_html)

            if word in epd_dict:
                epd_dict[word].extend(html_entries)
            else:
                epd_dict[word] = html_entries

    # 3. Process Tamil TPD if enabled
    if show_ta_data:
        tpd_lookup_db = db_session.query(Lookup).filter(Lookup.tpd != "").all()
        for lookup_entry in tpd_lookup_db:
            word = lookup_entry.lookup_key
            tpd_entries = lookup_entry.tpd_unpack
            html_entries = []
            for lemma_clean, pos, meaning_plus_case in tpd_entries:
                entry_html = (
                    f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"
                )
                html_entries.append(entry_html)
            if word in epd_dict:
                epd_dict[word].extend(html_entries)
            else:
                epd_dict[word] = html_entries

    epd_data_list: List[DictEntry] = []

    for word, html_entries in epd_dict.items():
        data = EpdDataSBS(word, html_entries, pth, jinja_env)

        html_rendered = template.render(d=data)

        # Re-calculate parts for parity
        header = data.header
        body = extract_body(html_rendered)

        final_html = squash_whitespaces(header) + minify(body)

        size_dict["epd"] += len(final_html)
        size_dict["epd_header"] += len(squash_whitespaces(header))

        res = DictEntry(
            word=word,
            definition_html=final_html,
            definition_plain="",
            synonyms=[],
        )

        epd_data_list.append(res)

    pr.yes(len(epd_data_list))
    return epd_data_list, size_dict
