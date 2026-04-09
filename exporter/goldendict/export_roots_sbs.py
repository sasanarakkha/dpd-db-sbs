"""Compile HTML data for Roots dictionary."""

import re
from typing import Dict, List, Tuple

from minify_html import minify
from sqlalchemy.orm import Session

from db.models import DpdRoot, FamilyRoot
from tools.goldendict_exporter import DictEntry
from tools.niggahitas import add_niggahitas
from tools.paths_dps import DPSPaths
from tools.printer import printer as pr
from tools.utils import squash_whitespaces
from tools.utils_sbs import RenderedSizes, default_rendered_sizes
from exporter.jinja2_env import get_jinja2_env
from exporter.goldendict.data_classes_dps import RootsData


def generate_root_html(
    db_session: Session,
    pth: DPSPaths,
    roots_count_dict: Dict[str, int],
    show_ru_data=False,
) -> Tuple[List[DictEntry], RenderedSizes]:
    """compile html components for each pali root"""

    pr.green_tmr("generating roots html")
    size_dict = default_rendered_sizes()
    root_data_list: List[DictEntry] = []

    jinja_env = get_jinja2_env("exporter/goldendict/sbs_templates")

    roots_db = db_session.query(DpdRoot).all()

    for counter, r in enumerate(roots_db):
        frs = db_session.query(FamilyRoot).filter(FamilyRoot.root_key == r.root).all()

        data = RootsData(
            r=r,
            roots_count_dict=roots_count_dict,
            pth=pth,
            jinja_env=jinja_env,
            frs=frs,
        )

        template = jinja_env.get_template("root_headword_sbs.jinja")
        html = template.render(d=data)

        # Re-calculate parts for parity
        header = data.header
        body_start = html.find("<body>")
        body = html[body_start:]

        final_html = squash_whitespaces(header) + minify(body)

        size_dict["root_definition"] += len(final_html)

        synonyms: set = set()
        synonyms.add(r.root_clean)
        synonyms.add(re.sub("√", "", r.root))
        synonyms.add(re.sub("√", "", r.root_clean))

        for fr in frs:
            synonyms.add(fr.root_family)
            synonyms.add(re.sub("√", "", fr.root_family))

        synonyms = set(add_niggahitas(list(synonyms)))
        size_dict["root_synonyms"] += len(str(synonyms))

        res = DictEntry(
            word=r.root,
            definition_html=final_html,
            definition_plain="",
            synonyms=list(synonyms),
        )

        root_data_list.append(res)

    pr.yes(len(root_data_list))
    return root_data_list, size_dict

