#!/usr/bin/env python3

"""Test the pure retrospective_exists gate helper in finalize_accepted_sync."""

from pathlib import Path


from kamma.upstream_sync.scripts.finalize_accepted_sync import retrospective_exists


def test_missing_retrospective_returns_false(tmp_path: Path) -> None:
    """A thread dir without retrospective.md returns False."""
    assert retrospective_exists(tmp_path) is False


def test_present_retrospective_returns_true(tmp_path: Path) -> None:
    """A thread dir with retrospective.md present returns True."""
    (tmp_path / "retrospective.md").write_text("# Retrospective\n")
    assert retrospective_exists(tmp_path) is True


def test_accepts_str_path(tmp_path: Path) -> None:
    """retrospective_exists accepts a string path as well as Path."""
    (tmp_path / "retrospective.md").write_text("# Retrospective\n")
    assert retrospective_exists(str(tmp_path)) is True


def test_empty_file_counts_as_present(tmp_path: Path) -> None:
    """An empty retrospective.md still counts as present (gate checks existence only)."""
    (tmp_path / "retrospective.md").write_text("")
    assert retrospective_exists(tmp_path) is True
