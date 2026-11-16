import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from kamma.translate.scripts import batch_runner

from kamma.translate.scripts.batch_runner import (
    build_check_command,
    build_generate_command,
    check_chunk_result,
    default_state,
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


def test_default_state_shape():
    state = default_state()
    assert state == {
        "last_op": None,
        "totals": {"generated": 0, "checked": 0},
    }


def test_build_generate_command_default_passes_no_provider_flags():
    cmd = build_generate_command("meaning", "ru", 50)
    assert "-provider" not in cmd
    assert "-model" not in cmd


def test_build_generate_command_respects_explicit_provider_and_model():
    cmd = build_generate_command("meaning", "ru", 50, "openrouter", "some-model")
    provider_idx = cmd.index("-provider")
    model_idx = cmd.index("-model")
    assert cmd[provider_idx + 1] == "openrouter"
    assert cmd[model_idx + 1] == "some-model"


def test_build_check_command_default_passes_no_provider_flags():
    cmd = build_check_command("meaning", 50)
    assert "--provider" not in cmd
    assert "--model" not in cmd


def test_build_check_command_respects_explicit_provider_and_model():
    cmd = build_check_command("meaning", 50, "openrouter", "some-model")
    assert cmd[cmd.index("--provider") + 1] == "openrouter"
    assert cmd[cmd.index("--model") + 1] == "some-model"


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


def test_check_chunk_result_zero_verdicts_with_exit_zero_is_not_ok():
    output = "Found 50 words to analyze\nAI request failed for x\n" * 1
    attempted, ok = check_chunk_result(output, 0)
    assert attempted == 50
    assert ok == 0


def test_check_chunk_result_uses_checked_line_as_ok():
    attempted, ok = check_chunk_result("Found 50 words to analyze\nchecked 40\n", 0)
    assert (attempted, ok) == (50, 40)


def test_check_chunk_result_nonzero_exit_is_not_ok():
    attempted, ok = check_chunk_result("Found 50 words to analyze\nchecked 40\n", 1)
    assert (attempted, ok) == (50, 0)


def test_check_chunk_result_empty_pool():
    assert check_chunk_result("Found 0 words to analyze\nchecked 0\n", 0) == (0, 0)


# --- main loop: peak gate, session log, exit paths ---


def _setup_runner(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    argv: list[str],
    outputs: list[tuple[str, int]],
) -> dict[str, Any]:
    """Point the runner at tmp files and a scripted subprocess; return call records."""
    monkeypatch.setattr(batch_runner, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(batch_runner, "LOG_PATH", tmp_path / "log.md")
    monkeypatch.setattr(batch_runner, "LAST_TRANSLATED_PATH", tmp_path / "last.json")
    monkeypatch.setattr(batch_runner, "PROCESSED_IDS_PATH", tmp_path / "ids.json")
    monkeypatch.setattr(sys, "argv", ["batch_runner.py", *argv])
    record: dict[str, Any] = {"cmds": [], "gate_calls": 0}

    def fake_run(cmd: list[str]) -> tuple[str, int]:
        record["cmds"].append(cmd)
        return outputs[min(len(record["cmds"]) - 1, len(outputs) - 1)]

    monkeypatch.setattr(batch_runner, "run_subprocess_capture", fake_run)
    return record


def _log_lines(tmp_path: Path) -> list[str]:
    path = tmp_path / "log.md"
    if not path.exists():
        return []
    return [
        ln
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.startswith("- ")
    ]


def test_session_writes_exactly_one_log_line_after_three_chunks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    record = _setup_runner(
        monkeypatch,
        tmp_path,
        ["--op", "check", "--mode", "meaning", "--max-chunks", "3"],
        [("Found 5 words to analyze\nchecked 5\n", 0)],
    )
    monkeypatch.setattr(batch_runner, "require_offpeak", lambda _allow: None)
    with pytest.raises(SystemExit) as exc:
        batch_runner.main()
    assert exc.value.code == 0
    assert len(record["cmds"]) == 3
    lines = _log_lines(tmp_path)
    assert len(lines) == 1
    assert "chunks=3 attempted=15 ok=15 exit=0" in lines[0]


def test_log_line_written_on_exit_2_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    _setup_runner(
        monkeypatch,
        tmp_path,
        ["--op", "check", "--mode", "meaning"],
        [("Found 50 words to analyze\n", 0)],  # no "checked" line -> ok 0
    )
    monkeypatch.setattr(batch_runner, "require_offpeak", lambda _allow: None)
    with pytest.raises(SystemExit) as exc:
        batch_runner.main()
    assert exc.value.code == 2
    lines = _log_lines(tmp_path)
    assert len(lines) == 1 and "attempted=50 ok=0 exit=2" in lines[0]


def test_mid_session_peak_stops_loop_cleanly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    record = _setup_runner(
        monkeypatch,
        tmp_path,
        ["--op", "check", "--mode", "meaning", "--max-chunks", "5"],
        [("Found 5 words to analyze\nchecked 5\n", 0)],
    )
    calls = {"n": 0}

    def gate(_allow: bool) -> None:
        calls["n"] += 1
        if calls["n"] >= 3:  # third chunk would start in peak
            raise SystemExit(1)

    monkeypatch.setattr(batch_runner, "require_offpeak", gate)
    with pytest.raises(SystemExit) as exc:
        batch_runner.main()
    assert exc.value.code == 0
    assert len(record["cmds"]) == 2
    assert len(_log_lines(tmp_path)) == 1


def test_first_chunk_blocked_by_guard_runs_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    record = _setup_runner(
        monkeypatch, tmp_path, ["--op", "check", "--mode", "meaning"], [("", 0)]
    )

    def blocked(_allow: bool) -> None:
        raise SystemExit(1)

    monkeypatch.setattr(batch_runner, "require_offpeak", blocked)
    with pytest.raises(SystemExit) as exc:
        batch_runner.main()
    assert exc.value.code == 1
    assert record["cmds"] == []


def test_allow_peak_flag_is_passed_to_guard(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    _setup_runner(
        monkeypatch,
        tmp_path,
        ["--op", "check", "--mode", "meaning", "--allow-peak"],
        [("Found 0 words to analyze\nchecked 0\n", 0)],
    )
    seen: list[bool] = []
    monkeypatch.setattr(
        batch_runner, "require_offpeak", lambda allow: seen.append(allow)
    )
    with pytest.raises(SystemExit):
        batch_runner.main()
    assert seen == [True]


def test_state_has_no_window_start_after_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    _setup_runner(
        monkeypatch,
        tmp_path,
        ["--op", "check", "--mode", "meaning", "--max-chunks", "1"],
        [("Found 5 words to analyze\nchecked 5\n", 0)],
    )
    (tmp_path / "state.json").write_text(
        json.dumps(
            {
                "window_start": "old",
                "last_op": None,
                "totals": {"generated": 0, "checked": 0},
            }
        )
    )
    monkeypatch.setattr(batch_runner, "require_offpeak", lambda _allow: None)
    with pytest.raises(SystemExit):
        batch_runner.main()
    saved = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert "window_start" not in saved and saved["totals"]["checked"] == 5


def test_runner_source_has_no_antigravity_mention():
    assert (
        "antigravity"
        not in Path(batch_runner.__file__).read_text(encoding="utf-8").lower()
    )


# --- processed_ids.json: reset at generate-session start, merge chunk ids ---


def test_generate_session_resets_stale_ids_then_merges_chunk_ids(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    ids_path = tmp_path / "ids.json"
    ids_path.write_text(json.dumps([99, 98]), encoding="utf-8")  # stale bare list
    _setup_runner(
        monkeypatch,
        tmp_path,
        ["--op", "generate", "--mode", "meaning", "--lang", "ru", "--max-chunks", "1"],
        [("", 0)],
    )
    monkeypatch.setattr(batch_runner, "require_offpeak", lambda _allow: None)

    def fake_generate(cmd: list[str]) -> tuple[str, int]:
        (tmp_path / "last.json").write_text(
            json.dumps({"ids": [5, 3]}), encoding="utf-8"
        )
        return "Rows filtered for the process: 2 / 10\n", 0

    monkeypatch.setattr(batch_runner, "run_subprocess_capture", fake_generate)
    with pytest.raises(SystemExit) as exc:
        batch_runner.main()
    assert exc.value.code == 0
    assert json.loads(ids_path.read_text(encoding="utf-8")) == {
        "lang": "ru",
        "mode": "meaning",
        "ids": [3, 5],
    }


def test_generate_rerun_same_scope_keeps_unverified_ids(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """A re-run after exit 2 / peak stop must not drop ids Op 2 has not checked yet."""
    ids_path = tmp_path / "ids.json"
    ids_path.write_text(
        json.dumps({"lang": "ru", "mode": "meaning", "ids": [7, 8]}), encoding="utf-8"
    )
    _setup_runner(
        monkeypatch,
        tmp_path,
        ["--op", "generate", "--mode", "meaning", "--lang", "ru", "--max-chunks", "1"],
        [("", 0)],
    )
    monkeypatch.setattr(batch_runner, "require_offpeak", lambda _allow: None)

    def fake_generate(cmd: list[str]) -> tuple[str, int]:
        (tmp_path / "last.json").write_text(json.dumps({"ids": [5]}), encoding="utf-8")
        return "Rows filtered for the process: 1 / 10\n", 0

    monkeypatch.setattr(batch_runner, "run_subprocess_capture", fake_generate)
    with pytest.raises(SystemExit):
        batch_runner.main()
    assert json.loads(ids_path.read_text(encoding="utf-8"))["ids"] == [5, 7, 8]


def test_generate_new_scope_resets_ids_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    ids_path = tmp_path / "ids.json"
    ids_path.write_text(
        json.dumps({"lang": "ru", "mode": "lit", "ids": [7, 8]}), encoding="utf-8"
    )
    _setup_runner(
        monkeypatch,
        tmp_path,
        ["--op", "generate", "--mode", "meaning", "--lang", "ru", "--max-chunks", "1"],
        [("", 0)],
    )
    monkeypatch.setattr(batch_runner, "require_offpeak", lambda _allow: None)

    def fake_generate(cmd: list[str]) -> tuple[str, int]:
        (tmp_path / "last.json").write_text(json.dumps({"ids": [5]}), encoding="utf-8")
        return "Rows filtered for the process: 1 / 10\n", 0

    monkeypatch.setattr(batch_runner, "run_subprocess_capture", fake_generate)
    with pytest.raises(SystemExit):
        batch_runner.main()
    assert json.loads(ids_path.read_text(encoding="utf-8")) == {
        "lang": "ru",
        "mode": "meaning",
        "ids": [5],
    }


def test_generate_refused_in_peak_does_not_reset_ids_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    ids_path = tmp_path / "ids.json"
    ids_path.write_text(json.dumps([1, 2]), encoding="utf-8")
    _setup_runner(
        monkeypatch,
        tmp_path,
        ["--op", "generate", "--mode", "meaning"],
        [("", 0)],
    )

    def blocked(_allow: bool) -> None:
        raise SystemExit(1)

    monkeypatch.setattr(batch_runner, "require_offpeak", blocked)
    with pytest.raises(SystemExit):
        batch_runner.main()
    assert json.loads(ids_path.read_text(encoding="utf-8")) == [1, 2]
