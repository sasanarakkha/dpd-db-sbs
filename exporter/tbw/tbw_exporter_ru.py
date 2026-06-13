#!/usr/bin/env python3

"""A simple system of for Pāḷi word lookup consisting of:
1. inflection to headwords
2. dictionary data for EBTS.
3. compound deconstruction

Export to `FDG` repo
"""

import json

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.configger import config_test
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.printer import printer as pr
from tools.cst_sc_text_sets import make_sc_text_set
from tools.meaning_construction import summarize_construction
from tools.paths import ProjectPaths
from tools.paths_ru import RuPaths

from tools.tools_for_ru_exporter import (
    make_ru_meaning_simpl,
    ru_replace_abbreviations,
)


class ProgData_ru:
    def __init__(self) -> None:
        pr.green_tmr("setting up data")
        self.pth: ProjectPaths = ProjectPaths()
        self.rupth: RuPaths = RuPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        dpd_db = self.db_session.query(DpdHeadword).all()
        self.dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))
        self.deconstructor_db = (
            self.db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
        )
        self.variants_db = (
            self.db_session.query(Lookup).filter(Lookup.variant != "").all()
        )
        self.spelling_db = (
            self.db_session.query(Lookup).filter(Lookup.spelling != "").all()
        )
        self.word_set: set[str] = set()
        self.deconstructed_splits_set: set[str] = set()
        self.matched_set: set[str] = set()
        self.i2h_dict: dict[str, list[str]] = {}
        self.unmatched_set: set[str] = set()
        self.headwords_set: set[str] = set()
        self.dpd_dict: dict[str, str] = {}
        self.deconstructor_dict: dict[str, str] = {}
        pr.yes("ok")


def generate_sc_word_set(g: ProgData_ru) -> None:
    sc_text_list = [
        "vin1",
        "vin2",
        "vin3",
        "vin4",
        "vin5",
        "dn1",
        "dn2",
        "dn3",
        "mn1",
        "mn2",
        "mn3",
        "sn1",
        "sn2",
        "sn3",
        "sn4",
        "sn5",
        "an1",
        "an2",
        "an3",
        "an4",
        "an5",
        "an6",
        "an7",
        "an8",
        "an9",
        "an10",
        "an11",
        "kn1",
        "kn2",
        "kn3",
        "kn4",
        "kn5",
        "kn8",
        "kn9",
    ]

    sc_word_set = make_sc_text_set(g.pth, sc_text_list)
    g.word_set = sc_word_set


def generate_deconstructed_word_set(g: ProgData_ru) -> None:
    """make a set of all words in deconstructed compounds"""

    pr.green_tmr("making deconstructor splits set")
    for i in g.deconstructor_db:
        if i.lookup_key in g.word_set:
            g.matched_set.add(i.lookup_key)
            deconstructions = i.deconstructor_unpack
            for deconstruction in deconstructions:
                g.deconstructed_splits_set.update(deconstruction.split(" + "))
    pr.yes(len(g.deconstructed_splits_set))


def generate_i2h_dict(g: ProgData_ru) -> None:
    """make an inflections to headwords dictionary"""

    pr.green_tmr("making inflection2headwords dict")
    for i in g.dpd_db:
        inflections = i.inflections_list_all  # include api ca eva iti
        for inflection in inflections:
            test1 = inflection in g.word_set or inflection in g.deconstructed_splits_set
            test2 = "(gram)" not in i.meaning_1
            if test1 and test2:
                g.matched_set.add(inflection)
                g.i2h_dict.setdefault(inflection, []).append(i.lemma_1)
    pr.yes(len(g.i2h_dict))


def sort_i2h_dict(g: ProgData_ru) -> None:
    """sort i2h dict by values"""

    pr.green_tmr("sorting i2h_dict")
    for inflection, headwords in g.i2h_dict.items():
        g.i2h_dict[inflection] = pali_list_sorter(headwords)
    pr.yes(len(g.i2h_dict))


def generate_unmatched_word_set(g: ProgData_ru) -> None:
    """make a set of unmatched words"""

    pr.green_tmr("making set of unmatched words")
    g.unmatched_set = g.word_set - g.matched_set
    pr.yes(len(g.unmatched_set))


def generate_ebt_headwords_set(g: ProgData_ru) -> None:
    """make a set of headwords in ebts"""

    pr.green_tmr("making headwords set")
    for values in g.i2h_dict.values():
        g.headwords_set.update(values)
    pr.yes(len(g.headwords_set))


