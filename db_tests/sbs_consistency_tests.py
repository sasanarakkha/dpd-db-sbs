#!/usr/bin/env python3

"""SBS Example Consistency Tests."""

import re
import sys
from collections.abc import Callable

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import SBS, DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def run_sbs_consistency_tests() -> int:
    pr.tic()
    pr.yellow_title("run sbs consistency tests")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    results_list: list[tuple[str, str | None, int, str]] = []

    def run_one(name, func):
        pr.green_tmr(name.replace("_", " "))

        res = func(db_session)
        results_list.append(res)

        count = res[2]
        if count == 0:
            pr.yes(count)
        else:
            pr.no(count)

        if count > 0:
            pr.red(f"solution: {res[3]}")
            if res[1]:
                pr.white(res[1])
        pr.white("")

    # Triplet
    run_one("pat_consistency", check_pat_consistency)
    run_one("dhp_source_consistency", check_dhp_source_consistency)
    run_one("dhp_triplet_consistency", check_dhp_triplet_consistency)
    run_one("vib_consistency", check_vib_consistency)
    run_one("class_consistency", check_class_consistency)
    run_one("discourses_consistency", check_discourses_consistency)
    run_one("extra_consistency", check_extra_consistency)
    run_one("sbs_example_consistency", check_sbs_example_consistency)
    run_one("class_anki_consistency", check_class_anki_consistency)

    # Source validation
    run_one("discourses_source_prefix", check_discourses_source_prefix)
    run_one("discourses_source_full", check_discourses_source_full)

    for field in SOURCE_FIELDS:
        run_one(
            f"source_has_space_{field}",
            lambda db, field=field: check_source_has_space_field(db, field),
        )

    # Formatting
    for field in EXAMPLE_FIELDS:
        run_one(
            f"bold_tags_{field}",
            lambda db, field=field: check_bold_tags_field(db, field),
        )

    for field in EXAMPLE_FIELDS:
        run_one(
            f"capital_letter_{field}",
            lambda db, field=field: check_example_capital_letters_field(db, field),
        )

    for field in EXAMPLE_FIELDS:
        run_one(
            f"space_comma_{field}",
            lambda db, field=field: check_example_spacing_comma_field(db, field),
        )
        run_one(
            f"space_comma_edge_{field}",
            lambda db, field=field: check_example_spacing_comma_edge_field(db, field),
        )
        run_one(
            f"space_fullstop_edge_{field}",
            lambda db, field=field: check_example_spacing_fullstop_edge_field(
                db, field
            ),
        )

    # Example content
    run_one("example_space_before_comma", check_example_space_before_comma)
    run_one("example_space_before_fullstop", check_example_space_before_fullstop)
    run_one(
        "example_leading_trailing_whitespace",
        check_example_leading_trailing_whitespace,
    )
    run_one("example_capital_letter", check_example_capital_letter)
    run_one("example_missing_bold_open", check_example_missing_bold_open)
    run_one("example_missing_bold_close", check_example_missing_bold_close)
    run_one("example_missing_source", check_example_missing_source)
    run_one("example_missing_sutta", check_example_missing_sutta)

    # Cross-reference
    run_one("sbs_index_mapping", check_sbs_index_mapping)
    run_one("class_translation_uniqueness", check_class_translation_uniqueness)

    total_errors = sum(
        count
        for name, _, count, _ in results_list
        if name not in SOFT_ERROR_CHECK_NAMES
    )

    if total_errors > 0:
        pr.red(f"SBS consistency tests FAILED with {total_errors} total errors.")
        pr.toc()
        return 1

    pr.green("All SBS consistency tests passed.")
    pr.toc()
    return 0


# ============================================================
# SHARED HELPERS & CONSTANTS
# ============================================================

EXAMPLE_FIELDS: list[str] = [
    "sbs_example_1",
    "sbs_example_2",
    "dhp_example",
    "pat_example",
    "vib_example",
    "class_example",
    "discourses_example",
]

SOURCE_FIELDS: list[str] = [
    "sbs_source_1",
    "sbs_source_2",
    "dhp_source",
    "pat_source",
    "vib_source",
    "class_source",
    "discourses_source",
]

# Source values where sutta is allowed to be empty (from TSV rows 71-77).
SUTTA_EXCEPTION_SOURCES: list[str] = ["MJG", "Sri Lanka", "Thai", "Trad"]

# Source substrings where a space is allowed in the source value (TSV rows 108-114).
SOURCE_SPACE_EXEMPT_SUBSTRINGS: list[str] = ["PAT", "Sri Lanka", "(modif)", "(simpl)"]

