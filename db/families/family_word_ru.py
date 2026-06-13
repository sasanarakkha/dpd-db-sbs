#!/usr/bin/env python3

"""Create an html table of all words belonging to the same family (ru)."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyWord
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

from sqlalchemy.orm import Session, joinedload


def main() -> None:
    pr.tic()
    pr.yellow_title("word families generator (ru)")

    if not (
        config_test("exporter", "make_dpd", "yes")
        or config_test("regenerate", "db_rebuild", "yes")
    ):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    wf_db = (
        db_session.query(DpdHeadword)
        .options(joinedload(DpdHeadword.ru))
        .filter(DpdHeadword.family_word != "")
        .all()
    )

    wf_db = sorted(wf_db, key=lambda x: pali_sort_key(x.lemma_1))

    wf_dict = make_word_fam_dict(wf_db)
    wf_dict = compile_wf_html_ru(wf_db, wf_dict)
    errors_list = add_wf_to_db(db_session, wf_dict)
    print_errors_list(errors_list)
    db_session.close()

    if config_test("anki", "update", "yes"):
        from exporter.anki.anki_updater import family_updater

        # word families
        anki_data_list = make_anki_data(wf_dict)
        deck = ["Family Word RU"]
        family_updater(anki_data_list, deck)

    pr.toc()


def make_word_fam_dict(wf_db: list[DpdHeadword]) -> dict[str, dict]:
    pr.green_tmr("extracting word families")

    # create a dict of all word families
    # word: {headwords: [], html: "", }

    wf_dict: dict[str, dict] = {}

    for i in wf_db:
        wf = i.family_word

        if " " in wf:
            pr.red("ERROR: spaces found please remove!")

        if wf in wf_dict:
            wf_dict[wf]["headwords"] += [i.lemma_1]
        else:
            wf_dict[wf] = {
                "headwords": [i.lemma_1],
                "html_ru": "",
                "data_ru": [],
            }

    pr.yes(len(wf_dict))
    return wf_dict


def compile_wf_html_ru(
    wf_db: list[DpdHeadword], wf_dict: dict[str, dict]
) -> dict[str, dict]:
    pr.green_tmr("compiling html ru")

    for i in wf_db:
        wf = i.family_word
        # rus
        if not wf_dict[wf]["html_ru"]:
            ru_html_string = "<table class='family'>"
        else:
            ru_html_string = wf_dict[wf]["html_ru"]

        ru_meaning = make_short_ru_meaning(i, i.ru)
        pos = ru_replace_abbreviations(i.pos)
        ru_html_string += "<tr>"
        ru_html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
        ru_html_string += f"<td><b>{pos}</b></td>"
        ru_html_string += f"<td>{ru_meaning}</td>"
        ru_html_string += f"<td>{degree_of_completion_ru(i)}</td>"
        ru_html_string += "</tr>"

        wf_dict[wf]["html_ru"] = ru_html_string

        # rus data
        wf_dict[wf]["data_ru"].append(
            (i.lemma_1, pos, ru_meaning, degree_of_completion_ru(i, html=False))
        )

    for i in wf_dict:
        wf_dict[i]["html_ru"] += "</table>"

    pr.yes(len(wf_dict))
    return wf_dict


def add_wf_to_db(db_session: Session, wf_dict: dict[str, dict]) -> list[str]:
    pr.green_tmr("adding to db")

    errors_list = []

    for wf in wf_dict:
        if len(wf_dict[wf]["headwords"]) < 2:
            errors_list += [wf]

        wf_data = db_session.query(FamilyWord).filter_by(word_family=wf).first()

        if wf_data:
            wf_data.html_ru = wf_dict[wf]["html_ru"]
            wf_data.data_ru_pack(wf_dict[wf]["data_ru"])
            db_session.add(wf_data)
        else:
            pr.red(f"{wf} not found in db")

    db_session.commit()
    pr.yes("ok")

    return errors_list


def print_errors_list(errors_list: list[str]) -> None:
    if len(errors_list) > 0:
        pr.red("ERROR: only 1 word in family:")
    for error in errors_list:
        pr.red(f"{error}")
    pr.red("")


def make_anki_data(wf_dict: dict[str, dict]) -> list[tuple[str, str]]:
    """Save to TSV for anki."""

    anki_data_list = []

    for i in wf_dict:
        html = "<table><tbody>"
        for row in wf_dict[i]["data_ru"]:
            headword, pos, meaning, degree = row
            html += "<tr valign='top'>"
            html += "<div style='color: #FFB380'>"
            html += f"<td>{headword}</td>"
            html += f"<td><div style='color: #FF6600'>{pos}</div></td>"
            html += f"<td><div style='color: #FFB380'>{meaning}</td>"
            html += f"<td><div style='color: #FF6600'>{degree}</div></td></tr>"

        html += "</tbody></table>"
        if len(html) > 131072:
            pr.red(f"{i} longer than 131072 characters")
        else:
            anki_data_list += [(i, html)]

    return anki_data_list


if __name__ == "__main__":
    main()
