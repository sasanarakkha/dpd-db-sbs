"""Tests for sbs_anki_fields_check parsing and comparison logic."""

from pathlib import Path

import pytest

from scripts.export.sbs_anki_fields_check import compare_fields, parse_field_list_md


@pytest.fixture()
def tmp_md(tmp_path: Path):
    def _make(content: str) -> Path:
        p = tmp_path / "field-list.md"
        p.write_text(content, encoding="utf-8")
        return p

    return _make


def test_parse_field_list_md_valid(tmp_md):
    p = tmp_md("# Title\n\n```\nfoo\nbar\nbaz\n```\n")
    assert parse_field_list_md(p) == ["foo", "bar", "baz"]


def test_parse_field_list_md_missing_file(tmp_path: Path):
    result = parse_field_list_md(tmp_path / "nonexistent.md")
    assert result == []


def test_parse_field_list_md_no_fenced_block(tmp_md):
    p = tmp_md("# Title\n\nNo code block here.\n")
    assert parse_field_list_md(p) == []


def test_compare_fields_identical():
    fields = ["a", "b", "c"]
    only_anki, only_file, order = compare_fields(fields, fields)
    assert only_anki == []
    assert only_file == []
    assert order is False


def test_compare_fields_extra_in_anki():
    only_anki, only_file, order = compare_fields(["a", "b", "c"], ["a", "b"])
    assert only_anki == ["c"]
    assert only_file == []
    assert order is False


def test_compare_fields_extra_in_file():
    only_anki, only_file, order = compare_fields(["a", "b"], ["a", "b", "c"])
    assert only_anki == []
    assert only_file == ["c"]
    assert order is False


def test_compare_fields_order_differs():
    only_anki, only_file, order = compare_fields(["a", "b", "c"], ["c", "a", "b"])
    assert only_anki == []
    assert only_file == []
    assert order is True
