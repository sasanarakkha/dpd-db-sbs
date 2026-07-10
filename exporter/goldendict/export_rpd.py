"""Compile HTML data for Russian to Pāḷi dictionary."""

from minify_html import minify
from sqlalchemy.orm import Session

from db.models import Lookup
from tools.goldendict_exporter import DictEntry
from tools.paths import ProjectPaths
from tools.paths_ru import RuPaths
from tools.printer import printer as pr
from tools.utils import (
    RenderedSizes,
    default_rendered_sizes,
    extract_body,
    squash_whitespaces,
)
from exporter.jinja2_env import get_jinja2_env
from exporter.goldendict.data_classes_dps import RpdData


def generate_epd_html(
    db_session: Session,
    pth: ProjectPaths,
    rupth: RuPaths,
) -> tuple[list[DictEntry], RenderedSizes]:
    """generate html for russian to pali dictionary using lookup table data"""

    size_dict = default_rendered_sizes()

    pr.green("generating rpd html from lookup")

    jinja_env = get_jinja2_env("exporter/goldendict/ru_components/templates")
    template = jinja_env.get_template("rpd_ru.jinja")

    lookup_db = db_session.query(Lookup).filter(Lookup.rpd != "").all()

    epd_data_list: list[DictEntry] = []

    if not lookup_db:
        pr.yes(0)
        return epd_data_list, size_dict

    # The plain header has no per-entry variables, so it is identical for every
    # entry — generate it once instead of per row.
    header = RpdData(lookup_db[0], pth, jinja_env).header
    header_squashed = squash_whitespaces(header)

    for lookup_entry in lookup_db:
        # Same html-string logic as RpdData._generate_html_string.
        html_string = "<br>".join(
            f"<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}"
            for lemma_clean, pos, meaning_plus_case in lookup_entry.rpd_unpack
        )

        html_rendered = template.render(
            d={"header": header, "html_string": html_string}
        )

        # Re-calculate parts for parity
        body = extract_body(html_rendered)

        final_html = header_squashed + minify(body)

        size_dict["epd"] += len(final_html)
        size_dict["epd_header"] += len(header_squashed)

        res = DictEntry(
            word=lookup_entry.lookup_key,
            definition_html=final_html,
            definition_plain="",
            synonyms=[],
        )

        epd_data_list.append(res)

    pr.yes(len(epd_data_list))

    return epd_data_list, size_dict
