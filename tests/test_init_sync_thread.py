"""Verify upstream sync thread initialization writes restartable metadata."""

import json
from pathlib import Path
from unittest.mock import patch

from kamma.upstream_sync.scripts import init_sync_thread

FULL_OLD_SHA = "a" * 40


def test_init_sync_thread_autofills_accepted_sync_metadata(tmp_path: Path) -> None:
    state_path = tmp_path / "accepted_sync.json"
    state_path.write_text(
        json.dumps(
            {
                "last_accepted_upstream_sha": FULL_OLD_SHA,
                "last_accepted_upstream_date": "2026-05-02",
                "last_accepted_upstream_ref": "upstream/main",
            }
        ),
        encoding="utf-8",
    )
    threads_dir = tmp_path / "threads"

    with (
        patch.object(init_sync_thread, "THREADS_DIR", threads_dir),
        patch.object(init_sync_thread, "ACCEPTED_SYNC_PATH", state_path),
    ):
        init_sync_thread.main()

    thread_dir = next(threads_dir.iterdir())
    spec = (thread_dir / "spec.md").read_text(encoding="utf-8")
    handoff = (thread_dir / "handoff.md").read_text(encoding="utf-8")

    assert f"- **From**: `{FULL_OLD_SHA}`" in spec
    assert "- **Commit / tag**: `aaaaaaaaaaaa`" in handoff
    assert "- **Date**: `2026-05-02`" in handoff
    assert "- **Ref**: `upstream/main`" in handoff
    assert "## Errors, Issues, And Repeated Mistakes" in handoff
