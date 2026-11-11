"""Golden-master and filter tests for pat_for_anki.process_patimokkha_csv()."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from scripts.work_with_csv import pat_for_anki

FIXTURES_PATH = Path(__file__).parent / "test_pat_for_anki_fixtures.json"
FIXTURES = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))

# Deliberately naive: .astimezone() on a naive datetime attaches the local
# tzinfo without shifting the wall-clock date, keeping this reproducible
# across machines regardless of timezone.
FIXED_NOW = datetime(2026, 6, 19, 10, 30, 0)  # noqa: DTZ001

REAL_PAT_LINKS = Path("shared_data/sbs_csvs/pat_links.tsv").resolve()

NORMAL_ROWS = [
    {
        "pali": "buddho",
        "pos": "noun",
        "grammar": "nom sg masc",
        "meaning": "the Buddha",
        "source": "nidānuddeso",
    },
    {
        "pali": "dhammo",
        "pos": "noun",
        "grammar": "nom sg masc",
        "meaning": "",
        "source": "nidānuddeso",
    },
    {
        "pali": "saṅgho",
        "pos": "",
        "grammar": "nom sg masc",
        "meaning": "the community",
        "source": "nidānuddeso",
    },
    {
        "pali": "vinayo",
        "pos": "noun",
        "grammar": "nom sg masc",
        "meaning": "discipline",
        "source": "unknown_source",
    },
]


def _write_input_csv(
    path: Path, rows: list[dict], *, include_meaning_col: bool = True
) -> None:
    cols = ["pali", "pos", "grammar", "source"]
    if include_meaning_col:
        cols.insert(3, "meaning")
    lines = ["\t".join(cols)]
    for row in rows:
        lines.append("\t".join(str(row.get(c, "")) for c in cols))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run(
    tmp_path: Path,
    rows: list[dict],
    *,
    include_meaning_col: bool = True,
    links_path: str | None = "real",
    sbs_dir_exists: bool = True,
) -> dict[str, str | None]:
    anki_csvs_dir = tmp_path / "anki_csvs"
    sbs_style_dir = tmp_path / "sbs_style"

    input_csv_path = tmp_path / "patimokkha_word_by_word.tsv"
    _write_input_csv(input_csv_path, rows, include_meaning_col=include_meaning_col)

    if links_path == "real":
        pat_links_path = REAL_PAT_LINKS
    elif links_path == "missing":
        pat_links_path = tmp_path / "does_not_exist.tsv"
    elif links_path == "bad":
        pat_links_path = tmp_path / "bad_links.tsv"
        pat_links_path.write_text("source\nnidānuddeso\n", encoding="utf-8")
    else:
        pat_links_path = tmp_path / "links.tsv"
        pat_links_path.write_text("source\tweb_link\n", encoding="utf-8")

    if sbs_dir_exists:
        sbs_style_dir.mkdir()

    fake_dpspth = type(
        "FakeDpspth",
        (),
        {
            "anki_csvs_dir": anki_csvs_dir,
            "pat_links_path": pat_links_path,
            "pat_source_path": input_csv_path,
            "sbs_anki_style_dir": sbs_style_dir,
        },
    )()

    with (
        patch.object(pat_for_anki, "dpspth", fake_dpspth),
        patch("scripts.work_with_csv.pat_for_anki.datetime") as mock_dt,
    ):
        mock_dt.today.return_value = FIXED_NOW
        mock_dt.now.return_value = FIXED_NOW.astimezone()
        pat_for_anki.process_patimokkha_csv()

    output_csv_path = anki_csvs_dir / "anki_patimokkha.csv"
    field_list_path = sbs_style_dir / "field-list-pat.md"
    return {
        "output_csv": output_csv_path.read_text(encoding="utf-8")
        if output_csv_path.exists()
        else None,
        "field_list_md": field_list_path.read_text(encoding="utf-8")
        if field_list_path.exists()
        else None,
    }


def test_normal(tmp_path: Path) -> None:
    result = _run(tmp_path, NORMAL_ROWS, links_path="real")
    assert result == FIXTURES["normal"]


def test_no_meaning_column(tmp_path: Path) -> None:
    result = _run(tmp_path, NORMAL_ROWS, include_meaning_col=False, links_path="real")
    assert result == FIXTURES["no_meaning_column"]


def test_no_sources_links_file(tmp_path: Path) -> None:
    result = _run(tmp_path, NORMAL_ROWS, links_path="missing")
    assert result == FIXTURES["no_sources_links_file"]


def test_bad_sources_links_file(tmp_path: Path) -> None:
    result = _run(tmp_path, NORMAL_ROWS, links_path="bad")
    assert result == FIXTURES["bad_sources_links_file"]


def test_no_sbs_style_dir(tmp_path: Path) -> None:
    result = _run(tmp_path, NORMAL_ROWS, links_path="real", sbs_dir_exists=False)
    assert result == FIXTURES["no_sbs_style_dir"]


def test_empty_input_does_not_crash(tmp_path: Path) -> None:
    """Old code raised ValueError('cannot set a frame with no defined index and a
    scalar') here on pandas 3.0 when zero rows survive filtering. Fixed as part of
    this pass; new behavior is an output CSV with headers only."""
    result = _run(tmp_path, [], links_path="real")
    assert result["output_csv"] is not None
    lines = result["output_csv"].strip().splitlines()
    assert len(lines) == 1
    assert "pali" in lines[0]


def test_no_matching_rows_does_not_crash(tmp_path: Path) -> None:
    """Same pre-existing bug as test_empty_input_does_not_crash, triggered instead
    by a non-empty input where every row fails the filter."""
    rows = [
        {
            "pali": "x",
            "pos": "p",
            "grammar": "g",
            "meaning": "",
            "source": "s",
        },
        {
            "pali": "y",
            "pos": "",
            "grammar": "g",
            "meaning": "m",
            "source": "s",
        },
    ]
    result = _run(tmp_path, rows, links_path="real")
    assert result["output_csv"] is not None
    lines = result["output_csv"].strip().splitlines()
    assert len(lines) == 1
    assert "pali" in lines[0]


def _rows(*specs: tuple[str, str, str]) -> list[dict]:
    return [
        {"pali": p, "pos": pos, "grammar": "g", "meaning": m, "source": "s"}
        for p, pos, m in specs
    ]


def _output_palis(result: dict[str, str | None]) -> list[str]:
    assert result["output_csv"] is not None
    lines = result["output_csv"].strip().splitlines()
    return [line.split("\t")[0] for line in lines[1:]]


def test_second_occurrence_of_a_word_is_dropped(tmp_path: Path) -> None:
    rows = _rows(("buddho", "noun", "first"), ("buddho", "noun", "second"))
    result = _run(tmp_path, rows, links_path="missing")
    assert _output_palis(result) == ["buddho"]
    assert "first" in str(result["output_csv"])
    assert "second" not in str(result["output_csv"])


def test_bold_wrapped_word_is_the_same_key(tmp_path: Path) -> None:
    rows = _rows(
        ("<b>buddho</b>", "noun", "bold first"),
        (" buddho ", "noun", "plain second"),
        ("dhammo", "noun", "other"),
    )
    result = _run(tmp_path, rows, links_path="missing")
    assert _output_palis(result) == ["<b>buddho</b>", "dhammo"]


def test_bold_tags_survive_in_output(tmp_path: Path) -> None:
    rows = _rows(("<b>namo</b> tassa", "ind", "homage"))
    result = _run(tmp_path, rows, links_path="missing")
    assert _output_palis(result) == ["<b>namo</b> tassa"]


def test_first_occurrence_ignores_rows_without_pos(tmp_path: Path) -> None:
    """A word's earlier row with a blank pos (e.g. a sentence line) must not
    use up its first occurrence."""
    rows = _rows(("buddho", "", "sentence line"), ("buddho", "noun", "the Buddha"))
    result = _run(tmp_path, rows, links_path="missing")
    assert _output_palis(result) == ["buddho"]
    assert "the Buddha" in str(result["output_csv"])


def test_first_occurrence_without_meaning_drops_the_word(tmp_path: Path) -> None:
    """The first pos-row decides: its empty meaning is not backfilled from a later row."""
    rows = _rows(("buddho", "noun", ""), ("buddho", "noun", "later meaning"))
    result = _run(tmp_path, rows, links_path="missing")
    assert _output_palis(result) == []
