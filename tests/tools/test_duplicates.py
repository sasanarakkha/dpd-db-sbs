"""Golden-master tests for tools/duplicates.has_duplicate_values_in_column."""

import pytest

from tools.duplicates import has_duplicate_values_in_column


def test_duplicates_found_by_column_name(tmp_path):
    tsv_path = tmp_path / "f1.tsv"
    tsv_path.write_text("id\tname\n1\ta\n2\tb\n1\tc\n3\td\n2\te\n", encoding="utf-8")

    has_dupes, dupe_values, dupe_lines = has_duplicate_values_in_column(
        tsv_path=tsv_path, column_name="id"
    )

    assert has_dupes is True
    assert dupe_values == ["1", "2"]
    assert dupe_lines == {"1": [2, 4], "2": [3, 6]}


def test_no_duplicates_by_column_index(tmp_path):
    tsv_path = tmp_path / "f2.tsv"
    tsv_path.write_text("id\tname\n1\ta\n2\tb\n3\tc\n", encoding="utf-8")

    has_dupes, dupe_values, dupe_lines = has_duplicate_values_in_column(
        tsv_path=tsv_path, column_index=1
    )

    assert has_dupes is False
    assert dupe_values == []
    assert dupe_lines == {}


def test_empty_file_returns_no_duplicates(tmp_path):
    tsv_path = tmp_path / "f3.tsv"
    tsv_path.write_text("", encoding="utf-8")

    result = has_duplicate_values_in_column(tsv_path=tsv_path)

    assert result == (False, [], {})


def test_short_rows_are_skipped(tmp_path):
    tsv_path = tmp_path / "f4.tsv"
    tsv_path.write_text("id\tname\n1\ta\n\n1\n2\tb\n", encoding="utf-8")

    has_dupes, dupe_values, dupe_lines = has_duplicate_values_in_column(
        tsv_path=tsv_path, column_name="id"
    )

    assert has_dupes is True
    assert dupe_values == ["1"]
    assert dupe_lines == {"1": [2, 4]}


def test_unknown_column_name_raises_value_error(tmp_path):
    tsv_path = tmp_path / "f5.tsv"
    tsv_path.write_text("id\tname\n1\ta\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Column name 'nope' not found"):
        has_duplicate_values_in_column(tsv_path=tsv_path, column_name="nope")


def test_out_of_bounds_column_index_raises_value_error(tmp_path):
    tsv_path = tmp_path / "f5.tsv"
    tsv_path.write_text("id\tname\n1\ta\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Column index 99 is out of bounds"):
        has_duplicate_values_in_column(tsv_path=tsv_path, column_index=99)


def test_missing_file_raises_file_not_found_error(tmp_path):
    tsv_path = tmp_path / "nope.tsv"

    with pytest.raises(FileNotFoundError, match="TSV file not found"):
        has_duplicate_values_in_column(tsv_path=tsv_path)