SOFT_ERROR_CHECK_NAMES: set[str] = {"discourses_source_full"}


def regex_results(results: list[str]) -> str | None:
    """Take a list of results and return a regex search string or None"""
    if results:
        results = results[:100]
        regex_string = r"/\b("
        regex_string += "|".join(results)
        regex_string += r")\b/"
        return regex_string
    return None


def _check_triplet(
    db_session: Session,
    *,
    name: str,
    example_field: str,
    source_field: str,
    sutta_field: str,
    solution: str,
    allow_sutta_exception: bool = True,
) -> tuple[str, str | None, int, str]:
    """Generic example/source/sutta triplet check."""
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        example = getattr(sbs, example_field) or ""
        source = getattr(sbs, source_field) or ""
        sutta = getattr(sbs, sutta_field) or ""
        if not (example or source or sutta):
            continue
        if not example or not source:
            results.append(str(sbs.id))
            continue
        if sutta:
            continue
        if allow_sutta_exception and source in SUTTA_EXCEPTION_SOURCES:
            continue
        results.append(str(sbs.id))
    return (name, regex_results(results), len(results), solution)


def _check_field_regex(
    db_session: Session,
    *,
    name: str,
    field: str,
    pattern: str,
    solution: str,
) -> tuple[str, str | None, int, str]:
    """Run one regex across one field."""
    compiled = re.compile(pattern)
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        val = getattr(sbs, field) or ""
        if val and compiled.search(val):
            results.append(str(sbs.id))
    return (name, regex_results(results), len(results), solution)


# ==== TRIPLET CHECKS ====


def check_dhp_triplet_consistency(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """If any of dhp_example, dhp_source, or dhp_sutta is present, example+source must be present."""
    return _check_triplet(
        db_session,
        name="dhp_triplet_consistency",
        example_field="dhp_example",
        source_field="dhp_source",
        sutta_field="dhp_sutta",
        solution="ensure dhp_example, dhp_source, and dhp_sutta are all present",
    )


def check_vib_consistency(db_session: Session) -> tuple[str, str | None, int, str]:
    """If any of vib_example, vib_source, or vib_sutta is present, example+source must be present."""
    return _check_triplet(
        db_session,
        name="vib_consistency",
        example_field="vib_example",
        source_field="vib_source",
        sutta_field="vib_sutta",
        solution="ensure vib_example, vib_source, and vib_sutta are all present",
    )


def check_class_consistency(db_session: Session) -> tuple[str, str | None, int, str]:
    """If any of class_example, class_source, or class_sutta is present, all three must be present."""
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        example = sbs.class_example or ""
        source = sbs.class_source or ""
        sutta = sbs.class_sutta or ""
        if not (example or source or sutta):
            continue

        # Existing class_anki exception
        if sbs.class_anki == 2 and any(
            w in example for w in ["upāsak", "thero", "sīho"]
        ):
            continue

        if not example or not source:
            results.append(str(sbs.id))
            continue
        if sutta:
            continue
        # New: MJG/Sri Lanka/Thai/Trad sutta exception
        if source in SUTTA_EXCEPTION_SOURCES:
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
) -> tuple[str, str | None, int, str]:
    """If any of discourses_example, discourses_source, or discourses_sutta is present, example+source must be present."""
    return _check_triplet(
        db_session,
        name="discourses_consistency",
        example_field="discourses_example",
        source_field="discourses_source",
        sutta_field="discourses_sutta",
        solution="ensure discourses_example, discourses_source, and discourses_sutta are all present",
    )


def check_extra_consistency(db_session: Session) -> tuple[str, str | None, int, str]:
    """Triplet check for extra_example/extra_source/extra_sutta."""
    return _check_triplet(
        db_session,
        name="extra_consistency",
        example_field="extra_example",
        source_field="extra_source",
        sutta_field="extra_sutta",
        solution="ensure extra_example, extra_source, and extra_sutta are all present",
    )


