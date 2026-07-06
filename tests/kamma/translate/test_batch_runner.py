import json
from datetime import datetime, timedelta

from kamma.translate.scripts.batch_runner import (
    default_state,
    detect_quota_exhaustion,
    merge_processed_ids,
    parse_check_attempted,
    parse_generate_counts,
    read_generated_ids,
)


def test_parse_generate_counts_extracts_attempted_and_total():
    output = "Current filter: meaning\nRows filtered for the process: 12 / 3456\n"
    assert parse_generate_counts(output) == (12, 3456)


def test_parse_generate_counts_no_match_returns_none():
    assert parse_generate_counts("nothing relevant here") is None


def test_parse_check_attempted_extracts_count():
    output = "Some banner\nFound 42 words to analyze\nmore output\n"
    assert parse_check_attempted(output) == 42


def test_parse_check_attempted_no_match_returns_none():
    assert parse_check_attempted("nothing relevant here") is None


def test_detect_quota_exhaustion_true_on_marker():
    output = "AIManager error: request failed (possible quota exhaustion)"
    assert detect_quota_exhaustion(output) is True


def test_detect_quota_exhaustion_false_without_marker():
    assert detect_quota_exhaustion("request failed: rate limited") is False


def test_default_state_shape():
    state = default_state()
    assert state == {
        "window_start": None,
        "quota_exhausted_at": None,
        "resume_at": None,
        "last_op": None,
        "totals": {"generated": 0, "checked": 0},
        "note": "resume_at assumes a conservative 5h wait after quota exhaustion",
    }


def test_merge_processed_ids_missing_file_returns_sorted_new_ids(tmp_path):
    path = tmp_path / "processed_ids.json"
    assert merge_processed_ids(path, [3, 1, 2]) == [1, 2, 3]


def test_merge_processed_ids_unions_existing_and_new(tmp_path):
    path = tmp_path / "processed_ids.json"
    path.write_text(json.dumps([1, 2, 5]), encoding="utf-8")
    assert merge_processed_ids(path, [2, 3]) == [1, 2, 3, 5]


def test_merge_processed_ids_tolerates_malformed_existing_file(tmp_path):
    path = tmp_path / "processed_ids.json"
    path.write_text("not valid json", encoding="utf-8")
    assert merge_processed_ids(path, [7, 8]) == [7, 8]


def test_merge_processed_ids_tolerates_non_list_existing_content(tmp_path):
    path = tmp_path / "processed_ids.json"
    path.write_text(json.dumps({"unexpected": "shape"}), encoding="utf-8")
    assert merge_processed_ids(path, [4]) == [4]


def test_read_generated_ids_missing_file_returns_empty(tmp_path):
    path = tmp_path / "last_translated.json"
    since = datetime.now().astimezone() - timedelta(minutes=1)
    assert read_generated_ids(path, since) == []


def test_read_generated_ids_fresh_file_returns_ids(tmp_path):
    path = tmp_path / "last_translated.json"
    since = datetime.now().astimezone() - timedelta(minutes=1)
    path.write_text(json.dumps({"lang": "ru", "ids": [3, 1, 2]}), encoding="utf-8")
    assert read_generated_ids(path, since) == [3, 1, 2]


def test_read_generated_ids_stale_file_returns_empty(tmp_path):
    path = tmp_path / "last_translated.json"
    path.write_text(json.dumps({"lang": "ru", "ids": [1, 2]}), encoding="utf-8")
    since = datetime.now().astimezone() + timedelta(minutes=1)
    assert read_generated_ids(path, since) == []


def test_read_generated_ids_malformed_file_returns_empty(tmp_path):
    path = tmp_path / "last_translated.json"
    path.write_text("not valid json", encoding="utf-8")
    since = datetime.now().astimezone() - timedelta(minutes=1)
    assert read_generated_ids(path, since) == []
