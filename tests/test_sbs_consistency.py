"""
Unit tests for SBS consistency logic.
These tests verify the correctness of data integrity rules (regexes, triplets, exceptions)
defined in db_tests/sbs_consistency_tests.py using an in-memory database and mock data.
"""

import pytest
import re
from unittest.mock import patch, mock_open
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, DpdHeadword, SBS
from db_tests.sbs_consistency_tests import (
    check_pat_consistency,
    check_dhp_source_consistency,
    check_dhp_triplet_consistency,
    check_vib_consistency,
    check_class_consistency,
    check_discourses_consistency,
    check_extra_consistency,
    check_class_anki_consistency,
    check_discourses_source_prefix,
    check_discourses_source_full,
    check_source_has_space,
    check_sbs_example_consistency,
    check_sbs_index_mapping,
    check_bold_tags,
    check_example_capital_letters,
    check_example_spacing,
    check_class_translation_uniqueness,
    run_sbs_consistency_tests,
)


@pytest.fixture
def in_memory_db():
    """Sets up an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_pat_consistency_logic(in_memory_db):
    # Case 1: All correct
    sbs1 = SBS(id=1, pat_example="ex", pat_source="VIN PAT", pat_sutta="su")
    in_memory_db.add(sbs1)

    # Case 2: pat_example present but "VIN PAT" missing from source (Violation)
    sbs2 = SBS(id=2, pat_example="ex", pat_source="OTHER", pat_sutta="su")
    in_memory_db.add(sbs2)

    # Case 3: "VIN PAT" present but pat_example empty (Violation)
    sbs3 = SBS(id=3, pat_example="", pat_source="VIN PAT", pat_sutta="su")
    in_memory_db.add(sbs3)

    # Case 4: Missing one of the triplet (Violation)
    sbs4 = SBS(id=4, pat_example="ex", pat_source="VIN PAT", pat_sutta="")
    in_memory_db.add(sbs4)

    in_memory_db.commit()

    name, results, count, solution = check_pat_consistency(in_memory_db)
    assert count == 3
    assert re.search(r"2", results)
    assert re.search(r"3", results)
    assert re.search(r"4", results)


def test_dhp_source_consistency_logic(in_memory_db):
    # Case 1: Correct - DHP source in headword and SBS dhp_source
    h1 = DpdHeadword(id=1, lemma_1="l1", source_1="DHP100", meaning_1="m1")
    s1 = SBS(id=1, dhp_source="DHP100")
    in_memory_db.add_all([h1, s1])

    # Case 2: DHP source in headword but SBS dhp_source empty (Violation)
    h2 = DpdHeadword(id=2, lemma_1="l2", source_1="DHP200", meaning_1="m2")
    s2 = SBS(id=2, dhp_source="")
    in_memory_db.add_all([h2, s2])

    # Case 3: No SBS entry but headword has DHP source (Violation)
    h3 = DpdHeadword(id=3, lemma_1="l3", source_2="DHP400", meaning_1="m3")
    in_memory_db.add(h3)

    in_memory_db.commit()

    name, results, count, solution = check_dhp_source_consistency(in_memory_db)
    assert count == 2
    assert re.search(r"2", results)
    assert re.search(r"3", results)


def test_dhp_triplet_consistency_logic(in_memory_db):
    # Case 1: Correct triplet
    s1 = SBS(id=1, dhp_example="ex", dhp_source="DHP100", dhp_sutta="su")
    # Case 2: Missing one of the triplet in SBS (Violation)
    s2 = SBS(id=2, dhp_example="ex", dhp_source="DHP300", dhp_sutta="")
    # Case 3: New exception: sutta may be empty when source is in SUTTA_EXCEPTION_SOURCES
    s3 = SBS(id=3, dhp_example="ex", dhp_source="MJG", dhp_sutta="")

    in_memory_db.add_all([s1, s2, s3])
    in_memory_db.commit()

    name, results, count, solution = check_dhp_triplet_consistency(in_memory_db)
    assert count == 1
    assert re.search(r"2", results)
    assert not re.search(r"3", results)


def test_triplet_consistency_logic(in_memory_db):
    # vib triplet violation
    s1 = SBS(id=1, vib_example="ex", vib_source="so", vib_sutta="")
    # class triplet violation
    s2 = SBS(id=2, class_example="ex", class_source="", class_sutta="su")
    # discourses triplet violation
    s3 = SBS(id=3, discourses_example="", discourses_source="so", discourses_sutta="su")
    # correct ones
    s4 = SBS(id=4, vib_example="ex", vib_source="so", vib_sutta="su")
    s5 = SBS(id=5, class_example="ex", class_source="so", class_sutta="su")
    s6 = SBS(
        id=6, discourses_example="ex", discourses_source="so", discourses_sutta="su"
    )
    # class triplet violation but with existing exception (class_anki=2 and "upāsak")
    s7 = SBS(
        id=7, class_example="upāsako", class_source="", class_sutta="", class_anki=2
    )
    # new exceptions: MJG/Sri Lanka/Thai/Trad sutta exception
    s8 = SBS(id=8, vib_example="ex", vib_source="Thai", vib_sutta="")
    s9 = SBS(
        id=9,
        discourses_example="ex",
        discourses_source="Sri Lanka",
        discourses_sutta="",
    )
    s10 = SBS(id=10, class_example="ex", class_source="Trad", class_sutta="")

    in_memory_db.add_all([s1, s2, s3, s4, s5, s6, s7, s8, s9, s10])
    in_memory_db.commit()

    name, results, count, solution = check_vib_consistency(in_memory_db)
    assert count == 1
    assert re.search(r"1", results)
    assert not re.search(r"8", results)

    name, results, count, solution = check_class_consistency(in_memory_db)
    assert count == 1  # Only s2 should be flagged, s7 and s10 are excepted
    assert re.search(r"2", results)
    assert not re.search(r"7", results)
    assert not re.search(r"10", results)

    name, results, count, solution = check_discourses_consistency(in_memory_db)
    assert count == 1
    assert re.search(r"3", results)
    assert not re.search(r"9", results)


def test_extra_consistency_logic(in_memory_db):
    # 1. All three populated -> OK.
    s1 = SBS(id=1, extra_example="ex", extra_source="so", extra_sutta="su")
    # 2. extra_example="ex", extra_source="so", extra_sutta="" -> flagged.
    s2 = SBS(id=2, extra_example="ex", extra_source="so", extra_sutta="")
    # 3. extra_source="MJG", extra_example="ex", extra_sutta="" -> OK (exception).
    s3 = SBS(id=3, extra_example="ex", extra_source="MJG", extra_sutta="")
    # 4. All three empty -> OK.
    s4 = SBS(id=4, extra_example="", extra_source="", extra_sutta="")

    in_memory_db.add_all([s1, s2, s3, s4])
    in_memory_db.commit()

    name, results, count, solution = check_extra_consistency(in_memory_db)
    assert count == 1
    assert re.search(r"2", results)


def test_class_anki_logic(in_memory_db):
    # 1. Correct: both present
    s1 = SBS(id=1, class_example="ex", class_anki=2, class_example_translation="tr")
    # 2. Correct: anki is 1, no example needed
    s2 = SBS(id=2, class_example="", class_anki=1, class_example_translation="")
    # 3. Violation: class_example present but class_anki missing
    s3 = SBS(id=3, class_example="ex", class_anki=None, class_example_translation="tr")
    # 4. Violation: class_anki present but class_example missing
    s4 = SBS(id=4, class_example="", class_anki=2, class_example_translation="tr")
    # 5. Violation: class_anki is 2 but class_example_translation missing
    s5 = SBS(id=5, class_example="ex", class_anki=2, class_example_translation="")

    in_memory_db.add_all([s1, s2, s3, s4, s5])
    in_memory_db.commit()

    name, results, count, solution = check_class_anki_consistency(in_memory_db)
    assert count == 3
    assert re.search(r"3", results)
    assert re.search(r"4", results)
    assert re.search(r"5", results)


def test_discourses_source_prefix_logic(in_memory_db):
    # Correct: SN12 is in sbs_category_list (sn12)
    s1 = SBS(id=1, discourses_source="SN12.2")
    # Violation: UNK99 is not in list
    s2 = SBS(id=2, discourses_source="UNK99.1")
    # Correct: MN107 is in list (even without dot)
    s3 = SBS(id=3, discourses_source="MN107")
    # Correct: case insensitive
    s4 = SBS(id=4, discourses_source="mn107.1")

    in_memory_db.add_all([s1, s2, s3, s4])
    in_memory_db.commit()

    name, results, count, solution = check_discourses_source_prefix(in_memory_db)
    assert count == 1
    assert re.search(r"2", results)


def test_discourses_source_full_logic(in_memory_db):
    # 1. discourses_source="SN12.1" -> OK (in list).
    s1 = SBS(id=1, discourses_source="SN12.1")
    # 2. discourses_source="SN12.99" -> flagged (prefix OK but full value not in list).
    s2 = SBS(id=2, discourses_source="SN12.99")
    # 3. discourses_source="MN107" -> OK.
    s3 = SBS(id=3, discourses_source="MN107")
    # 4. discourses_source="" -> OK (skipped).
    s4 = SBS(id=4, discourses_source="")

    in_memory_db.add_all([s1, s2, s3, s4])
    in_memory_db.commit()

    name, results, count, solution = check_discourses_source_full(in_memory_db)
    # Note: MN107 and SN12.1 are in tools.sbs_table_functions.list_of_discourses
    assert count == 1
    assert re.search(r"2", results)


def test_source_has_space_logic(in_memory_db):
    # 1. sbs_source_1="DN 33" -> flagged.
    s1 = SBS(id=1, sbs_source_1="DN 33")
    # 2. pat_source="VIN PAT PA 1" -> OK (contains "PAT").
    s2 = SBS(id=2, pat_source="VIN PAT PA 1")
    # 3. sbs_source_1="Sri Lanka monks" -> OK (contains "Sri Lanka").
    s3 = SBS(id=3, sbs_source_1="Sri Lanka monks")
    # 4. dhp_source="DHP100" -> OK (no space).
    s4 = SBS(id=4, dhp_source="DHP100")
    # 5. discourses_source="SN 12.1" -> flagged.
    s5 = SBS(id=5, discourses_source="SN 12.1")

    in_memory_db.add_all([s1, s2, s3, s4, s5])
    in_memory_db.commit()

    results_list = check_source_has_space(in_memory_db)

    sbs1_res = next(r for r in results_list if r[0] == "source_has_space_sbs_source_1")
    assert sbs1_res[2] == 1  # id 1
    assert re.search(r"1", sbs1_res[1])

    pat_res = next(r for r in results_list if r[0] == "source_has_space_pat_source")
    assert pat_res[2] == 0  # id 2 excepted

    disc_res = next(
        r for r in results_list if r[0] == "source_has_space_discourses_source"
    )
    assert disc_res[2] == 1  # id 5
    assert re.search(r"5", disc_res[1])


def test_sbs_example_population_logic(in_memory_db):
    # 1. Correct: all 6 populated
    s1 = SBS(
        id=1,
        sbs_source_1="so",
        sbs_sutta_1="su",
        sbs_example_1="ex",
        sbs_chant_pali_1="pa",
        sbs_chant_eng_1="en",
        sbs_chapter_1="ch",
    )
    # 2. Violation: one missing (sbs_chapter_1)
    s2 = SBS(
        id=2,
        sbs_source_1="so",
        sbs_sutta_1="su",
        sbs_example_1="ex",
        sbs_chant_pali_1="pa",
        sbs_chant_eng_1="en",
        sbs_chapter_1="",
    )
    # 3. Correct (Exception): sbs_source is "Trad", sbs_sutta can be empty
    s3 = SBS(
        id=3,
        sbs_source_1="Trad",
        sbs_sutta_1="",
        sbs_example_1="ex",
        sbs_chant_pali_1="pa",
        sbs_chant_eng_1="en",
        sbs_chapter_1="ch",
    )
    # 4. Correct: all empty
    s4 = SBS(id=4, sbs_source_1="", sbs_sutta_1="")

    # 5. Check _2 fields: violation
    s5 = SBS(
        id=5,
        sbs_source_2="so",
        sbs_sutta_2="su",
        sbs_example_2="ex",
        sbs_chant_pali_2="",
        sbs_chant_eng_2="en",
        sbs_chapter_2="ch",
    )

    in_memory_db.add_all([s1, s2, s3, s4, s5])
    in_memory_db.commit()

    name, results, count, solution = check_sbs_example_consistency(in_memory_db)
    assert count == 2
    assert re.search(r"2", results)
    assert re.search(r"5", results)


def test_sbs_index_mapping_logic(in_memory_db):
    # Mock CSV data
    csv_content = (
        "index\tpali_chant\tenglish_chant\tchapter\tlink\n"
        "1\tPali1\tEng1\tChap1\tlink1\n"
        "2\tPali2\tEng2\tChap2\tlink2\n"
    )

    # 1. Correct mapping
    s1 = SBS(
        id=1, sbs_chant_pali_1="Pali1", sbs_chant_eng_1="Eng1", sbs_chapter_1="Chap1"
    )
    # 2. Violation: Incorrect Eng mapping
    s2 = SBS(
        id=2, sbs_chant_pali_1="Pali1", sbs_chant_eng_1="WRONG", sbs_chapter_1="Chap1"
    )
    # 3. Violation: Incorrect Chapter mapping
    s3 = SBS(
        id=3, sbs_chant_pali_2="Pali2", sbs_chant_eng_2="Eng2", sbs_chapter_2="WRONG"
    )
    # 4. Correct mapping for _2
    s4 = SBS(
        id=4, sbs_chant_pali_2="Pali2", sbs_chant_eng_2="Eng2", sbs_chapter_2="Chap2"
    )

    in_memory_db.add_all([s1, s2, s3, s4])
    in_memory_db.commit()

    with patch("builtins.open", mock_open(read_data=csv_content)):
        name, results, count, solution = check_sbs_index_mapping(in_memory_db)
        assert count == 2
        assert re.search(r"2", results)
        assert re.search(r"3", results)


def test_bold_tag_verification_logic(in_memory_db):
    # 1. Correct: both tags present
    s1 = SBS(id=1, dhp_example="some <b>bold</b> text")
    # 2. Violation: missing </b>
    s2 = SBS(id=2, dhp_example="some <b>bold text")
    # 3. Violation: missing <b>
    s3 = SBS(id=3, dhp_example="some bold</b> text")
    # 4. Violation: missing both
    s4 = SBS(id=4, dhp_example="no bold text")
    # 5. Correct: empty field
    s5 = SBS(id=5, dhp_example="")

    # Test other fields too
    s6 = SBS(id=6, sbs_example_1="<b>ex</b>", sbs_example_2="no bold")

    in_memory_db.add_all([s1, s2, s3, s4, s5, s6])
    in_memory_db.commit()

    results_list = check_bold_tags(in_memory_db)

    # Check dhp_example results
    dhp_res = next(r for r in results_list if r[0] == "bold_tags_dhp_example")
    assert dhp_res[2] == 3  # ids 2, 3, 4
    assert re.search(r"2", dhp_res[1])
    assert re.search(r"3", dhp_res[1])
    assert re.search(r"4", dhp_res[1])

    # Check sbs_example_2 results
    sbs2_res = next(r for r in results_list if r[0] == "bold_tags_sbs_example_2")
    assert sbs2_res[2] == 1  # id 6
    assert re.search(r"6", sbs2_res[1])


def test_example_capital_letters_logic(in_memory_db):
    # 1. dhp_example="pure pali text" -> OK.
    s1 = SBS(id=1, dhp_example="pure pali text")
    # 2. dhp_example="Text with Capital" -> flagged.
    s2 = SBS(id=2, dhp_example="Text with Capital")
    # 3. sbs_example_1="<b>...</b>" -> OK (lowercase).
    s3 = SBS(id=3, sbs_example_1="<b>...</b>")
    # 4. sbs_example_1="&Auml;" -> flagged (A).
    s4 = SBS(id=4, sbs_example_1="&Auml;")

    in_memory_db.add_all([s1, s2, s3, s4])
    in_memory_db.commit()

    results_list = check_example_capital_letters(in_memory_db)

    dhp_res = next(r for r in results_list if r[0] == "capital_letter_dhp_example")
    assert dhp_res[2] == 1  # id 2
    assert re.search(r"2", dhp_res[1])

    sbs1_res = next(r for r in results_list if r[0] == "capital_letter_sbs_example_1")
    assert sbs1_res[2] == 1  # id 4
    assert re.search(r"4", sbs1_res[1])


def test_example_spacing_logic(in_memory_db):
    # 1. sbs_example_1="foo ,bar" -> flagged by space_comma.
    s1 = SBS(id=1, sbs_example_1="foo ,bar")
    # 2. sbs_example_1="foo ." (end) -> flagged by space_fullstop_edge.
    s2 = SBS(id=2, sbs_example_1="foo .")
    # 3. sbs_example_1="foo . bar" -> flagged by space_fullstop_edge.
    s3 = SBS(id=3, sbs_example_1="foo . bar")
    # 4. sbs_example_1="foo, bar" -> OK.
    s4 = SBS(id=4, sbs_example_1="foo, bar")
    # 5. sbs_example_1="foo." -> OK.
    s5 = SBS(id=5, sbs_example_1="foo.")
    # 6. sbs_example_1="foo , " -> flagged by space_comma_edge.
    s6 = SBS(id=6, sbs_example_1="foo , ")

    in_memory_db.add_all([s1, s2, s3, s4, s5, s6])
    in_memory_db.commit()

    results_list = check_example_spacing(in_memory_db)

    comma_res = next(r for r in results_list if r[0] == "space_comma_sbs_example_1")
    assert re.search(r"1", comma_res[1])
    assert re.search(r"6", comma_res[1])

    comma_edge_res = next(
        r for r in results_list if r[0] == "space_comma_edge_sbs_example_1"
    )
    assert not re.search(r"1", comma_edge_res[1])  # " ,bar" is not edge
    assert re.search(r"6", comma_edge_res[1])

    dot_edge_res = next(
        r for r in results_list if r[0] == "space_fullstop_edge_sbs_example_1"
    )
    assert re.search(r"2", dot_edge_res[1])
    assert re.search(r"3", dot_edge_res[1])


def test_class_translation_uniqueness_logic(in_memory_db):
    # 1. Correct: same translation, same source
    s1 = SBS(id=1, class_example_translation="tr1", class_source="so1")
    s2 = SBS(id=2, class_example_translation="tr1", class_source="so1")

    # 2. Violation: same translation, different sources
    s3 = SBS(id=3, class_example_translation="tr2", class_source="so1")
    s4 = SBS(id=4, class_example_translation="tr2", class_source="so2")

    # 3. Correct: different translations, different sources
    s5 = SBS(id=5, class_example_translation="tr3", class_source="so3")

    # 4. Correct: empty translation
    s6 = SBS(id=6, class_example_translation="", class_source="so4")
    s7 = SBS(id=7, class_example_translation="", class_source="so5")

    in_memory_db.add_all([s1, s2, s3, s4, s5, s6, s7])
    in_memory_db.commit()

    name, results, count, solution = check_class_translation_uniqueness(in_memory_db)
    # Expect count to be 1 (one translation 'tr2' has conflicts)
    assert count == 1

    assert re.search(r"so1", results)
    assert re.search(r"so2", results)
    assert "tr2" in results
    assert not re.search(r"3", results)  # Should not contain IDs


def test_run_returns_exit_code(in_memory_db):
    with patch(
        "db_tests.sbs_consistency_tests.get_db_session", return_value=in_memory_db
    ):
        with patch("db_tests.sbs_consistency_tests.ProjectPaths") as mock_paths:
            mock_paths.return_value.dpd_db_path = "fake"

            # Case 1: Empty DB -> should pass (0)
            exit_code = run_sbs_consistency_tests()
            assert exit_code == 0

            # Case 2: Injected error
            s1 = SBS(id=1, dhp_example="ex", dhp_source="so", dhp_sutta="")
            in_memory_db.add(s1)
            in_memory_db.commit()

            exit_code = run_sbs_consistency_tests()
            assert exit_code == 1
