"""Tests for ru_cognate unit building, the Wiktionary join and ledger I/O."""

import json
from pathlib import Path

import pytest

from scripts.ru_cognate import ru_cognate_ledger as led
from scripts.ru_cognate.ru_cognate_etyma import (
    index_pali,
    index_protoslavic,
    index_russian,
    index_sanskrit,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"

NOVYJ_LINE = json.dumps(
    {
        "word": "новый",
        "lang_code": "ru",
        "etymology_text": "",
        "etymology_templates": [
            {"name": "inh", "args": {"1": "ru", "2": "sla-pro", "3": "*nòvъ"}}
        ],
    },
    ensure_ascii=False,
)


def fixture_lines(name: str) -> list[str]:
    return (FIXTURES / name).read_text(encoding="utf-8").splitlines()


def hw(
    lemma: str,
    root: str = "",
    family: str = "",
    sanskrit: str = "",
    meaning: str = "",
    non_ia: str = "",
    cognate: str = "",
) -> dict[str, str]:
    return {
        "lemma_1": lemma,
        "root_key": root,
        "family_word": family,
        "sanskrit": sanskrit,
        "meaning_1": meaning,
        "non_ia": non_ia,
        "cognate": cognate,
    }


def root_row(root: str, sanskrit_root: str, meaning: str = "m") -> dict[str, str]:
    return {"root": root, "sanskrit_root": sanskrit_root, "root_meaning": meaning}


def make_indexes() -> tuple[
    dict[str, set[str]], dict[str, set[str]], dict[str, set[str]]
]:
    by_rom, by_word = index_sanskrit(fixture_lines("sanskrit.jsonl"))
    pali = index_pali(fixture_lines("pali.jsonl"), by_word)
    psl = index_protoslavic(fixture_lines("protoslavic.jsonl"))
    ru = index_russian([*fixture_lines("russian.jsonl"), NOVYJ_LINE], psl)
    return by_rom, pali, ru


def by_key(units: list[led.Unit]) -> dict[str, led.Unit]:
    return {u.row["unit_key"]: u for u in units}


def test_root_unit_splits_sanskrit_roots() -> None:
    units = led.build_units(
        [root_row("√argh", "√argh √arh")], [hw("argha", root="√argh")]
    )
    assert units[0].sanskrit_terms == ["argh", "arh"]
    assert units[0].row["sanskrit"] == "argh, arh"
    assert units[0].row["headword_count"] == "1"


def test_family_collects_and_cleans_sanskrit() -> None:
    units = led.build_units(
        [],
        [
            hw("mātar", family="mātar", sanskrit="mātar, mātṛ", meaning="mother"),
            hw("mātaraṃ", family="mātar", sanskrit="mātaram"),
            hw("dvikkhattuṃ", family="mātar", sanskrit="dvi + kṛtvas"),
            hw("x 1", family="mātar", sanskrit=""),
        ],
    )
    assert len(units) == 1
    unit = units[0]
    assert unit.row["unit_type"] == "family"
    assert unit.sanskrit_terms == ["mātar", "mātṛ", "mātaram"]
    assert unit.row["pali_meaning"] == "mother"
    assert unit.row["headword_count"] == "4"
    assert unit.pali_words == ["mātar", "mātaraṃ", "dvikkhattuṃ", "x"]


def test_family_ignores_rooted_headwords_and_strips_brackets() -> None:
    units = led.build_units(
        [root_row("√dvar", "√dvṛ")],
        [
            hw("dvāra 1", root="√dvar", family="dvāra", sanskrit="dvāra [dvṛ]"),
            hw("a", family="fam", sanskrit="dvāra [dvṛ]"),
        ],
    )
    assert [u.row["unit_key"] for u in units] == ["√dvar", "fam"]
    assert units[1].sanskrit_terms == ["dvāra"]


def test_non_ia_unit_is_none() -> None:
    units = led.build_units(
        [], [hw("vali", family="vali", non_ia="vali 'wrinkle' (Tamil)")]
    )
    assert units[0].row["status"] == "none"
    assert units[0].row["verifier_note"] == "non-IA"
    assert units[0].row["ru_candidates"] == ""


def test_en_cognate_collected() -> None:
    units = led.build_units(
        [],
        [hw("a", family="f", cognate="Eng. door"), hw("b", family="f", cognate="")],
    )
    assert units[0].row["en_cognate"] == "Eng. door"


def test_ledger_round_trip(tmp_path: Path) -> None:
    units = led.build_units([root_row("√budh", "√budh", 'say "x"')], [])
    rows = [u.row for u in units]
    path = tmp_path / "ledger.tsv"
    led.write_ledger(path, rows)
    assert led.read_ledger(path) == rows
    assert path.read_text(encoding="utf-8").splitlines()[0].split("\t") == led.COLUMNS
    assert not list(tmp_path.glob("*.tmp"))


def test_ru_flagged_column_follows_ru_final_and_starts_empty() -> None:
    assert led.COLUMNS.index("ru_flagged") == led.COLUMNS.index("ru_final") + 1
    units = led.build_units([root_row("√budh", "√budh", "wake")], [])
    assert units[0].row["ru_flagged"] == ""


def test_join_family_dvara_gives_door() -> None:
    units = led.build_units([], [hw("dvāra", family="dvāra", sanskrit="dvāra")])
    led.join_units(units, *make_indexes())
    row = units[0].row
    assert row["ru_candidates"] == "дверь"
    assert row["status"] == "proposed"
    assert row["method"] == "join"
    assert row["pie_id"] == ""
    assert "dʰwer" in row["pie_root"]
    assert "дверь" in row["source"]


def test_join_family_nava_gives_new() -> None:
    units = led.build_units([], [hw("nava 1", family="nava1", sanskrit="nava")])
    led.join_units(units, *make_indexes())
    assert units[0].row["ru_candidates"] == "новый"


def test_join_known_misses_stay_pending() -> None:
    units = led.build_units(
        [root_row("√budh", "√budh"), root_row("√dvar", "√dvṛ")],
        [hw("buddha", root="√budh"), hw("dvāra 1", root="√dvar")],
    )
    led.join_units(units, *make_indexes())
    units_by_key = by_key(units)
    assert units_by_key["√budh"].row["status"] == "pending"
    assert units_by_key["√dvar"].row["status"] == "pending"
    assert units_by_key["√budh"].row["ru_candidates"] == ""


def test_join_does_not_touch_non_ia() -> None:
    units = led.build_units(
        [], [hw("dvāra", family="dvāra", sanskrit="dvāra", non_ia="x")]
    )
    led.join_units(units, *make_indexes())
    assert units[0].row["status"] == "none"
    assert units[0].row["ru_candidates"] == ""


def test_join_pali_side_without_russian_match_stays_pending() -> None:
    # Pali `mātar` reaches méh₂tēr through the Sanskrit hop, but the fixture has no
    # Russian мать line, so it stays pending (and an empty sanskrit side does not crash).
    units = led.build_units([], [hw("mātar", family="mātar")])
    led.join_units(units, *make_indexes())
    assert units[0].row["status"] == "pending"


def test_candidates_capped_at_ten_shortest_first() -> None:
    words = {"а" * n for n in range(1, 13)}
    units = led.build_units([], [hw("abc", family="abc", sanskrit="abc")])
    led.join_units(units, {"abc": {"k"}}, {}, {"k": words})
    row = units[0].row
    candidates = row["ru_candidates"].split(", ")
    assert len(candidates) == 10
    assert candidates[0] == "а"
    assert candidates == sorted(candidates, key=lambda w: (len(w), w))
    assert row["source"].endswith("+2 more")


def test_clean_candidates_drops_affixes_keeps_internal_hyphen() -> None:
    assert led.clean_candidates(["-ед", "су-", "кое-что", "еда"], "family") == [
        "кое-что",
        "еда",
    ]


def test_clean_candidates_closed_class_only_dropped_for_roots() -> None:
    assert led.clean_candidates(["кто", "кость"], "root") == ["кость"]
    assert led.clean_candidates(["кто", "кость"], "family") == ["кто", "кость"]


def test_clean_candidates_dedupes_after_accent_strip_in_order() -> None:
    assert led.clean_candidates(["е\u0301да", "вода", "еда"], "family") == [
        "еда",
        "вода",
    ]


def test_join_cleans_before_the_ten_cap() -> None:
    closed = list(led.CLOSED_CLASS_RU)[:10]
    words = {*closed, "длиннослово"}
    units = led.build_units([root_row("√x", "x")], [])
    led.join_units(units, {"x": {"k"}}, {}, {"k": words})
    assert units[0].row["ru_candidates"] == "длиннослово"


def test_join_closed_class_only_root_stays_pending() -> None:
    units = led.build_units([root_row("√x", "x")], [])
    led.join_units(units, {"x": {"k"}}, {}, {"k": {"и", "он"}})
    row = units[0].row
    assert row["status"] == "pending"
    assert row["ru_candidates"] == ""


def _ledger_row(status: str, candidates: str, unit_type: str = "root") -> led.Row:
    row = {column: "" for column in led.COLUMNS}
    row.update(
        unit_type=unit_type,
        unit_key="√x",
        status=status,
        ru_candidates=candidates,
        pie_root="p",
        source="s",
        method="join",
    )
    return row


def test_clean_ledger_only_touches_proposed_rows_and_counts() -> None:
    verified = _ledger_row("verified", "-ед, еда")
    proposed = _ledger_row("proposed", "-ед, еда, он", "root")
    rows = [verified, proposed]
    assert led.clean_ledger(rows) == (1, 2)
    assert verified["ru_candidates"] == "-ед, еда"
    assert proposed["ru_candidates"] == "еда"
    assert proposed["status"] == "proposed"


def test_clean_ledger_emptied_row_becomes_pending() -> None:
    row = _ledger_row("proposed", "-ед, он")
    assert led.clean_ledger([row]) == (1, 2)
    assert row["status"] == "pending"
    for column in ("pie_root", "source", "method", "ru_candidates"):
        assert row[column] == ""


def test_full_join_refuses_existing_ledger(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.tsv"
    ledger.write_text("keep", encoding="utf-8")
    assert led.run_full_join(tmp_path, ledger) == 1
    assert ledger.read_text(encoding="utf-8") == "keep"


def test_read_ledger_rejects_wrong_columns(tmp_path: Path) -> None:
    path = tmp_path / "bad.tsv"
    path.write_text("a\tb\n1\t2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        led.read_ledger(path)
