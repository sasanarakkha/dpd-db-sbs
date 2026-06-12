"""Test SBS gāthā line splitting and verse-source detection."""

import csv
from pathlib import Path
from types import SimpleNamespace

from scripts.change_in_db.sbs_dpd_example_transfers import (
    collect_transfer_candidates_for_row,
    normalize_example_for_match,
)
from scripts.change_in_db.rearrange_sbs_gatha_lines import (
    ReviewRow,
    collect_concern_rows,
    is_verse_source,
    split_gatha_lines,
    write_review_tsv,
)


def test_split_two_padas_per_line_to_four_lines() -> None:
    text = "mano pubbaṅgamā dhammā, manoseṭṭhā manomayā,\nmanasā ce paduṭṭhena, bhāsati vā karoti vā,"

    result = split_gatha_lines(text)

    assert result == (
        "mano pubbaṅgamā dhammā,\n"
        "manoseṭṭhā manomayā,\n"
        "manasā ce paduṭṭhena,\n"
        "bhāsati vā karoti vā,"
    )


def test_split_flat_four_pada_verse_to_four_lines() -> None:
    text = "appamādo amatapadaṃ, pamādo maccuno padaṃ, appamattā na mīyanti, ye pamattā yathā matā."

    result = split_gatha_lines(text)

    assert result == (
        "appamādo amatapadaṃ,\n"
        "pamādo maccuno padaṃ,\n"
        "appamattā na mīyanti,\n"
        "ye pamattā yathā matā."
    )


def test_split_already_correct_four_line_verse_is_idempotent() -> None:
    text = (
        "appamādo amatapadaṃ,\n"
        "pamādo maccuno padaṃ,\n"
        "appamattā na mīyanti,\n"
        "ye pamattā yathā matā."
    )

    assert split_gatha_lines(text) == text


def test_split_already_correct_six_line_verse_is_idempotent() -> None:
    text = (
        "yaṅkiñci vittaṃ idha vā huraṃ vā,\n"
        "saggesu vā yaṃ ratanaṃ paṇītaṃ,\n"
        "na no samaṃ atthi tathāgatena,\n"
        "idampi buddhe ratanaṃ paṇītaṃ,\n"
        "etena saccena suvatthi hotu,\n"
        "khayaṃ virāgaṃ amataṃ paṇītaṃ."
    )

    assert split_gatha_lines(text) == text


def test_split_preserves_bold_markup() -> None:
    text = "etaṃ <b>mama</b>, esohamasmi, eso me attā, na hoti."

    result = split_gatha_lines(text)

    assert result == "etaṃ <b>mama</b>,\nesohamasmi,\neso me attā,\nna hoti."


def test_split_preserves_existing_period_separated_lines() -> None:
    text = (
        "ajj'eva kiccam'ātappaṃ,\n"
        "ko jaññā maraṇaṃ suve.\n"
        "na hi no saṅgaran'tena,\n"
        "mahāsenena maccunā."
    )

    assert split_gatha_lines(text) == text


def test_split_internal_period_space_to_new_line() -> None:
    text = (
        "saññā-virattassa na santi ganthā, paññā-vimuttassa na santi mohā. "
        "saññañ'ca diṭṭhiñ'ca ye <b>aggahesuṃ</b>, te ghaṭṭayantā vicaranti loke'ti."
    )

    result = split_gatha_lines(text)

    assert result == (
        "saññā-virattassa na santi ganthā,\n"
        "paññā-vimuttassa na santi mohā.\n"
        "saññañ'ca diṭṭhiñ'ca ye <b>aggahesuṃ</b>,\n"
        "te ghaṭṭayantā vicaranti loke'ti."
    )


def test_split_keeps_short_one_word_comma_run_together() -> None:
    text = (
        "mettañ'ca sabbalokasmiṃ, mānasam'bhāvaye aparimāṇaṃ, "
        "uddhaṃ <b>adho</b> ca tiriyañ'ca, asambādhaṃ, averaṃ, asapattaṃ."
    )

    result = split_gatha_lines(text)

    assert result == (
        "mettañ'ca sabbalokasmiṃ,\n"
        "mānasam'bhāvaye aparimāṇaṃ,\n"
        "uddhaṃ <b>adho</b> ca tiriyañ'ca,\n"
        "asambādhaṃ, averaṃ, asapattaṃ."
    )


