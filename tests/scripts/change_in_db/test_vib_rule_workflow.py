"""Tests for pure utility functions in vib_rule_workflow.py."""

import io

from scripts.change_in_db.vib_rule_workflow import (
    collect_tty_pasted_text,
    normalize_pat_file,
    strip_variant_readings,
    suggest_next_pat_file,
    suggest_next_source,
)


# --- suggest_next_pat_file ---


def test_suggest_next_pat_file_increments() -> None:
    assert suggest_next_pat_file("misc/pat/pc64.txt") == "misc/pat/pc65.txt"


def test_suggest_next_pat_file_different_prefix() -> None:
    assert suggest_next_pat_file("misc/pat/vib10.txt") == "misc/pat/vib11.txt"


def test_suggest_next_pat_file_no_digits_returns_empty() -> None:
    assert suggest_next_pat_file("misc/pat/pc.txt") == ""


def test_suggest_next_pat_file_bare_filename() -> None:
    assert suggest_next_pat_file("pc64.txt") == "misc/pat/pc65.txt"


# --- suggest_next_source ---


def test_suggest_next_source_increments_last_segment() -> None:
    assert suggest_next_source("VIN2.5.6.10") == "VIN2.5.6.11"


def test_suggest_next_source_single_level() -> None:
    assert suggest_next_source("VIN2.5") == "VIN2.6"


def test_suggest_next_source_no_trailing_number_returns_empty() -> None:
    assert suggest_next_source("VIN2") == ""


def test_suggest_next_source_no_dot_returns_empty() -> None:
    assert suggest_next_source("VIN25") == ""


# --- normalize_pat_file ---


def test_normalize_pat_file_bare_stem_expands() -> None:
    assert normalize_pat_file("pc64") == "misc/pat/pc64.txt"


def test_normalize_pat_file_full_path_unchanged() -> None:
    assert normalize_pat_file("misc/pat/pc64.txt") == "misc/pat/pc64.txt"


def test_normalize_pat_file_partial_path_unchanged() -> None:
    assert normalize_pat_file("misc/pc64.txt") == "misc/pc64.txt"


def test_normalize_pat_file_with_extension_but_no_slash() -> None:
    assert normalize_pat_file("pc64.txt") == "pc64.txt"


# --- strip_variant_readings ---


def test_strip_variant_readings_removes_single_brace_group() -> None:
    assert strip_variant_readings("some {variant} text") == "some  text"


def test_strip_variant_readings_removes_multiple_brace_groups() -> None:
    assert strip_variant_readings("{a} text {b}") == "text"


def test_strip_variant_readings_no_variants_unchanged() -> None:
    assert strip_variant_readings("clean text") == "clean text"


def test_strip_variant_readings_strips_outer_whitespace() -> None:
    assert strip_variant_readings("  hello  ") == "hello"


def test_strip_variant_readings_empty_string() -> None:
    assert strip_variant_readings("") == ""


# --- collect_tty_pasted_text ---


def test_collect_tty_pasted_text_eof_terminates() -> None:
    stream = io.StringIO("line one\nline two\n")
    result = collect_tty_pasted_text(stream)
    assert result == "line one\nline two\n"


def test_collect_tty_pasted_text_sentinel_terminates() -> None:
    stream = io.StringIO("line one\n__END__\nignored\n")
    result = collect_tty_pasted_text(stream)
    assert result == "line one\n"


def test_collect_tty_pasted_text_empty_input() -> None:
    stream = io.StringIO("")
    result = collect_tty_pasted_text(stream)
    assert result == ""
