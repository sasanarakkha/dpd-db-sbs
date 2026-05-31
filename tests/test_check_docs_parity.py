"""Verify docs translation parity reports classify and write expected outputs."""

from pathlib import Path

from kamma.upstream_sync.scripts.check_docs_parity import find_unexpected_local_files
from kamma.upstream_sync.scripts.check_docs_parity import write_report


def test_find_unexpected_local_files() -> None:
    unique_local = [
        "dpd_rus.md",
        "technical/dpd_headwords_table_ru.md",
        "technical/untracked_local.md",
    ]

    unexpected = find_unexpected_local_files(unique_local)

    assert unexpected == ["technical/untracked_local.md"]


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
