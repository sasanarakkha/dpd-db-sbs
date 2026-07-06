#!/usr/bin/env python3

"""Add combined view into db which have DpdHeadword, Russian, SBS tables and ebt_count together."""

from sqlalchemy import create_engine, text

from tools.paths import ProjectPaths
from tools.printer import printer as pr

_VIEW_COLUMNS: list[tuple[str, str, str]] = [
    ("dpd_headwords", "id", "id"),
    ("dpd_headwords", "ebt_count", "count"),
    ("sbs", "class_anki", "anki"),
    ("sbs", "sbs_index", "PER"),
    ("dpd_headwords", "lemma_1", "lemma_1"),
    ("dpd_headwords", "lemma_2", "lemma_2"),
    ("dpd_headwords", "pos", "pos"),
    ("dpd_headwords", "grammar", "grammar"),
    ("dpd_headwords", "derived_from", "derived"),
    ("dpd_headwords", "neg", "neg"),
    ("dpd_headwords", "verb", "verb"),
    ("dpd_headwords", "trans", "trans"),
    ("dpd_headwords", "plus_case", "plus_case"),
    ("dpd_headwords", "meaning_1", "meaning_1"),
    ("dpd_headwords", "meaning_lit", "meaning_lit"),
    ("dpd_headwords", "meaning_2", "meaning_2"),
    ("sbs", "sbs_meaning", "sbs_meaning"),
    ("russian", "ru_meaning", "ru_meaning"),
    ("russian", "ru_meaning_lit", "ru_meaning_lit"),
    ("russian", "ru_meaning_raw", "ru_meaning_raw"),
    ("dpd_headwords", "sanskrit", "sanskrit"),
    ("dpd_headwords", "root_key", "root"),
    ("dpd_headwords", "root_sign", "sign"),
    ("dpd_headwords", "root_base", "root_base"),
    ("dpd_headwords", "family_root", "family_root"),
    ("dpd_headwords", "family_word", "family_word"),
    ("dpd_headwords", "family_compound", "family_compound"),
    ("dpd_headwords", "family_set", "family_set"),
    ("dpd_headwords", "construction", "construction"),
    ("dpd_headwords", "derivative", "derivative"),
    ("dpd_headwords", "suffix", "suffix"),
    ("dpd_headwords", "phonetic", "phonetic"),
    ("dpd_headwords", "compound_type", "compound_type"),
    ("dpd_headwords", "compound_construction", "compound_construction"),
    ("dpd_headwords", "source_1", "source_1"),
    ("dpd_headwords", "sutta_1", "sutta_1"),
    ("dpd_headwords", "example_1", "example_1"),
    ("dpd_headwords", "source_2", "source_2"),
    ("dpd_headwords", "sutta_2", "sutta_2"),
    ("dpd_headwords", "example_2", "example_2"),
    ("sbs", "sbs_source_1", "sbs_source_1"),
    ("sbs", "sbs_sutta_1", "sbs_sutta_1"),
    ("sbs", "sbs_example_1", "sbs_example_1"),
    ("sbs", "sbs_chant_pali_1", "sbs_chant_pali_1"),
    ("sbs", "sbs_chant_eng_1", "sbs_chant_eng_1"),
    ("sbs", "sbs_chapter_1", "sbs_chapter_1"),
    ("sbs", "sbs_source_2", "sbs_source_2"),
    ("sbs", "sbs_sutta_2", "sbs_sutta_2"),
    ("sbs", "sbs_example_2", "sbs_example_2"),
    ("sbs", "sbs_chant_pali_2", "sbs_chant_pali_2"),
    ("sbs", "sbs_chant_eng_2", "sbs_chant_eng_2"),
    ("sbs", "sbs_chapter_2", "sbs_chapter_2"),
    ("sbs", "dhp_source", "dhp_source"),
    ("sbs", "dhp_sutta", "dhp_sutta"),
    ("sbs", "dhp_example", "dhp_example"),
    ("sbs", "pat_source", "pat_source"),
    ("sbs", "pat_sutta", "pat_sutta"),
    ("sbs", "pat_example", "pat_example"),
    ("sbs", "vib_source", "vib_source"),
    ("sbs", "vib_sutta", "vib_sutta"),
    ("sbs", "vib_example", "vib_example"),
    ("sbs", "class_source", "class_source"),
    ("sbs", "class_sutta", "class_sutta"),
    ("sbs", "class_example", "class_example"),
    ("sbs", "class_example_translation", "translation"),
    ("sbs", "class_extra", "extra"),
    ("sbs", "discourses_source", "discourses_source"),
    ("sbs", "discourses_sutta", "discourses_sutta"),
    ("sbs", "discourses_example", "discourses_example"),
    ("dpd_headwords", "antonym", "antonym"),
    ("dpd_headwords", "synonym", "synonym"),
    ("dpd_headwords", "variant", "variant"),
    ("dpd_headwords", "commentary", "commentary"),
    ("dpd_headwords", "notes", "notes"),
    ("sbs", "sbs_notes", "sbs_notes"),
    ("russian", "ru_notes", "ru_notes"),
    ("dpd_headwords", "cognate", "cognate"),
    ("dpd_headwords", "stem", "stem"),
    ("dpd_headwords", "pattern", "pattern"),
    ("sbs", "sbs_class", "class"),
]


def _build_select_clause(columns: list[tuple[str, str, str]]) -> str:
    """Build the COALESCE(...) AS alias select clause from (table, column, alias) triples."""
    lines = [
        f"COALESCE({table}.{column}, '') AS {alias}" for table, column, alias in columns
    ]
    return ",\n                ".join(lines)


def main() -> None:
    pr.tic()
    pr.yellow_title("making combined view")

    pth = ProjectPaths()
    engine = create_engine("sqlite:///" + str(pth.dpd_db_path))

    with engine.connect() as connection:
        connection.execute(text("DROP VIEW IF EXISTS _dps;"))

        select_clause = _build_select_clause(_VIEW_COLUMNS)
        connection.execute(
            text(f"""
            CREATE VIEW _dps AS
            SELECT
                {select_clause}
            FROM dpd_headwords
            LEFT JOIN sbs ON dpd_headwords.id = sbs.id
            LEFT JOIN russian ON dpd_headwords.id = russian.id
            """)
        )

    pr.toc()


if __name__ == "__main__":
    main()
