import json
from pathlib import Path

from scripts.other.add_combined_view import _VIEW_COLUMNS, _build_select_clause

FIXTURE_PATH = Path(__file__).parent / "test_add_combined_view_fixtures.json"


def test_view_columns_match_original_sql() -> None:
    expected = [
        tuple(row) for row in json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    ]
    assert _VIEW_COLUMNS == expected


def test_select_clause_contains_every_column_in_order() -> None:
    clause = _build_select_clause(_VIEW_COLUMNS)
    fragments = [
        f"COALESCE({table}.{column}, '') AS {alias}"
        for table, column, alias in _VIEW_COLUMNS
    ]
    positions = [clause.index(fragment) for fragment in fragments]
    assert positions == sorted(positions)


def test_select_clause_has_no_duplicate_aliases() -> None:
    aliases = [alias for _, _, alias in _VIEW_COLUMNS]
    assert len(aliases) == len(set(aliases))
