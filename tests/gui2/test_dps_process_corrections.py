"""Tests DPS correction review filtering by normalized processed IDs."""

import json
from types import SimpleNamespace

import gui2.dps_process_corrections as process_corrections


def test_main_treats_string_and_integer_processed_ids_as_same(
    tmp_path, monkeypatch, capsys
) -> None:
    corrections_path = tmp_path / "corrections_added.json"
    processed_path = tmp_path / "corrections_processed.json"

    corrections = [
        {
            "id": "45756",
            "lemma_1": "pāraṃ",
            "lemma_1_add": "pāraṃ",
            "meaning_1": "beyond; across; over",
            "meaning_1_add": "beyond; across; over",
            "comment": "",
            "comment_add": "already reviewed under numeric ID",
        },
    ]
    corrections_path.write_text(json.dumps(corrections), encoding="utf-8")
    processed_path.write_text(json.dumps([45756]), encoding="utf-8")

    monkeypatch.setattr(
        process_corrections,
        "DPSPaths",
        lambda: SimpleNamespace(corrections_processed_json_path=processed_path),
    )
    monkeypatch.setattr(
        process_corrections,
        "Gui2Paths",
        lambda: SimpleNamespace(corrections_added_path=corrections_path),
    )
    monkeypatch.setattr("builtins.input", lambda _: "q")

    process_corrections.main()

    output = capsys.readouterr().out
    assert "No new corrections with 'comment_add' to process." in output
    assert "ID: 45756" not in output
