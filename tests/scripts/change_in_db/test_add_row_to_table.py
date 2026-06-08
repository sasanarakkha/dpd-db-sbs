"""Tests for add_row_to_table column validation logic."""

from sqlalchemy import inspect as sa_inspect

from db.models import SBS


def test_sbs_column_attrs_contains_valid_column() -> None:
    valid_columns = {attr.key for attr in sa_inspect(SBS).column_attrs}
    assert "class_anki" in valid_columns


def test_sbs_column_attrs_excludes_nonexistent() -> None:
    valid_columns = {attr.key for attr in sa_inspect(SBS).column_attrs}
    assert "nonexistent_column_xyz" not in valid_columns
