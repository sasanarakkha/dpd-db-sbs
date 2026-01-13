#!/usr/bin/env python3

"""SBS Example Consistency Tests."""

import re
from typing import List, Tuple, Optional

from sqlalchemy.orm import Session
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword, SBS
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def run_sbs_consistency_tests():
    print("[bright_yellow]run sbs consistency tests")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # tests
    results_list = []

    results_list.append(check_pat_consistency(db_session))
    results_list.append(check_dhp_source_consistency(db_session))
    results_list.append(check_dhp_triplet_consistency(db_session))
    results_list.append(check_vib_consistency(db_session))
    results_list.append(check_class_consistency(db_session))
    results_list.append(check_discourses_consistency(db_session))
    results_list.append(check_class_anki_consistency(db_session))
    results_list.append(check_discourses_source_prefix(db_session))
    results_list.append(check_sbs_example_consistency(db_session))
    results_list.append(check_sbs_index_mapping(db_session))
    results_list.extend(check_bold_tags(db_session))
    results_list.append(check_class_translation_uniqueness(db_session))

    for name, results, count, solution in results_list:
        print(f"[green]{name.replace('_', ' ')} [{count}]")
        if count > 0:
            print(f"solution: {solution}")
            if results:
                print(results)
        print()


def check_dhp_source_consistency(
    db_session: Session,
) -> Tuple[str, Optional[str], int, str]:
    r"""If meaning_1 and (DpdHeadword.source_1 or DpdHeadword.source_2) contains "DHP\d+", then SBS.dhp_source must not be empty."""
    results = []
    data = db_session.query(DpdHeadword).outerjoin(SBS).all()
    for headword in data:
        if not headword.meaning_1:
            continue
        has_dhp_source = re.search(r"DHP\d+", headword.source_1) or re.search(
            r"DHP\d+", headword.source_2
        )
        if has_dhp_source:
            if not headword.sbs or not headword.sbs.dhp_source:
                results.append(str(headword.id))
    return (
        "dhp_source_consistency",
        regex_results(results),
        len(results),
        "ensure dhp_source is present if headword has DHP source, run def dhp in scripts/change_in_db/sbs_examples_rearrangement.py",
    )


def check_dhp_triplet_consistency(
    db_session: Session,
) -> Tuple[str, Optional[str], int, str]:
    """If any of dhp_example, dhp_source, or dhp_sutta is present, all three must be present."""
    results = []
    sbs_data = db_session.query(SBS).all()
    for sbs in sbs_data:
        vals = [sbs.dhp_example, sbs.dhp_source, sbs.dhp_sutta]
        if any(vals) and not all(vals):
            results.append(str(sbs.id))
    return (
        "dhp_triplet_consistency",
        regex_results(results),
        len(results),
        "ensure dhp_example, dhp_source, and dhp_sutta are all present",
    )


