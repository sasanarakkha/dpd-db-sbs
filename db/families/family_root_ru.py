#!/usr/bin/env python3

"""Create an html list of all words belonging to the same root family
and add to db (ru)."""

import re


from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, FamilyRoot
from scripts.build.anki_updater import family_updater
from tools.configger import config_test
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.superscripter import superscripter_uni

from tools.degree_of_completion_ru import degree_of_completion_ru

from tools.tools_for_ru_exporter import (
    make_short_ru_meaning,
    ru_replace_abbreviations,
)

from sqlalchemy.orm import joinedload


def main():
    pr.tic()
    pr.yellow_title("root families (ru)")

    if not (
        config_test("exporter", "make_dpd", "yes")
        or config_test("regenerate", "db_rebuild", "yes")
    ):
        pr.green_tmr("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.ru))
        .filter(DpdHeadword.family_root != "")
        .all()
    )

    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    roots_db = db_session.query(DpdRoot).all()
    roots_db = sorted(roots_db, key=lambda x: pali_sort_key(x.root))

    rf_dict, bases_dict = make_roots_family_dict_and_bases_dict(dpd_db)
    rf_dict = compile_rf_html_ru(dpd_db, rf_dict)
    add_rf_to_db(db_session, rf_dict)
    # update_lookup_table(db_session) # Already done by the main script

    # generate_root_info_html and generate_root_matrix are shared, but they use
    # root meanings. If we want RU specific matrix, we'd need more changes.
    # For now, let's just keep parity with structure.

    db_session.close()

    if config_test("anki", "update", "yes"):
        anki_data_list = make_anki_data(rf_dict)
        deck = ["Family Root RU"]
        family_updater(anki_data_list, deck)

    pr.toc()


def make_roots_family_dict_and_bases_dict(dpd_db):
    pr.green_tmr("extracting root families and bases")
    rf_dict = {}
    bases_dict = {}
    for i in dpd_db:
        # compile root subfamilies
        family = i.root_family_key

        if family not in rf_dict:
            rf_dict[family] = {
                "root_key": i.root_key,
                "root_family": i.family_root,
                "root_ru_meaning": i.rt.root_ru_meaning,
                "headwords": [i.lemma_1],
                "html_ru": "",
                "count": 1,
                "meaning_ru": i.rt.root_ru_meaning,
                "data_ru": [],
                "anki": [],
            }
        else:
            rf_dict[family]["headwords"] += [i.lemma_1]
            rf_dict[family]["count"] += 1

        # compile bases
        base = re.sub("^.+> ", "", i.root_base)

        if base:
            if i.root_key not in bases_dict:
                bases_dict[i.root_key] = {base}
            else:
                bases_dict[i.root_key].add(base)

    pr.yes(len(rf_dict))
    return rf_dict, bases_dict


def compile_rf_html_ru(dpd_db: list[DpdHeadword], rf_dict):
    pr.green_tmr("compiling html ru")

    for __counter__, i in enumerate(dpd_db):
        family = i.root_family_key

        if i.lemma_1 in rf_dict[family]["headwords"]:
            # rus
            if not rf_dict[family]["html_ru"]:
                ru_html_string = "<table class='family'>"
            else:
                ru_html_string = rf_dict[family]["html_ru"]

            ru_meaning = make_short_ru_meaning(i, i.ru)
            pos = ru_replace_abbreviations(i.pos)
            ru_html_string += "<tr>"
            ru_html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
            ru_html_string += f"<td><b>{pos}</b></td>"
            ru_html_string += f"<td>{ru_meaning}</td>"
            ru_html_string += f"<td>{degree_of_completion_ru(i)}</td>"
            ru_html_string += "</tr>"

            rf_dict[family]["html_ru"] = ru_html_string

            # rus data
            rf_dict[family]["data_ru"].append(
                (i.lemma_1, pos, ru_meaning, degree_of_completion_ru(i, html=False))
            )

            # anki data
            anki_family = f"<b>{i.family_root}</b> "
            anki_family += f"{i.rt.root_group} ({i.rt.root_ru_meaning})"
            cf_construction = i.construction_clean
            if not i.meaning_1:
                cf_construction = f"-{cf_construction}"
            rf_dict[family]["anki"].append(
                (anki_family, i.lemma_1, pos, ru_meaning, cf_construction)
            )

    for rf in rf_dict:
        header_ru = make_root_header_ru(rf_dict, rf)
        rf_dict[rf]["html_ru"] = header_ru + rf_dict[rf]["html_ru"] + "</table>"

    pr.yes(len(rf_dict))

    return rf_dict


def make_root_header_ru(rf_dict, rf):
    header = "<p class='heading underlined'>"
    if rf_dict[rf]["count"] == 1:
        header += "<b>1</b> слово принадлежит к семье корня "
    else:
        header += f"<b>{rf_dict[rf]['count']}</b> слов(а) принадлежат к семье корня "
    header += f"<b>{rf_dict[rf]['root_family']}</b> ({rf_dict[rf]['meaning_ru']})</p>"
    return header


def add_rf_to_db(db_session, rf_dict):
    pr.green_tmr("updating db")

    for rf in rf_dict:
        # find in db
        root_family = (
            db_session.query(FamilyRoot)
            .filter_by(root_family_key=rf, root_key=rf_dict[rf]["root_key"])
            .first()
        )

        if root_family:
            root_family.root_ru_meaning = rf_dict[rf]["root_ru_meaning"]
            root_family.html_ru = rf_dict[rf]["html_ru"]
            root_family.data_ru_pack(rf_dict[rf]["data_ru"])
            db_session.add(root_family)
        else:
            pr.red(f"{rf} not found in db")

    db_session.commit()
    pr.yes("ok")


def make_anki_data(rf_dict):
    """Create anki_data_list for updating"""

    pr.green_tmr("making anki data")

    anki_data_list = []

    for i in rf_dict:
        html = "<table><tbody>"
        family, headword, pos, meaning, construction = "", "", "", "", ""
        for row in rf_dict[i]["anki"]:
            family, headword, pos, meaning, construction = row
            html += "<tr valign='top'>"
            html += "<div style='color: #FFB380'>"
            html += f"<td>{headword}</td>"
            html += f"<td><div style='color: #FF6600'>{pos}</div></td>"
            html += f"<td><div style='color: #FFB380'>{meaning}</td>"
            if construction.startswith("-"):
                construction = construction.lstrip("-")
                html += (
                    f"<td><div style='color: #421B01'>{construction}</div></td></tr>"
                )
            else:
                html += (
                    f"<td><div style='color: #FF6600'>{construction}</div></td></tr>"
                )

        html += "</tbody></table>"
        if len(html) > 131072:
            pr.red(f"{i} longer than 131072 characters")
        else:
            anki_data_list += [(family, html)]

    pr.yes(len(anki_data_list))

    return anki_data_list


if __name__ == "__main__":
    main()
