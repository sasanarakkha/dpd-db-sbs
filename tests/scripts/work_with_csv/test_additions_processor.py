"""Golden-master tests for additions_processor: TSV ID replacement and JSON state tracking."""

import json
from pathlib import Path

from scripts.work_with_csv import additions_processor as mod

FIXTURE_PATH = Path(__file__).parent / "test_additions_processor_fixtures.json"
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


# ── load_additions_data / load_processed_ids / save_processed_ids ──────────


def test_load_additions_data(tmp_path: Path) -> None:
    case = FIXTURES["load_additions_data"]
    additions_json = tmp_path / "additions_added.json"
    additions_json.write_text(
        json.dumps([{"id_add": "82904", "id": 82990}, {"id_add": "100", "id": 200}]),
        encoding="utf-8",
    )
    result = mod.load_additions_data(additions_json)
    assert result == case["output"]


def test_load_processed_ids_existing(tmp_path: Path) -> None:
    case = FIXTURES["load_processed_ids_existing"]
    processed_path = tmp_path / "addition_replaced.json"
    processed_path.write_text(json.dumps(["1", "2"]), encoding="utf-8")
    assert sorted(mod.load_processed_ids(processed_path)) == case["output"]


def test_load_processed_ids_missing_file(tmp_path: Path) -> None:
    case = FIXTURES["load_processed_ids_missing"]
    missing_path = tmp_path / "does_not_exist.json"
    assert sorted(mod.load_processed_ids(missing_path)) == case["output"]


def test_save_processed_ids_merges_with_existing(tmp_path: Path) -> None:
    case = FIXTURES["save_processed_ids_merged"]
    processed_path = tmp_path / "addition_replaced.json"
    processed_path.write_text(json.dumps(["1", "2"]), encoding="utf-8")
    mod.save_processed_ids(processed_path, {"3", "4"})
    saved = json.loads(processed_path.read_text(encoding="utf-8"))
    assert sorted(saved) == case["output"]


# ── replace_ids_in_tsv ──────────────────────────────────────────────────────


def test_replace_ids_in_tsv_missing_file_returns_zero(tmp_path: Path) -> None:
    case = FIXTURES["missing_file"]
    missing_path = tmp_path / "does_not_exist.tsv"
    replacements = mod.replace_ids_in_tsv(missing_path, case["id_mapping"])
    assert replacements == case["replacements"] == 0
    assert not missing_path.exists()


def test_replace_ids_in_tsv_matches_only_first_column(tmp_path: Path) -> None:
    """
    Locks in the bug fix: id_add must only match the first (id) column, not be
    substring-matched against the rest of the line. A row whose free-text column
    happens to contain the same digits as an id_add (e.g. a sutta reference like
    "DHP408" colliding with id_add "408") must NOT be touched.

    Old (buggy) behaviour for this exact input is recorded in
    FIXTURES["normal_match_and_collision_bait_OLD_BEHAVIOR"]["output_tsv"], where
    "DHP408" was corrupted into "DHP12345". This test asserts the new, intended
    behaviour instead.
    """
    case = FIXTURES["normal_match_and_collision_bait_OLD_BEHAVIOR"]
    tsv_path = tmp_path / "sample.tsv"
    tsv_path.write_text(case["input_tsv"], encoding="utf-8")

    replacements = mod.replace_ids_in_tsv(tsv_path, case["id_mapping"])

    output = tsv_path.read_text(encoding="utf-8")
    assert replacements == 1  # only the genuine id-column match, not the bait
    assert '"99990"' in output  # id "7" in the id column was replaced
    assert "DHP408" in output  # collision bait left untouched
    assert "DHP12345" not in output  # old buggy output must not reappear
