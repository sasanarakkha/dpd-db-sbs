"""Verify read_line_list strips blank/#-comment lines but preserves other content verbatim."""

from pathlib import Path

from kamma.upstream_sync.scripts.registry_helper import read_line_list


def test_read_line_list_missing_file_returns_empty(tmp_path: Path) -> None:
    result = read_line_list(tmp_path / "missing.txt")

    assert result == []


def test_read_line_list_skips_blanks_and_comments(tmp_path: Path) -> None:
    path = tmp_path / "lines.txt"
    path.write_text(
        "path/one.py\n\n# a comment\n   # indented comment\npath/two.py\n   \n",
        encoding="utf-8",
    )

    result = read_line_list(path)

    assert result == ["path/one.py", "path/two.py"]


def test_read_line_list_preserves_surrounding_whitespace_on_kept_lines(
    tmp_path: Path,
) -> None:
    path = tmp_path / "lines.txt"
    path.write_text("  path/padded.py  \n", encoding="utf-8")

    result = read_line_list(path)

    assert result == ["  path/padded.py  "]
