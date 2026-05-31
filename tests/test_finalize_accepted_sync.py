"""Verify accepted sync finalization refuses unsafe prep manifests."""

from pathlib import Path
from unittest.mock import patch

from kamma.upstream_sync.scripts.finalize_accepted_sync import finalize_accepted_sync


@patch("kamma.upstream_sync.scripts.finalize_accepted_sync.write_accepted_sync_state")
@patch(
    "kamma.upstream_sync.scripts.finalize_accepted_sync.verify_manifest", return_value=1
)
def test_finalize_rejects_invalid_manifest(
    mock_verify_manifest, mock_write_state, tmp_path: Path
) -> None:
    result = finalize_accepted_sync(
        thread_dir=str(tmp_path),
        state_path=tmp_path / "accepted_sync.json",
        notes="accepted",
    )

    assert result == 1
    mock_verify_manifest.assert_called_once_with(str(tmp_path), allow_discuss=False)
    mock_write_state.assert_not_called()
