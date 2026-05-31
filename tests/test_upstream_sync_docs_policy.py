"""Verify upstream sync docs do not authorize autonomous commits."""

from pathlib import Path


def test_guide_uses_commit_preparation_wording() -> None:
    guide = Path("kamma/upstream_sync/guide.md").read_text(encoding="utf-8")

    assert "then commit" not in guide
    assert "then prepare the commit message" in guide