def test_split_groups_short_internal_comma_word_with_next_phrase() -> None:
    text = "atha kho, bhikkhave, bhikkhū nisīdiṃsu, dhammaṃ suṇiṃsu, anumodiṃsu."

    result = split_gatha_lines(text)

    assert result.splitlines() == [
        "atha kho, bhikkhave,",
        "bhikkhū nisīdiṃsu,",
        "dhammaṃ suṇiṃsu,",
        "anumodiṃsu.",
    ]


def test_split_groups_short_two_word_phrase_with_next_phrase() -> None:
    text = (
        "<b>kayirā</b> ce, kayirāth'enaṃ, daḷham'enaṃ parakkame.\n"
        "sithilo hi paribbājo, bhiyyo ākirate rajaṃ."
    )

    result = split_gatha_lines(text)

    assert result == (
        "<b>kayirā</b> ce, kayirāth'enaṃ,\n"
        "daḷham'enaṃ parakkame.\n"
        "sithilo hi paribbājo,\n"
        "bhiyyo ākirate rajaṃ."
    )


def test_split_does_not_create_blank_lines_from_trailing_comma_space() -> None:
    text = (
        "gaha<b>kāraka</b> diṭṭho'si,\n"
        "puna gehaṃ na kāhasi, \n"
        "sabbā te phāsukā bhaggā,\n"
        "gahakūṭaṃ visaṅkhataṃ, \n"
        "visaṅkhāragataṃ cittaṃ,\n"
        "taṇhānaṃ khayam'ajjhagā."
    )

    result = split_gatha_lines(text)

    assert result == (
        "gaha<b>kāraka</b> diṭṭho'si,\n"
        "puna gehaṃ na kāhasi,\n"
        "sabbā te phāsukā bhaggā,\n"
        "gahakūṭaṃ visaṅkhataṃ,\n"
        "visaṅkhāragataṃ cittaṃ,\n"
        "taṇhānaṃ khayam'ajjhagā."
    )


def test_long_one_word_padas_are_not_concerns() -> None:
    before = (
        "vītataṇho anādāno, niruttipadakovido,\n"
        "<b>akkharānaṃ</b> sannipātaṃ,\n"
        "jaññā pubbāparāni ca, sa ve antimasārīro,\n"
        "mahāpañño mahāpuriso'ti vuccati."
    )
    after = split_gatha_lines(before)

    concern_rows = collect_concern_rows(
        entry_id=386,
        field_name="dhp_example",
        source="DHP352",
        before=before,
        after=after,
    )

    assert "niruttipadakovido," in after
    assert concern_rows == []


def test_short_one_word_over_four_lines_is_a_concern() -> None:
    after = "ekaṃ,\ndve,\ntīṇi,\nvā,\ncattāri."

    concern_rows = collect_concern_rows(
        entry_id=1,
        field_name="dhp_example",
        source="DHP1",
        before="ekaṃ, dve, tīṇi, vā, cattāri.",
        after=after,
    )

    assert [row.line for row in concern_rows] == [
        "ekaṃ,",
        "dve,",
        "tīṇi,",
        "vā,",
        "cattāri.",
    ]


def test_split_keeps_trailing_punctuation_untouched() -> None:
    assert split_gatha_lines("dīghasaddapariyāyo, dve,") == (
        "dīghasaddapariyāyo,\ndve,"
    )
    assert split_gatha_lines("dīghasaddapariyāyo, dve.") == (
        "dīghasaddapariyāyo,\ndve."
    )


def test_split_empty_string_is_empty() -> None:
    assert split_gatha_lines("") == ""


def test_is_verse_source_matches_verse_only_prefixes() -> None:
    assert is_verse_source("DHP191")
    assert is_verse_source("Snp 1.1")
    assert is_verse_source("THAG 10.1")
    assert is_verse_source("thig 1.2")
    assert is_verse_source("VV 1")
    assert is_verse_source("PV 2")


def test_is_verse_source_rejects_mixed_or_empty_sources() -> None:
    assert not is_verse_source("")
    assert not is_verse_source("AN 1.1")
    assert not is_verse_source("MN10")
    assert not is_verse_source("DhpA 1")


def test_write_review_tsv_escapes_newlines(tmp_path: Path) -> None:
    review_path = tmp_path / "review.tsv"
    rows = [
        ReviewRow(
            entry_id=1,
            field="dhp_example",
            source="DHP1",
            before="ekaṃ,\ndve",
            after="ekaṃ,\ndve,\ntīṇi",
        )
    ]

    write_review_tsv(rows, review_path)

    with review_path.open(encoding="utf-8", newline="") as f:
        written_rows = list(csv.reader(f, delimiter="\t"))
    assert written_rows == [
        ["id", "field", "source", "before", "after"],
        ["1", "dhp_example", "DHP1", r"ekaṃ,\ndve", r"ekaṃ,\ndve,\ntīṇi"],
    ]


