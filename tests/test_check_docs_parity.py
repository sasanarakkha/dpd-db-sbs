"""Verify docs translation parity reports classify and write expected outputs."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from kamma.upstream_sync.scripts.check_docs_parity import DocsDiffError
from kamma.upstream_sync.scripts.check_docs_parity import find_unexpected_local_files
from kamma.upstream_sync.scripts.check_docs_parity import get_docs_changed_since
from kamma.upstream_sync.scripts.check_docs_parity import load_docs_sync_range
from kamma.upstream_sync.scripts.check_docs_parity import run_parity_check
from kamma.upstream_sync.scripts.check_docs_parity import write_report

FULL_OLD_SHA = "a" * 40
FULL_NEW_SHA = "b" * 40


def write_valid_manifest(thread_dir: Path) -> None:
    """Write a minimal valid prep manifest for docs parity tests."""
    (thread_dir / "prep_manifest.json").write_text(
        json.dumps(
            {
                "from_upstream_sha": FULL_OLD_SHA,
                "to_upstream_sha": FULL_NEW_SHA,
                "target_upstream_ref": "upstream/main",
                "generated_at": "2026-05-31T00:00:00+08:00",
                "changed_upstream_paths": ["docs/example.md"],
                "deleted_upstream_paths": [],
                "mapped_actions": {},
                "discuss_paths": [],
            }
        ),
        encoding="utf-8",
    )


def test_find_unexpected_local_files() -> None:
    unique_local = [
        "dpd_rus.md",
        "technical/dpd_headwords_table_ru.md",
        "technical/untracked_local.md",
    ]

    unexpected = find_unexpected_local_files(unique_local)

    assert unexpected == ["technical/untracked_local.md"]


def test_load_docs_sync_range_uses_thread_manifest(tmp_path: Path) -> None:
    write_valid_manifest(tmp_path)

    from_ref, to_ref = load_docs_sync_range(tmp_path)

    assert from_ref == FULL_OLD_SHA
    assert to_ref == FULL_NEW_SHA


@patch("kamma.upstream_sync.scripts.check_docs_parity.subprocess.run")
def test_get_docs_changed_since_uses_explicit_end_ref(
    mock_run: MagicMock,
) -> None:
    mock_run.return_value.stdout = "docs/example.md\n"

    changed = get_docs_changed_since(FULL_OLD_SHA, FULL_NEW_SHA)

    assert changed == {"example.md"}
    mock_run.assert_called_once()
    assert mock_run.call_args.args[0] == [
        "git",
        "diff",
        "--name-only",
        FULL_OLD_SHA,
        FULL_NEW_SHA,
        "--",
        "docs/",
    ]


@patch("kamma.upstream_sync.scripts.check_docs_parity.subprocess.run")
def test_get_docs_changed_since_strict_mode_raises_on_git_diff_failure(
    mock_run: MagicMock,
) -> None:
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=128,
        cmd=["git", "diff"],
        stderr="bad revision",
    )

    with pytest.raises(DocsDiffError, match="git diff failed"):
        get_docs_changed_since(FULL_OLD_SHA, FULL_NEW_SHA, fail_on_error=True)


@patch("kamma.upstream_sync.scripts.check_docs_parity.write_report")
@patch(
    "kamma.upstream_sync.scripts.check_docs_parity.get_docs_changed_since",
    side_effect=DocsDiffError("git diff failed"),
)
@patch(
    "kamma.upstream_sync.scripts.check_docs_parity.collect_md_files",
    side_effect=[{"example.md"}, {"example.md"}],
)
def test_run_parity_check_strict_mode_fails_when_git_diff_fails(
    mock_collect: MagicMock,
    mock_changed: MagicMock,
    mock_write_report: MagicMock,
    tmp_path: Path,
) -> None:
    write_valid_manifest(tmp_path)

    result = run_parity_check(tmp_path, strict=True)

    assert result == 1
    mock_collect.assert_called()
    mock_changed.assert_called_once_with(FULL_OLD_SHA, FULL_NEW_SHA, fail_on_error=True)
    mock_write_report.assert_not_called()


@patch("kamma.upstream_sync.scripts.check_docs_parity.write_report")
@patch(
    "kamma.upstream_sync.scripts.check_docs_parity.get_docs_changed_since",
    return_value={"example.md"},
)
@patch(
    "kamma.upstream_sync.scripts.check_docs_parity.collect_md_files",
    side_effect=[{"example.md"}, {"example.md"}],
)
def test_run_parity_check_uses_thread_manifest_range(
    mock_collect: MagicMock,
    mock_changed: MagicMock,
    mock_write_report: MagicMock,
    tmp_path: Path,
) -> None:
    write_valid_manifest(tmp_path)

    result = run_parity_check(tmp_path)

    assert result == 0
    mock_collect.assert_called()
    mock_changed.assert_called_once_with(FULL_OLD_SHA, FULL_NEW_SHA)
    assert mock_write_report.call_args.kwargs["to_ref"] == FULL_NEW_SHA


@patch("kamma.upstream_sync.scripts.check_docs_parity.write_report")
@patch(
    "kamma.upstream_sync.scripts.check_docs_parity.get_docs_changed_since",
    return_value={"stale.md"},
)
@patch(
    "kamma.upstream_sync.scripts.check_docs_parity.collect_md_files",
    side_effect=[{"missing.md", "stale.md"}, {"stale.md"}],
)
def test_run_parity_check_default_mode_reports_missing_and_stale_without_failing(
    mock_collect: MagicMock,
    mock_changed: MagicMock,
    mock_write_report: MagicMock,
    tmp_path: Path,
) -> None:
    write_valid_manifest(tmp_path)

    result = run_parity_check(tmp_path)

    assert result == 0
    mock_collect.assert_called()
    mock_changed.assert_called_once_with(FULL_OLD_SHA, FULL_NEW_SHA)
    assert mock_write_report.called


@patch("kamma.upstream_sync.scripts.check_docs_parity.write_report")
@patch(
    "kamma.upstream_sync.scripts.check_docs_parity.get_docs_changed_since",
    return_value={"stale.md"},
)
@patch(
    "kamma.upstream_sync.scripts.check_docs_parity.collect_md_files",
    side_effect=[{"missing.md", "stale.md"}, {"stale.md"}],
)
def test_run_parity_check_strict_mode_fails_on_missing_or_stale_docs(
    mock_collect: MagicMock,
    mock_changed: MagicMock,
    mock_write_report: MagicMock,
    tmp_path: Path,
) -> None:
    write_valid_manifest(tmp_path)

    result = run_parity_check(tmp_path, strict=True)

    assert result == 1
    mock_collect.assert_called()
    mock_changed.assert_called_once_with(FULL_OLD_SHA, FULL_NEW_SHA, fail_on_error=True)
    assert mock_write_report.called


def test_run_parity_check_reports_missing_thread_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = run_parity_check(tmp_path)

    captured = capsys.readouterr()
    assert result == 1
    assert "Manifest not found" in captured.out


def test_write_report_accepts_external_thread_dir(tmp_path: Path) -> None:
    write_report(
        thread_dir=tmp_path,
        sha="abc123",
        missing=[],
        stale=[],
        no_translate=[],
        unique_local=[],
        unexpected_local=[],
    )

    assert (tmp_path / "docs_parity_report.md").exists()


def test_write_report_includes_stale_docs_diff_evidence(tmp_path: Path) -> None:
    with patch(
        "kamma.upstream_sync.scripts.check_docs_parity.get_docs_diff",
        return_value="diff --git a/docs/example.md b/docs/example.md\n+new line\n",
    ):
        write_report(
            thread_dir=tmp_path,
            sha="abc123",
            missing=[],
            stale=["example.md"],
            no_translate=[],
            unique_local=[],
            unexpected_local=[],
        )

    report = (tmp_path / "docs_parity_report.md").read_text(encoding="utf-8")
    assert "### `docs/example.md`" in report
    assert "```diff" in report
    assert "diff --git a/docs/example.md b/docs/example.md" in report
    assert "+new line" in report
