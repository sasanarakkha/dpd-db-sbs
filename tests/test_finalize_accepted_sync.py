"""Verify accepted sync finalization refuses unsafe prep manifests."""

from pathlib import Path
from unittest.mock import patch

from kamma.upstream_sync.scripts.finalize_accepted_sync import (
    DEFAULT_ACCEPTANCE_NOTES,
    finalize_accepted_sync,
)
from kamma.upstream_sync.scripts.sync_schema import AcceptedSyncState, PrepManifest

FULL_OLD_SHA = "a" * 40
FULL_NEW_SHA = "b" * 40


@patch("kamma.upstream_sync.scripts.finalize_accepted_sync.write_accepted_sync_state")
@patch("kamma.upstream_sync.scripts.finalize_accepted_sync.load_accepted_sync_state")
@patch(
    "kamma.upstream_sync.scripts.finalize_accepted_sync.verify_manifest", return_value=1
)
def test_finalize_rejects_invalid_manifest(
    mock_verify_manifest, mock_load_accepted_state, mock_write_state, tmp_path: Path
) -> None:
    accepted_state = AcceptedSyncState(
        last_accepted_upstream_sha=FULL_OLD_SHA,
        last_accepted_upstream_date="2026-05-02",
        last_accepted_upstream_ref="upstream/main",
    )
    mock_load_accepted_state.return_value = accepted_state

    result = finalize_accepted_sync(
        thread_dir=str(tmp_path),
        state_path=tmp_path / "accepted_sync.json",
        notes="accepted",
    )

    assert result == 1
    mock_verify_manifest.assert_called_once_with(
        str(tmp_path),
        accepted_sync_state=accepted_state,
        allow_discuss=False,
        allow_blockers=False,
    )
    mock_write_state.assert_not_called()


@patch("kamma.upstream_sync.scripts.finalize_accepted_sync.write_accepted_sync_state")
@patch("kamma.upstream_sync.scripts.finalize_accepted_sync.load_accepted_sync_state")
@patch(
    "kamma.upstream_sync.scripts.finalize_accepted_sync.verify_manifest",
    return_value=0,
)
@patch("kamma.upstream_sync.scripts.finalize_accepted_sync.load_prep_manifest")
@patch("kamma.upstream_sync.scripts.finalize_accepted_sync.resolve_commit_date")
def test_finalize_verifies_manifest_against_current_accepted_state(
    mock_resolve_date,
    mock_load_manifest,
    mock_verify_manifest,
    mock_load_accepted_state,
    mock_write_state,
    tmp_path: Path,
) -> None:
    accepted_state = AcceptedSyncState(
        last_accepted_upstream_sha=FULL_OLD_SHA,
        last_accepted_upstream_date="2026-05-02",
        last_accepted_upstream_ref="upstream/main",
    )
    manifest = PrepManifest(
        from_upstream_sha=FULL_OLD_SHA,
        to_upstream_sha=FULL_NEW_SHA,
        target_upstream_ref="upstream/main",
        generated_at="2026-05-31T00:00:00+08:00",
        changed_upstream_paths=[],
        deleted_upstream_paths=[],
        blocker_paths=[],
        discuss_paths=[],
        mapped_actions={},
        needs_classification_paths=[],
    )
    mock_load_accepted_state.return_value = accepted_state
    mock_load_manifest.return_value = manifest
    mock_resolve_date.return_value = "2026-05-31T00:00:00+00:00"

    result = finalize_accepted_sync(
        thread_dir=str(tmp_path),
        state_path=tmp_path / "accepted_sync.json",
        notes="accepted",
    )

    assert result == 0
    mock_verify_manifest.assert_called_once_with(
        str(tmp_path),
        accepted_sync_state=accepted_state,
        allow_discuss=False,
        allow_blockers=False,
    )
    mock_write_state.assert_called_once()
    written_state = mock_write_state.call_args.args[1]
    assert written_state.last_accepted_upstream_sha == FULL_NEW_SHA


def test_default_acceptance_notes_reference_stage_five() -> None:
    assert DEFAULT_ACCEPTANCE_NOTES == "Accepted after Stage 5 verification."