def generate_dpd_ebt_dict(g: ProgData_ru) -> None:
    """make a dict of dpd data - only words in ebts"""

    pr.green_tmr("making dpd ebts dict")
    for i in g.dpd_db:
        if i.lemma_1 in g.headwords_set:
            pos_ru = ru_replace_abbreviations(i.pos, "gram")
            string = f"{pos_ru}. "
            string += make_ru_meaning_simpl(i)
            if i.construction:
                string += f" [{summarize_construction(i)}]"
            g.dpd_dict[i.lemma_1] = string

    g.dpd_dict = dict(sorted(g.dpd_dict.items(), key=lambda x: pali_sort_key(x[0])))
    pr.yes(len(g.dpd_dict))


def generate_deconstructor_dict(g: ProgData_ru) -> None:
    """make a dict of all deconstructed compounds"""

    pr.green_tmr("making deconstructor dict")

    for i in g.deconstructor_db:
        if i.lookup_key not in g.dpd_dict and i.lookup_key in g.word_set:
            deconstructions = i.deconstructor_unpack
            string = "<br>".join(deconstructions)
            g.deconstructor_dict[i.lookup_key] = string
    pr.yes(len(g.deconstructor_dict))


def deconstructor_dict_add_variants(g: ProgData_ru) -> None:
    """add variant readings to deconstructor data"""

    pr.green_tmr("adding variants")
    var_counter = 0
    for i in g.variants_db:
        if i.lookup_key in g.word_set:
            variant_string = f"variant reading of <i>{i.variant_unpack[0]}</i>"
            if i.lookup_key in g.deconstructor_dict:
                g.deconstructor_dict[i.lookup_key] += f"<br>{variant_string}"
                var_counter += 1
            else:
                g.deconstructor_dict[i.lookup_key] = variant_string
                var_counter += 1
    pr.yes(var_counter)


def deconstructor_dict_add_spelling_mistakes(g: ProgData_ru) -> None:
    """add spelling mistakes to deconstructor data"""

    pr.green_tmr("adding spelling mistakes")
    spell_counter = 0
    for i in g.spelling_db:
        if i.lookup_key in g.word_set:
            spelling_string = f"incorrect spelling of <i>{i.spelling_unpack[0]}</i>"
            if i.lookup_key in g.deconstructor_dict:
                g.deconstructor_dict[i.lookup_key] += f"<br>{spelling_string}"
                spell_counter += 1
            else:
                g.deconstructor_dict[i.lookup_key] = spelling_string
                spell_counter += 1
    pr.yes(spell_counter)


def sort_deconstructor_dict(g: ProgData_ru) -> None:
    """sort deconstructor dict"""

    pr.green_tmr("sorting deconstructor dict")
    g.deconstructor_dict = dict(
        sorted(g.deconstructor_dict.items(), key=lambda x: pali_sort_key(x[0]))
    )
    pr.yes(len(g.deconstructor_dict))


def save_js_files_for_fdg(g: ProgData_ru) -> None:
    """saving .js files for fdg"""

    pr.green_tmr("saving .js files for fdg")

    i2h_json_dump = json.dumps(g.i2h_dict, ensure_ascii=False, indent=2)
    with g.pth.fdg_i2h_js_path.open("w", encoding="utf-8") as f:
        f.write(f"dpd_i2h = {i2h_json_dump}")

    dpd_json_dump = json.dumps(g.dpd_dict, ensure_ascii=False, indent=2)
    with g.rupth.fdg_dpd_ebts_js_ru_path.open("w", encoding="utf-8") as f:
        f.write(f"let dpd_ebts = {dpd_json_dump}")

    pr.yes("ok")


def main() -> None:
    pr.tic()
    pr.yellow_title("export dpd data for TBW and Sutta Central")

    if not config_test("exporter", "make_tbw", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    g = ProgData_ru()
    generate_sc_word_set(g)
    generate_deconstructed_word_set(g)
    generate_i2h_dict(g)
    sort_i2h_dict(g)
    generate_unmatched_word_set(g)
    generate_ebt_headwords_set(g)
    generate_dpd_ebt_dict(g)
    generate_deconstructor_dict(g)
    # deconstructor_dict_add_variants(g) # format has changed
    deconstructor_dict_add_spelling_mistakes(g)
    sort_deconstructor_dict(g)

    save_js_files_for_fdg(g)

    pr.toc()


if __name__ == "__main__":
    main()