def check_sbs_index_mapping(db_session: Session) -> Tuple[str, Optional[str], int, str]:
    """
    For sbs_example_1 and sbs_example_2, the combination of sbs_chant_pali,
    sbs_chant_eng, and sbs_chapter must match a valid row in sbs_index.csv.
    """
    import csv
    from tools.paths_dps import DPSPaths

    dpspth = DPSPaths()

    # Load sbs_index.csv
    valid_mappings = set()
    try:
        with open(dpspth.sbs_index_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                # Store tuple of (pali, eng, chapter)
                valid_mappings.add(
                    (row["pali_chant"], row["english_chant"], row["chapter"])
                )
    except Exception as e:
        print(f"[red]Error loading sbs_index.csv: {e}")
        return "sbs_index_mapping", None, 0, f"Error: {e}"

    results = []
    sbs_data = db_session.query(SBS).all()

    for sbs in sbs_data:
        # Check set 1
        if sbs.sbs_chant_pali_1:
            mapping1 = (sbs.sbs_chant_pali_1, sbs.sbs_chant_eng_1, sbs.sbs_chapter_1)
            if mapping1 not in valid_mappings:
                results.append(str(sbs.id))
                continue

        # Check set 2
        if sbs.sbs_chant_pali_2:
            mapping2 = (sbs.sbs_chant_pali_2, sbs.sbs_chant_eng_2, sbs.sbs_chapter_2)
            if mapping2 not in valid_mappings:
                results.append(str(sbs.id))

    return (
        "sbs_index_mapping",
        regex_results(results),
        len(results),
        "ensure chanting/chapter mapping matches sbs_index.csv",
    )


def check_sbs_example_consistency(
    db_session: Session,
) -> Tuple[str, Optional[str], int, str]:
    """
    Each set of 6 related fields (sbs_source_1/2, sbs_sutta_1/2, sbs_example_1/2,
    sbs_chant_pali_1/2, sbs_chant_eng_1/2, sbs_chapter_1/2) must be fully populated
    if any one of them has a value.
    Exception: If sbs_source_1/2 is one of ["Trad", "Sri Lanka", "Thai", "MJG"],
    then sbs_sutta_1/2 is allowed to be empty.
    """
    results = []
    sbs_data = db_session.query(SBS).all()

    exceptions = ["Trad", "Sri Lanka", "Thai", "MJG"]

    for sbs in sbs_data:
        # Check set 1
        set1 = [
            sbs.sbs_source_1,
            sbs.sbs_sutta_1,
            sbs.sbs_example_1,
            sbs.sbs_chant_pali_1,
            sbs.sbs_chant_eng_1,
            sbs.sbs_chapter_1,
        ]
        if any(set1):
            if sbs.sbs_source_1 in exceptions:
                # Sutta can be empty
                other_fields = [
                    sbs.sbs_source_1,
                    sbs.sbs_example_1,
                    sbs.sbs_chant_pali_1,
                    sbs.sbs_chant_eng_1,
                    sbs.sbs_chapter_1,
                ]
                if not all(other_fields):
                    results.append(str(sbs.id))
            else:
                if not all(set1):
                    results.append(str(sbs.id))
                    continue  # Already added

        # Check set 2
        set2 = [
            sbs.sbs_source_2,
            sbs.sbs_sutta_2,
            sbs.sbs_example_2,
            sbs.sbs_chant_pali_2,
            sbs.sbs_chant_eng_2,
            sbs.sbs_chapter_2,
        ]
        if any(set2):
            if sbs.sbs_source_2 in exceptions:
                # Sutta can be empty
                other_fields = [
                    sbs.sbs_source_2,
                    sbs.sbs_example_2,
                    sbs.sbs_chant_pali_2,
                    sbs.sbs_chant_eng_2,
                    sbs.sbs_chapter_2,
                ]
                if not all(other_fields):
                    results.append(str(sbs.id))
            else:
                if not all(set2):
                    results.append(str(sbs.id))

    return (
        "sbs_example_consistency",
        regex_results(results),
        len(results),
        "ensure all 6 sbs_example fields are populated if any are present",
    )


def check_vib_consistency(db_session: Session) -> Tuple[str, Optional[str], int, str]:
    """If any of vib_example, vib_source, or vib_sutta is present, all three must be present."""
    results = []
    sbs_data = db_session.query(SBS).all()
    for sbs in sbs_data:
        vals = [sbs.vib_example, sbs.vib_source, sbs.vib_sutta]
        if any(vals) and not all(vals):
            results.append(str(sbs.id))
    return (
        "vib_consistency",
        regex_results(results),
        len(results),
        "ensure vib_example, vib_source, and vib_sutta are all present",
    )


def check_class_consistency(db_session: Session) -> Tuple[str, Optional[str], int, str]:
    """If any of class_example, class_source, or class_sutta is present, all three must be present."""
    results = []
    sbs_data = db_session.query(SBS).all()
    for sbs in sbs_data:
        vals = [sbs.class_example, sbs.class_source, sbs.class_sutta]
        if any(vals) and not all(vals):
            # Exception: class_anki == 2 and words "upāsak" or "thero" or "sīho" in class_example
            if sbs.class_anki == 2 and any(
                word in sbs.class_example for word in ["upāsak", "thero", "sīho"]
            ):
                continue
            results.append(str(sbs.id))
    return (
        "class_consistency",
        regex_results(results),
        len(results),
        "ensure class_example, class_source, and class_sutta are all present",
    )


def check_discourses_consistency(
    db_session: Session,
) -> Tuple[str, Optional[str], int, str]:
    """If any of discourses_example, discourses_source, or discourses_sutta is present, all three must be present."""
    results = []
    sbs_data = db_session.query(SBS).all()
    for sbs in sbs_data:
        vals = [sbs.discourses_example, sbs.discourses_source, sbs.discourses_sutta]
        if any(vals) and not all(vals):
            results.append(str(sbs.id))
    return (
        "discourses_consistency",
        regex_results(results),
        len(results),
        "ensure discourses_example, discourses_source, and discourses_sutta are all present",
    )


def check_class_anki_consistency(
    db_session: Session,
) -> Tuple[str, Optional[str], int, str]:
    """
    1. 1:1 relationship between SBS.class_example and SBS.class_anki (if one exists, the other must).
    2. If SBS.class_anki is not "1" (or 1), then SBS.class_example AND SBS.class_example_translation must have values.
    """
    results = []
    sbs_data = db_session.query(SBS).all()

    for sbs in sbs_data:
        # Rule 1
        if (sbs.class_example and not sbs.class_anki) or (
            not sbs.class_example and sbs.class_anki
        ):
            # Special case for Rule 2: if anki is 1, example can be empty.
            # So if (no example and anki == 1), it's OK.
            if not (not sbs.class_example and str(sbs.class_anki) == "1"):
                results.append(str(sbs.id))
                continue

        # Rule 2
        if sbs.class_anki and str(sbs.class_anki) != "1":
            if not sbs.class_example or not sbs.class_example_translation:
                results.append(str(sbs.id))

    return (
        "class_anki_consistency",
        regex_results(results),
        len(results),
        "ensure class_example, class_anki and class_example_translation are consistent",
    )


def check_discourses_source_prefix(
    db_session: Session,
) -> Tuple[str, Optional[str], int, str]:
    """
    The prefix of SBS.discourses_source (before the first '.')
    must exist in the sbs_category_list (case-insensitive).
    If there is no '.', the entire string must exist in the list.
    """
    from tools.sbs_table_functions import sbs_category_list

    results = []
    sbs_data = db_session.query(SBS).all()
    categories = [cat.lower() for cat in sbs_category_list]

    for sbs in sbs_data:
        if sbs.discourses_source:
            prefix = sbs.discourses_source.split(".")[0].lower()
            if prefix not in categories:
                results.append(str(sbs.id))

    return (
        "discourses_source_prefix",
        regex_results(results),
        len(results),
        "ensure discourses_source prefix is in sbs_category_list",
    )


def check_pat_consistency(db_session: Session) -> Tuple[str, Optional[str], int, str]:
    """
    1. If SBS.pat_example is present, SBS.pat_source must contain "VIN PAT".
    2. If SBS.pat_source contains "VIN PAT", SBS.pat_example must not be empty.
    3. If any of pat_example, pat_source, or pat_sutta is present, all three must be present.
    """
    results = []
    exceptions_count = 0

    sbs_data = db_session.query(SBS).all()
    for sbs in sbs_data:
        if sbs.pat_source == "PAT":
            exceptions_count += 1
            continue
        # Rule 1 & 2
        if sbs.pat_example and "VIN PAT" not in sbs.pat_source:
            results.append(str(sbs.id))
        elif "VIN PAT" in sbs.pat_source and not sbs.pat_example:
            results.append(str(sbs.id))
        # Rule 3
        elif any([sbs.pat_example, sbs.pat_source, sbs.pat_sutta]):
            if not all([sbs.pat_example, sbs.pat_source, sbs.pat_sutta]):
                results.append(str(sbs.id))

    # print reminder of issue #29
    print(
        f"[red]Reminder: {exceptions_count} rows still do not have Pātimokkha examples, see issue #29"
    )

    return (
        "pat_consistency",
        regex_results(results),
        len(results),
        "ensure pat_example matches pat_source and all fields are present",
    )


def check_bold_tags(db_session: Session) -> List[Tuple[str, Optional[str], int, str]]:
    """All SBS-related example fields must contain both start <b> and end </b> tags if not empty."""
    example_fields = [
        "sbs_example_1",
        "sbs_example_2",
        "dhp_example",
        "pat_example",
        "vib_example",
        "class_example",
        "discourses_example",
    ]

    all_results = []
    sbs_data = db_session.query(SBS).all()

    for field in example_fields:
        results = []
        for sbs in sbs_data:
            val = getattr(sbs, field)
            if val:
                if "<b>" not in val or "</b>" not in val:
                    results.append(str(sbs.id))

        all_results.append(
            (
                f"bold_tags_{field}",
                regex_results(results),
                len(results),
                f"ensure {field} has both <b> and </b> tags",
            )
        )

    return all_results


def check_class_translation_uniqueness(
    db_session: Session,
) -> Tuple[str, Optional[str], int, str]:
    """If any class_example_translation has more than 1 corresponding class_source, it should be investigated."""
    sbs_data = db_session.query(SBS).all()

    # Map translation to set of sources
    translation_map = {}  # {translation: set(sources)}

    for sbs in sbs_data:
        if sbs.class_example_translation:
            tr = sbs.class_example_translation.strip()
            if tr not in translation_map:
                translation_map[tr] = set()
            source = sbs.class_source.strip() if sbs.class_source else ""
            translation_map[tr].add(source)

    output_lines = []
    for tr, sources in translation_map.items():
        if len(sources) > 1:
            sorted_sources = sorted([str(s) for s in sources])
            output_lines.append(f"'{tr}': {sorted_sources}")

    results_str = "\n".join(output_lines) if output_lines else None

    return (
        "class_translation_uniqueness",
        results_str,
        len(output_lines),
        "ensure class_example_translation corresponds to only one class_source",
    )


def regex_results(results: List[str]) -> Optional[str]:
    """Take a list of results and return a regex search string or None"""
    if results:
        results = results[:100]
        regex_string = r"/\b("
        regex_string += "|".join(results)
        regex_string += r")\b/"
        return regex_string
    return None


if __name__ == "__main__":
    pr.tic()
    run_sbs_consistency_tests()
    pr.toc()
