"""Unit tests for extract_translations.py's pure functions — generic across any book code."""

from pathlib import Path

import pytest

from scripts.export.extract_translations import (
    apply_combines,
    build_translation_map,
    natural_sort_key,
    parse_combine_arg,
    sorted_rows,
    write_tsv,
)

ITEMS = [
    {"num": "TH1", "translation": "trans one", "literal_translation": "lit one"},
    {"num": "TH2", "translation": "trans two", "literal_translation": "lit two"},
    {"num": "TH11", "translation": "trans eleven", "literal_translation": "lit eleven"},
]


def test_build_translation_map() -> None:
    result = build_translation_map(ITEMS)
    assert result == {
        "TH1": ("trans one", "lit one"),
        "TH2": ("trans two", "lit two"),
        "TH11": ("trans eleven", "lit eleven"),
    }


def test_parse_combine_arg() -> None:
    assert parse_combine_arg("TH1-2=TH1,TH2") == ("TH1-2", ["TH1", "TH2"])


def test_apply_combines_adds_without_removing_sources() -> None:
    translations = build_translation_map(ITEMS)
    result = apply_combines(translations, [("TH1-2", ["TH1", "TH2"])])

    assert result["TH1-2"] == ("trans one trans two", "lit one lit two")
    # Original entries must still be present, untouched.
    assert result["TH1"] == ("trans one", "lit one")
    assert result["TH2"] == ("trans two", "lit two")


def test_apply_combines_unknown_source_raises() -> None:
    translations = build_translation_map(ITEMS)
    with pytest.raises(ValueError, match="TH99"):
        apply_combines(translations, [("TH1-99", ["TH1", "TH99"])])


def test_natural_sort_key_orders_numerically() -> None:
    values = ["TH11", "TH2", "TH1"]
    assert sorted(values, key=natural_sort_key) == ["TH1", "TH2", "TH11"]


def test_sorted_rows() -> None:
    translations = build_translation_map(ITEMS)
    rows = sorted_rows(translations)
    assert rows == [
        ("TH1", "trans one", "lit one"),
        ("TH2", "trans two", "lit two"),
        ("TH11", "trans eleven", "lit eleven"),
    ]


def test_write_tsv_quotes_embedded_newline(tmp_path: Path) -> None:
    output = tmp_path / "out.tsv"
    rows = [("TH1", "line one\nline two", "lit one")]
    write_tsv(output, rows)

    content = output.read_text(encoding="utf-8")
    assert content.splitlines()[0] == "source\ttranslation\tliteral_translation"
    # csv.writer quotes fields containing the embedded newline.
    assert '"line one\nline two"' in content

    # Round-trip via csv.reader must recover the original 3 fields (not more).
    import csv

    with open(output, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        data_row = next(reader)

    assert header == ["source", "translation", "literal_translation"]
    assert data_row == ["TH1", "line one\nline two", "lit one"]
