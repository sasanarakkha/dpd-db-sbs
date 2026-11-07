"""Golden-master tests for anki_class_grammar duplicate-id detection."""

import pandas as pd

from scripts.work_with_csv.anki_class_grammar import (
    check_duplicate_ids,
    make_feedback_link,
)


def _fixture_sheets() -> dict[str, pd.DataFrame]:
    return {
        "with_dupes": pd.DataFrame({"id": [1, 2, 2, 3], "word": ["a", "b", "c", "d"]}),
        "bad_column_order": pd.DataFrame({"word": ["x"], "id": [1]}),
    }


def test_check_duplicate_ids_flags_repeated_id(capsys) -> None:
    check_duplicate_ids(_fixture_sheets())

    out = capsys.readouterr().out
    assert "2" in out
    assert "does not have an 'id' column as the first column" in out


def test_make_feedback_link_unaffected_by_refactor() -> None:
    link = make_feedback_link("kamma", "06-19")
    assert "entry.438735500=kamma" in link
