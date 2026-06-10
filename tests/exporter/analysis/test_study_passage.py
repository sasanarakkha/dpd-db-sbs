"""Verify Stage 1 passage preview truncation and multi-select parsing."""

from exporter.analysis.passage_extraction import format_extraction_report
from exporter.analysis.study_passage import (
    _format_selection_preview,
    _parse_selection_indices,
    _select_passage,
)
from exporter.analysis.passage_by_code import PassageResult


def test_format_selection_preview_truncates_long_units() -> None:
    result = PassageResult(
        source="AN3.12",
        vagga="rathakāravaggo, sāraṇīyasuttaṃ",
        paragraphs=[
            "one two three four five six seven eight nine ten eleven twelve "
            "thirteen fourteen",
        ],
        is_verse=False,
    )

    preview = _format_selection_preview(result)

    assert (
        "## Paragraph 1 (14 words): one two three four five six seven eight "
        "nine ten eleven twelve…"
    ) in preview
    assert "thirteen fourteen" not in preview


def test_format_selection_preview_keeps_short_units_untruncated() -> None:
    result = PassageResult(
        source="DHP1",
        vagga="yamakavaggo",
        paragraphs=["one two three"],
        is_verse=True,
    )

    preview = _format_selection_preview(result)

    assert "## Verse 1 (3 words): one two three" in preview
    assert "…" not in preview


def test_format_selection_preview_header_matches_extraction_preview() -> None:
    result = PassageResult(
        source="AN3.12",
        vagga="rathakāravaggo, sāraṇīyasuttaṃ",
        paragraphs=[
            "tīṇimāni, bhikkhave, rañño khattiyassa.",
            "puna caparaṃ, bhikkhave.",
        ],
        is_verse=False,
    )

    selection_header = _format_selection_preview(result).splitlines()[:3]
    extraction_header = format_extraction_report(result).splitlines()[:3]

    assert selection_header == extraction_header


def test_parse_selection_indices_supports_ranges_and_mixed_input() -> None:
    assert _parse_selection_indices("1-2 5", 6) == [0, 1, 4]
    assert _parse_selection_indices("3 5", 6) == [2, 4]
    assert _parse_selection_indices("3-5", 6) == [2, 3, 4]


def test_parse_selection_indices_rejects_out_of_bounds_values() -> None:
    assert _parse_selection_indices("0 2", 4) is None
    assert _parse_selection_indices("2-5", 4) is None
    assert _parse_selection_indices("x", 4) is None


def test_select_passage_returns_joined_mixed_selection(
    monkeypatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "1-2 4")

    result = PassageResult(
        source="AN3.12",
        vagga="rathakāravaggo, sāraṇīyasuttaṃ",
        paragraphs=[
            "paragraph one",
            "paragraph two",
            "paragraph three",
            "paragraph four",
        ],
        is_verse=False,
    )
    passage, suffix = _select_passage(result)

    assert passage == "paragraph one\nparagraph two\nparagraph four"
    assert suffix == "_p1-2-4"


def test_select_passage_falls_back_to_all_on_invalid_input(
    monkeypatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "1-9")

    result = PassageResult(
        source="AN3.12",
        vagga="rathakāravaggo, sāraṇīyasuttaṃ",
        paragraphs=[
            "paragraph one",
            "paragraph two",
        ],
        is_verse=False,
    )
    passage, suffix = _select_passage(result)

    assert passage == "paragraph one\nparagraph two"
    assert suffix == ""
