"""Verify upstream sync docs do not authorize autonomous commits."""

from pathlib import Path


def test_guide_uses_commit_preparation_wording() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    assert "then commit" not in guide
    assert "then prepare the commit message" in guide


def test_guide_has_no_stale_backup_todo_or_grep_command() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    assert "TODO backup dps" not in guide
    assert "grep -r" not in guide
    assert "use `rg`" in guide


def test_guide_keeps_stage_4a_command_execution_with_fast() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    assert (
        "FAST must run `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py "
        "<thread_dir>` before handing off to Stage 4.A."
    ) in guide
    assert (
        "Run `uv run python3 kamma/upstream_sync/scripts/check_docs_parity.py "
        "<thread_dir>`"
    ) not in guide


def test_guide_stops_before_execute_sync_when_discuss_paths_exist() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    assert (
        "If `prep_manifest.json.discuss_paths` is non-empty, STOP before "
        "`execute_sync.py`."
    ) in guide
