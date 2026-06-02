"""Tests DPS addition review filtering by reviewer comments."""

import json
from types import SimpleNamespace

import gui2.dps_process_additions as process_additions


def test_main_shows_unprocessed_entries_with_comment(
    tmp_path, monkeypatch, capsys
) -> None:
    additions_path = tmp_path / "additions_added.json"
    processed_path = tmp_path / "addition_processed.json"

    additions = [
        {
            "id": 1,
            "lemma_1": "comment only",
            "lemma_1_add": "comment only",
            "meaning_1": "meaning",
            "meaning_1_add": "meaning",
            "comment": "review this item",
            "comment_add": "",
        },
        {
            "id": 2,
            "lemma_1": "comment add only",
            "lemma_1_add": "comment add only",
            "meaning_1": "meaning",
            "meaning_1_add": "meaning",
            "comment": "",
            "comment_add": "old filter would show this",
        },
        {
            "id": 3,
            "lemma_1": "processed comment",
            "lemma_1_add": "processed comment",
            "meaning_1": "meaning",
            "meaning_1_add": "meaning",
            "comment": "already processed",
            "comment_add": "",
        },
    ]
    additions_path.write_text(json.dumps(additions), encoding="utf-8")
    processed_path.write_text(json.dumps([3]), encoding="utf-8")

    monkeypatch.setattr(
        process_additions,
        "DPSPaths",
        lambda: SimpleNamespace(addition_processed_json_path=processed_path),
    )
    monkeypatch.setattr(
        process_additions,
        "Gui2Paths",
        lambda: SimpleNamespace(additions_added_path=additions_path),
    )
    monkeypatch.setattr("builtins.input", lambda _: "q")

    process_additions.main()

    output = capsys.readouterr().out
    assert "Total additions with 'comment': 2" in output
    assert "Remaining to process: 1" in output
    assert "ID: 1" in output
    assert "Comment: review this item" in output
    assert "ID: 2" not in output
    assert "ID: 3" not in output