def test_normalize_example_for_match_ignores_markup_punctuation_and_spaces() -> None:
    sbs_text = "saññā-virattassa na santi ganthā,\n<b>paññā</b>-vimuttassa."
    dpd_text = "Saññā virattassa na santi ganthā <b>paññā</b> vimuttassa"

    assert normalize_example_for_match(sbs_text) == normalize_example_for_match(
        dpd_text
    )


def test_collect_transfer_candidates_for_same_id_source_and_normalized_text() -> None:
    dpd = SimpleNamespace(
        id=1,
        source_1="DHP1",
        example_1=(
            "mano pubbaṅgamā dhammā,\n"
            "manoseṭṭhā manomayā,\n"
            "manasā ce paduṭṭhena,\n"
            "bhāsati vā karoti vā."
        ),
        source_2="",
        example_2="",
    )
    sbs = SimpleNamespace(
        id=1,
        sbs_source_1="DHP1",
        sbs_example_1=(
            "mano pubbaṅgamā dhammā, manoseṭṭhā manomayā, "
            "manasā ce paduṭṭhena, bhāsati vā karoti vā."
        ),
        sbs_source_2="",
        sbs_example_2="",
        dhp_source="",
        dhp_example="",
        pat_source="",
        pat_example="",
        vib_source="",
        vib_example="",
        class_source="",
        class_example="",
        discourses_source="",
        discourses_example="",
        extra_source="",
        extra_example="",
    )

    candidates = collect_transfer_candidates_for_row(dpd, sbs)

    assert len(candidates) == 1
    assert candidates[0].sbs_field == "sbs_example_1"
    assert candidates[0].dpd_field == "example_1"
    assert candidates[0].dpd_example == dpd.example_1


def test_collect_transfer_candidates_rejects_different_sources() -> None:
    dpd = SimpleNamespace(
        id=1,
        source_1="DHP1",
        example_1="mano pubbaṅgamā dhammā.",
        source_2="",
        example_2="",
    )
    sbs = SimpleNamespace(
        id=1,
        sbs_source_1="DHP2",
        sbs_example_1="mano pubbaṅgamā dhammā.",
        sbs_source_2="",
        sbs_example_2="",
        dhp_source="",
        dhp_example="",
        pat_source="",
        pat_example="",
        vib_source="",
        vib_example="",
        class_source="",
        class_example="",
        discourses_source="",
        discourses_example="",
        extra_source="",
        extra_example="",
    )

    assert collect_transfer_candidates_for_row(dpd, sbs) == []


def test_collect_transfer_candidates_accepts_non_migration_target() -> None:
    dpd = SimpleNamespace(
        id=1,
        source_1="MN1",
        example_1="idaṃ prose example.",
        source_2="",
        example_2="",
    )
    sbs = SimpleNamespace(
        id=1,
        sbs_source_1="MN1",
        sbs_example_1="idaṃ prose example",
        sbs_source_2="",
        sbs_example_2="",
        dhp_source="",
        dhp_example="",
        pat_source="",
        pat_example="",
        vib_source="",
        vib_example="",
        class_source="",
        class_example="",
        discourses_source="",
        discourses_example="",
        extra_source="",
        extra_example="",
    )

    candidates = collect_transfer_candidates_for_row(dpd, sbs)

    assert len(candidates) == 1
    assert candidates[0].sbs_field == "sbs_example_1"


def test_collect_transfer_candidates_accepts_unstable_dpd_example() -> None:
    dpd = SimpleNamespace(
        id=1,
        source_1="DHP1",
        example_1="mano pubbaṅgamā dhammā, manoseṭṭhā manomayā.",
        source_2="",
        example_2="",
    )
    sbs = SimpleNamespace(
        id=1,
        sbs_source_1="DHP1",
        sbs_example_1="mano pubbaṅgamā dhammā,\nmanoseṭṭhā manomayā.",
        sbs_source_2="",
        sbs_example_2="",
        dhp_source="",
        dhp_example="",
        pat_source="",
        pat_example="",
        vib_source="",
        vib_example="",
        class_source="",
        class_example="",
        discourses_source="",
        discourses_example="",
        extra_source="",
        extra_example="",
    )

    candidates = collect_transfer_candidates_for_row(dpd, sbs)

    assert len(candidates) == 1
    assert candidates[0].dpd_example == dpd.example_1
