"""Test loading grammar sheets from TSVs in manifest order."""

from pathlib import Path

import pytest

from scripts.work_with_csv.anki_class_grammar import load_grammar_sheets


def _write_fixture(grammar_dir: Path) -> None:
    (grammar_dir / "zeta.tsv").write_text(
        'id\tpali\tnote\n1\tka\t"line one\nline two"\n', encoding="utf-8"
    )
    (grammar_dir / "alpha.tsv").write_text(
        "id\tpali\tnote\n2\tkha\t<i>x</i><br>y\n", encoding="utf-8"
    )
    (grammar_dir / "stray.tsv").write_text("id\tpali\n3\tga\n", encoding="utf-8")
    (grammar_dir / "sheet_order.txt").write_text("zeta\nalpha\n", encoding="utf-8")


def test_load_grammar_sheets_manifest_order_and_values(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    sheets = load_grammar_sheets(tmp_path)

    assert list(sheets) == ["zeta", "alpha"]
    assert sheets["zeta"].loc[0, "note"] == "line one\nline two"
    assert sheets["alpha"].loc[0, "note"] == "<i>x</i><br>y"


def test_load_grammar_sheets_skips_tsv_missing_from_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_fixture(tmp_path)

    sheets = load_grammar_sheets(tmp_path)

    assert "stray" not in sheets
    assert "stray.tsv is not listed in sheet_order.txt" in capsys.readouterr().out


def test_load_grammar_sheets_skips_manifest_entry_without_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_fixture(tmp_path)
    (tmp_path / "sheet_order.txt").write_text("zeta\nghost\nalpha\n", encoding="utf-8")

    sheets = load_grammar_sheets(tmp_path)

    assert list(sheets) == ["zeta", "alpha"]
    assert "ghost is listed in sheet_order.txt but has no TSV file" in (
        capsys.readouterr().out
    )