def check_sbs_example_consistency(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """
    Each set of 6 related fields must be fully populated if any one of them has a value.
    """
    results: list[str] = []
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


def check_pat_consistency(db_session: Session) -> tuple[str, str | None, int, str]:
    """Patimokkha consistency rules."""
    results: list[str] = []
    exceptions_count = 0
    sbs_data = db_session.query(SBS).all()
    for sbs in sbs_data:
        if sbs.pat_source == "PAT":
            exceptions_count += 1
            continue
        if (
            (
                sbs.pat_example
                and "VIN PAT" not in sbs.pat_source
                or "VIN PAT" in sbs.pat_source
                and not sbs.pat_example
            )
            or any([sbs.pat_example, sbs.pat_source, sbs.pat_sutta])
            and not all([sbs.pat_example, sbs.pat_source, sbs.pat_sutta])
        ):
            results.append(str(sbs.id))

    if exceptions_count > 0:
        pr.amber(
            f"Reminder: {exceptions_count} rows still do not have Pātimokkha examples, see issue #29"
        )

    return (
        "pat_consistency",
        regex_results(results),
        len(results),
        "ensure pat_example matches pat_source and all fields are present",
    )


# ==== FORMATTING ====


def check_bold_tags_field(
    db_session: Session, field: str
) -> tuple[str, str | None, int, str]:
    """Check bold tags in one field."""
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        val = getattr(sbs, field)
        if val and ("<b>" not in val or "</b>" not in val):
            results.append(str(sbs.id))
    return (
        f"bold_tags_{field}",
        regex_results(results),
        len(results),
        f"ensure {field} has both <b> and </b> tags",
    )


def check_example_capital_letters_field(
    db_session: Session, field: str
) -> tuple[str, str | None, int, str]:
    """Check capital letters in one field."""
    return _check_field_regex(
        db_session,
        name=f"capital_letter_{field}",
        field=field,
        pattern=r"[A-Z]",
        solution="remove stray ASCII capital letters from example",
    )


def check_example_spacing_comma_field(
    db_session: Session, field: str
) -> tuple[str, str | None, int, str]:
    """Check space before comma."""
    return _check_field_regex(
        db_session,
        name=f"space_comma_{field}",
        field=field,
        pattern=r" ,",
        solution="remove space before comma",
    )


def check_example_spacing_comma_edge_field(
    db_session: Session, field: str
) -> tuple[str, str | None, int, str]:
    """Check trailing or floating comma."""
    return _check_field_regex(
        db_session,
        name=f"space_comma_edge_{field}",
        field=field,
        pattern=r" ,$| , ",
        solution="remove trailing or floating ' ,'",
    )


def check_example_spacing_fullstop_edge_field(
    db_session: Session, field: str
) -> tuple[str, str | None, int, str]:
    """Check trailing or floating full stop."""
    return _check_field_regex(
        db_session,
        name=f"space_fullstop_edge_{field}",
        field=field,
        pattern=r" \.$| \. ",
        solution="remove trailing or floating ' .'",
    )


# ==== EXAMPLE CONTENT CHECKS ====


def _check_example_all_fields(
    db_session: Session,
    *,
    name: str,
    solution: str,
    condition: Callable[[str, SBS], bool],
) -> tuple[str, str | None, int, str]:
    """Run a condition across all 7 example fields. Condition is a callable(val, sbs) -> bool."""
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        for field in EXAMPLE_FIELDS:
            val = getattr(sbs, field) or ""
            if condition(val, sbs):
                results.append(f"{sbs.id}/{field}")
                break
    return (name, regex_results(results), len(results), solution)


def check_example_space_before_comma(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Detect space before comma across all example fields."""
    return _check_example_all_fields(
        db_session,
        name="example_space_before_comma",
        condition=lambda v, s: " ," in v,
        solution="remove space before comma across all example fields",
    )


def check_example_space_before_fullstop(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Detect space before fullstop across all example fields."""
    return _check_example_all_fields(
        db_session,
        name="example_space_before_fullstop",
        condition=lambda v, s: " ." in v,
        solution="remove space before fullstop across all example fields",
    )


def check_example_leading_trailing_whitespace(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Detect leading or trailing whitespace across all example fields."""
    return _check_example_all_fields(
        db_session,
        name="example_leading_trailing_whitespace",
        condition=lambda v, s: v != v.strip(),
        solution="strip leading/trailing whitespace across all example fields",
    )


def check_example_capital_letter(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Detect ASCII capital letters across all example fields."""
    return _check_example_all_fields(
        db_session,
        name="example_capital_letter",
        condition=lambda v, s: bool(re.search(r"[A-Z]", v)),
        solution="lowercase ASCII capital letters across all example fields",
    )


def check_example_missing_bold_open(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Detect non-empty fields missing <b>."""
    return _check_example_all_fields(
        db_session,
        name="example_missing_bold_open",
        condition=lambda v, s: bool(v) and "<b>" not in v,
        solution="add <b> tag to example fields missing bold open",
    )


def check_example_missing_bold_close(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Detect non-empty fields missing </b>."""
    return _check_example_all_fields(
        db_session,
        name="example_missing_bold_close",
        condition=lambda v, s: bool(v) and "</b>" not in v,
        solution="add </b> tag to example fields missing bold close",
    )


SOURCE_TO_EXAMPLE: dict[str, str] = {
    "sbs_example_1": "sbs_source_1",
    "sbs_example_2": "sbs_source_2",
    "dhp_example": "dhp_source",
    "pat_example": "pat_source",
    "vib_example": "vib_source",
    "class_example": "class_source",
    "discourses_example": "discourses_source",
}

SUTTA_FIELD_MAP: dict[str, str] = {
    "sbs_example_1": "sbs_sutta_1",
    "sbs_example_2": "sbs_sutta_2",
    "dhp_example": "dhp_sutta",
    "pat_example": "pat_sutta",
    "vib_example": "vib_sutta",
    "class_example": "class_sutta",
    "discourses_example": "discourses_sutta",
}


def check_example_missing_source(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Detect example non-empty but source empty."""
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        for example_field, source_field in SOURCE_TO_EXAMPLE.items():
            example = getattr(sbs, example_field) or ""
            source = getattr(sbs, source_field) or ""
            if example and not source:
                results.append(f"{sbs.id}/{example_field}")
    return (
        "example_missing_source",
        regex_results(results),
        len(results),
        "ensure source is present when example is non-empty",
    )


def check_example_missing_sutta(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Detect example non-empty, source not exempt, but sutta empty."""
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        for example_field in EXAMPLE_FIELDS:
            example = getattr(sbs, example_field) or ""
            if not example:
                continue
            source_field = SOURCE_TO_EXAMPLE[example_field]
            source = getattr(sbs, source_field) or ""
            if source in SUTTA_EXCEPTION_SOURCES:
                continue
            sutta_field = SUTTA_FIELD_MAP[example_field]
            sutta = getattr(sbs, sutta_field) or ""
            if not sutta:
                results.append(f"{sbs.id}/{example_field}")
    return (
        "example_missing_sutta",
        regex_results(results),
        len(results),
        "ensure sutta is present when example is non-empty and source is not exempt",
    )


# ==== SOURCE VALIDATION ====
# MARKER: add full-source validations below (issue #20)


def check_discourses_source_prefix(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Check discourses source prefix."""
    from tools.sbs_table_functions import sbs_category_list

    results: list[str] = []
    categories = [cat.lower() for cat in sbs_category_list]
    for sbs in db_session.query(SBS).all():
        if sbs.discourses_source:
            prefix = sbs.discourses_source.split(".")[0].lower()
            if prefix not in categories:
                results.append(str(sbs.id))

    if results:
        pr.amber(f"Reminder: {len(results)} rows have invalid discourses prefix")
    return (
        "discourses_source_prefix",
        regex_results(results),
        len(results),
        "ensure discourses_source prefix is in sbs_category_list",
    )


def check_discourses_source_full(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Check discourses source against full list."""
    from tools.sbs_table_functions import list_of_discourses

    valid = set(list_of_discourses)
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        if sbs.discourses_source and sbs.discourses_source not in valid:
            results.append(str(sbs.id))

    if results:
        pr.amber(
            f"Reminder: {len(results)} rows have invalid discourses source, see issue #47"
        )
    return (
        "discourses_source_full",
        regex_results(results),
        len(results),
        "ensure discourses_source matches entry in tools/sbs_table_functions.py:list_of_discourses",
    )


def check_source_has_space_field(
    db_session: Session, field: str
) -> tuple[str, str | None, int, str]:
    """Check for spaces in source field."""
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        val = getattr(sbs, field) or ""
        if not val or " " not in val:
            continue
        if any(exempt in val for exempt in SOURCE_SPACE_EXEMPT_SUBSTRINGS):
            continue
        results.append(str(sbs.id))
    return (
        f"source_has_space_{field}",
        regex_results(results),
        len(results),
        f"remove space from {field}",
    )


# ==== CROSS-REFERENCE ====


def check_dhp_source_consistency(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """DHP source consistency."""
    results: list[str] = []
    data = db_session.query(DpdHeadword).outerjoin(SBS).all()
    for headword in data:
        if not headword.meaning_1:
            continue
        has_dhp_source = re.search(r"DHP\d+", headword.source_1) or re.search(
            r"DHP\d+", headword.source_2
        )
        if has_dhp_source and (not headword.sbs or not headword.sbs.dhp_source):
            results.append(str(headword.id))

    if results:
        pr.amber(
            f"Reminder: {len(results)} rows still do not have DHP examples consider running scripts/change_in_db/dhp_examples_copy.py"
        )
    return (
        "dhp_source_consistency",
        regex_results(results),
        len(results),
        "ensure dhp_source is present if headword has DHP source",
    )


def check_sbs_index_mapping(db_session: Session) -> tuple[str, str | None, int, str]:
    """Check sbs_index.csv mapping."""
    from tools.sbs_table_functions import SBS_table_tools

    sbs_tools = SBS_table_tools()
    try:
        valid_mappings = sbs_tools.load_valid_mappings()
    except Exception as e:  # noqa: BLE001
        return "sbs_index_mapping", None, 0, f"Error: {e}"

    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        if (
            sbs.sbs_chant_pali_1
            and (
                sbs.sbs_chant_pali_1,
                sbs.sbs_chant_eng_1,
                sbs.sbs_chapter_1,
            )
            not in valid_mappings
        ):
            results.append(str(sbs.id))
        if (
            sbs.sbs_chant_pali_2
            and (
                sbs.sbs_chant_pali_2,
                sbs.sbs_chant_eng_2,
                sbs.sbs_chapter_2,
            )
            not in valid_mappings
        ):
            results.append(str(sbs.id))
    return (
        "sbs_index_mapping",
        regex_results(results),
        len(results),
        "ensure chanting/chapter mapping matches sbs_index.csv",
    )


def check_class_anki_consistency(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Check class_anki consistency."""
    results: list[str] = []
    for sbs in db_session.query(SBS).all():
        if (sbs.class_example and not sbs.class_anki) or (
            not sbs.class_example and sbs.class_anki
        ):
            if not (not sbs.class_example and str(sbs.class_anki) == "1"):
                results.append(str(sbs.id))
        elif (
            sbs.class_anki
            and str(sbs.class_anki) != "1"
            and (not sbs.class_example or not sbs.class_example_translation)
        ):
            results.append(str(sbs.id))
    return (
        "class_anki_consistency",
        regex_results(results),
        len(results),
        "ensure class_example, class_anki and class_example_translation are consistent",
    )


def check_class_translation_uniqueness(
    db_session: Session,
) -> tuple[str, str | None, int, str]:
    """Check class translation uniqueness."""
    translation_map = {}
    for sbs in db_session.query(SBS).all():
        if sbs.class_example_translation:
            tr = sbs.class_example_translation.strip()
            if tr not in translation_map:
                translation_map[tr] = set()
            translation_map[tr].add(
                sbs.class_source.strip() if sbs.class_source else ""
            )
    output_lines = [
        f"'{tr}': {sorted([str(s) for s in sources])}"
        for tr, sources in translation_map.items()
        if len(sources) > 1
    ]
    return (
        "class_translation_uniqueness",
        "\n".join(output_lines) if output_lines else None,
        len(output_lines),
        "ensure class_example_translation corresponds to only one class_source",
    )


# ============================================================
# COMPATIBILITY WRAPPERS FOR TESTS
# ============================================================


def check_source_has_space(
    db_session: Session,
) -> list[tuple[str, str | None, int, str]]:
    """Compatibility wrapper for all source fields."""
    return [check_source_has_space_field(db_session, f) for f in SOURCE_FIELDS]


def check_bold_tags(db_session: Session) -> list[tuple[str, str | None, int, str]]:
    """Compatibility wrapper for all example fields."""
    return [check_bold_tags_field(db_session, f) for f in EXAMPLE_FIELDS]


def check_example_capital_letters(
    db_session: Session,
) -> list[tuple[str, str | None, int, str]]:
    """Compatibility wrapper for all example fields."""
    return [check_example_capital_letters_field(db_session, f) for f in EXAMPLE_FIELDS]


def check_example_spacing(
    db_session: Session,
) -> list[tuple[str, str | None, int, str]]:
    """Compatibility wrapper for all example fields."""
    results = []
    for f in EXAMPLE_FIELDS:
        results.append(check_example_spacing_comma_field(db_session, f))
        results.append(check_example_spacing_comma_edge_field(db_session, f))
        results.append(check_example_spacing_fullstop_edge_field(db_session, f))
    return results


if __name__ == "__main__":
    exit_code = run_sbs_consistency_tests()
    sys.exit(exit_code)
