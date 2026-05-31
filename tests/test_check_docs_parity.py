"""Verify docs translation parity classification catches unexpected local files."""

from kamma.upstream_sync.scripts.check_docs_parity import find_unexpected_local_files


def test_find_unexpected_local_files() -> None:
    unique_local = [
        "dpd_rus.md",
        "technical/dpd_headwords_table_ru.md",
        "technical/untracked_local.md",
    ]

    unexpected = find_unexpected_local_files(unique_local)

    assert unexpected == ["technical/untracked_local.md"]
