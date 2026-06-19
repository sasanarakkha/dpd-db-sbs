"""Golden-master tests for anki_class_grammar duplicate-id detection."""

from pathlib import Path

import pandas as pd

from scripts.work_with_csv.anki_class_grammar import (
    check_duplicate_ids,
    make_feedback_link,
)


def _write_fixture_xlsx(path: Path) -> None:
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"id": [1, 2, 2, 3], "word": ["a", "b", "c", "d"]}).to_excel(
            writer, sheet_name="with_dupes", index=False
        )
        pd.DataFrame({"word": ["x"], "id": [1]}).to_excel(
            writer, sheet_name="bad_column_order", index=False
        )


def test_check_duplicate_ids_flags_repeated_id(tmp_path: Path, capsys) -> None:
    fixture_path = tmp_path / "grammar.xlsx"
    _write_fixture_xlsx(fixture_path)

    check_duplicate_ids(fixture_path)

    out = capsys.readouterr().out
    assert "2" in out
    assert "does not have an 'id' column as the first column" in out


def test_make_feedback_link_unaffected_by_refactor() -> None:
    link = make_feedback_link("kamma", "06-19")
    assert "entry.438735500=kamma" in link
