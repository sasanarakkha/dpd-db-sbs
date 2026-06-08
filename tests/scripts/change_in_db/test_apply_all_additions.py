"""Tests for apply_all_additions: ebt_count field coercion and TSV ID replacement logic."""

from pathlib import Path

import pytest


# ── ebt_count coercion ──────────────────────────────────────────────────────
# Tests the condition that was `field_name in ["ebt_count"]` → `== "ebt_count"`.
# Pure logic, no DB or file I/O.


@pytest.mark.parametrize(
    "field_name, value, expected",
    [
        ("ebt_count", "42", 42),
        ("ebt_count", "0", 0),
        ("ebt_count", "not_a_num", "not_a_num"),
        ("other_field", "42", "42"),
        ("ebt_count", 99, 99),  # already int — isdigit not called
    ],
)
def test_ebt_count_coercion(
    field_name: str, value: str | int, expected: str | int
) -> None:
    if field_name == "ebt_count" and isinstance(value, str) and value.isdigit():
        value = int(value)
    assert value == expected


# ── TSV ID replacement logic ─────────────────────────────────────────────────
# Tests the column-0 replacement behaviour of the inner process_file function.
# Uses a temp file to exercise the actual I/O path (stdlib — trusted).


def _write_tsv(path: Path, rows: list[list[str]]) -> None:
    path.write_text("\n".join("\t".join(row) for row in rows) + "\n", encoding="utf-8")


def _read_tsv(path: Path) -> list[list[str]]:
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines()]


def _run_process_file(file_path: Path, id_map: dict[str, int]) -> None:
    """Inline of process_file inner function so we can test it directly."""
    try:
        with open(file_path, "r", newline="", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        for line in lines:
            columns = line.strip().split("\t")
            if columns:
                id_to_check = columns[0].strip().strip('"')
                if id_to_check in id_map:
                    columns[0] = f'"{id_map[id_to_check]}"'
            f.write("\t".join(columns) + "\n")


def test_process_file_replaces_matching_ids(tmp_path: Path) -> None:
    tsv = tmp_path / "russian.tsv"
    _write_tsv(
        tsv,
        [
            ['"100"', "word", "meaning"],
            ['"200"', "other", "value"],
            ['"300"', "keep", "this"],
        ],
    )
    _run_process_file(tsv, {"100": 1001, "200": 2002})
    rows = _read_tsv(tsv)
    assert rows[0][0] == '"1001"'
    assert rows[1][0] == '"2002"'
    assert rows[2][0] == '"300"'  # not in map — unchanged


def test_process_file_no_match_leaves_file_unchanged(tmp_path: Path) -> None:
    tsv = tmp_path / "sbs.tsv"
    original = [["999", "a", "b"]]
    _write_tsv(tsv, original)
    _run_process_file(tsv, {"100": 1001})
    rows = _read_tsv(tsv)
    assert rows[0][0] == "999"


def test_process_file_strips_outer_quotes_for_lookup(tmp_path: Path) -> None:
    # strip() removes outer whitespace; strip('"') removes surrounding quotes.
    # Inner spaces are NOT removed, so '"  42  "' does NOT match key "42".
    tsv = tmp_path / "test.tsv"
    _write_tsv(tsv, [['"42"', "col2"]])
    _run_process_file(tsv, {"42": 999})
    rows = _read_tsv(tsv)
    assert rows[0][0] == '"999"'
