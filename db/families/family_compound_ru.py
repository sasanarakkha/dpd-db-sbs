#!/usr/bin/env python3

"""Compile compound families and save to database."""

import json
import re

from db.db_helpers import get_db_session
from db.models import DbInfo, DpdHeadword, FamilyCompound
from tools.configger import config_test
from tools.degree_of_completion_ru import degree_of_completion_ru
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.superscripter import superscripter_uni

from tools.tools_for_ru_exporter import (
    make_short_ru_meaning,
    ru_replace_abbreviations,
)

from sqlalchemy.orm import Session, joinedload


def main() -> None:
    pr.tic()
    pr.yellow_title("compound families generator (ru)")

    if not (
        config_test("exporter", "make_dpd", "yes")
        or config_test("regenerate", "db_rebuild", "yes")
    ):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.ru))
        .filter(DpdHeadword.family_compound != "")
        .all()
    )

    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    cf_dict = create_comp_fam_dict(dpd_db)
    cf_dict = compile_cf_html_ru(dpd_db, cf_dict)
    add_cf_to_db(db_session, cf_dict)
    update_db_cache(db_session, cf_dict)

    db_session.close()

    # update anki
    if config_test("anki", "update", "yes"):
        from exporter.anki.anki_updater import family_updater

        anki_data_list = make_anki_data(cf_dict)
        deck = ["Family Compound RU"]
        family_updater(anki_data_list, deck)

    pr.toc()


def create_comp_fam_dict(dpd_db: list[DpdHeadword]) -> dict[str, dict]:
    pr.green_tmr("extracting compound families")

    cf_dict: dict[str, dict] = {}

    for i in dpd_db:
        for cf in i.family_compound_list:
            if cf == " ":
                pr.red("ERROR: spaces found please remove!")
            elif not cf:
                pr.red("ERROR: '' found please remove!")
            elif cf == "+":
                pr.red("ERROR: + found please remove!")

            test1 = re.findall(r"\bcomp\b", i.grammar) != []
            test2 = len(i.lemma_clean) < 30
            test3 = i.meaning_1

            if test1 and test2 and test3:
                if cf in cf_dict:
                    cf_dict[cf]["headwords"] += [i.lemma_1]
                else:
                    cf_dict[cf] = {
                        "headwords": [i.lemma_1],
                        "html_ru": "",
                        "data_ru": [],
                        "anki": [],
                    }

    pr.yes(len(cf_dict))
    return cf_dict


def compile_cf_html_ru(
    dpd_db: list[DpdHeadword], cf_dict: dict[str, dict]
) -> dict[str, dict]:
    pr.green_tmr("compiling html ru")

    for i in dpd_db:
        for cf in i.family_compound_list:
            if cf in cf_dict:
                if i.lemma_1 in cf_dict[cf]["headwords"]:
                    # rus
                    if not cf_dict[cf]["html_ru"]:
                        ru_html_string = "<table class='family'>"
                    else:
                        ru_html_string = cf_dict[cf]["html_ru"]

                    ru_meaning = make_short_ru_meaning(i, i.ru)
                    pos = ru_replace_abbreviations(i.pos)
                    ru_html_string += "<tr>"
                    ru_html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                    ru_html_string += f"<td><b>{pos}</b></td>"
                    ru_html_string += f"<td>{ru_meaning}</td>"
                    ru_html_string += f"<td>{degree_of_completion_ru(i)}</td>"
                    ru_html_string += "</tr>"

                    cf_dict[cf]["html_ru"] = ru_html_string

                    # rus data
                    if i.meaning_1:
                        cf_dict[cf]["data_ru"].append(
                            (
                                i.lemma_1,
                                pos,
                                ru_meaning,
                                degree_of_completion_ru(i, html=False),
                            )
                        )
                        # anki data
                        construction = i.construction_clean
                        cf_dict[cf]["anki"] += [
                            (i.lemma_1, pos, ru_meaning, construction)
                        ]

    for i in cf_dict:
        cf_dict[i]["html_ru"] += "</table>"
    pr.yes(len(cf_dict))
    return cf_dict


def add_cf_to_db(db_session: Session, cf_dict: dict[str, dict]) -> None:
    pr.green_tmr("updating db")

    for cf in cf_dict:
        # find in db
        cf_data = db_session.query(FamilyCompound).filter_by(compound_family=cf).first()
        if cf_data:
            cf_data.html_ru = cf_dict[cf]["html_ru"]
            cf_data.data_ru_pack(cf_dict[cf]["data_ru"])
            db_session.add(cf_data)
        else:
            pr.red(f"{cf} not found in db")

    db_session.commit()
    pr.yes("ok")


def make_anki_data(cf_dict: dict[str, dict]) -> list[tuple[str, str]]:
    """Make data list for anki updater."""

    anki_data_list = []

    for family in cf_dict:
        anki_family = f"<b>{family}</b>"
        html = "<table><tbody>"
        for row in cf_dict[family]["anki"]:
            headword, pos, meaning, construction = row
            html += "<tr valign='top'>"
            html += "<div style='color: #FFB380'>"
            html += f"<td>{headword}</td>"
            html += f"<td><div style='color: #FF6600'>{pos}</div></td>"
            html += f"<td><div style='color: #FFB380'>{meaning}</td>"
            html += f"<td><div style='color: #FF6600'>{construction}</div></td></tr>"
        html += "</tbody></table>"

        if len(html) > 131072:
            pr.red(f"{family} longer than 131072 characters")
        else:
            anki_data_list += [(anki_family, html)]

    return anki_data_list


def update_db_cache(db_session: Session, cf_dict: dict[str, dict]) -> None:
    """Update the db_info with cf_set for use in the exporter."""

    pr.green_tmr("adding DbInfo cache item")

    cf_set = set(cf_dict)

    cf_set_cache = db_session.query(DbInfo).filter_by(key="cf_set").first()

    if not cf_set_cache:
        cf_set_cache = DbInfo()

    cf_set_cache.key = "cf_set"
    cf_set_cache.value = json.dumps(sorted(cf_set), ensure_ascii=False, indent=1)
    db_session.add(cf_set_cache)
    db_session.commit()
    pr.yes("ok")


if __name__ == "__main__":
    main()
