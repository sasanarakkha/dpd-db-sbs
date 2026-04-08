"""Verify upstream sync state and prep manifest metadata are validated consistently."""

import json
from pathlib import Path

import pytest

from kamma.upstream_sync.scripts.registry_helper import (
    build_accepted_sync_state,
    load_accepted_sync_state,
    load_prep_manifest,
    write_accepted_sync_state,
)


def test_load_accepted_sync_state_valid(tmp_path: Path) -> None:
    state_path = tmp_path / "accepted_sync.json"
    state_path.write_text(
        json.dumps(
            {
                "last_accepted_upstream_sha": "abc123def456",
                "last_accepted_upstream_date": "2026-04-08",
                "last_accepted_upstream_ref": "upstream/main",
                "notes": "baseline",
            }
        ),
        encoding="utf-8",
    )

    state = load_accepted_sync_state(state_path)

    assert state["last_accepted_upstream_sha"] == "abc123def456"
    assert state["last_accepted_upstream_ref"] == "upstream/main"


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        ({}, "missing required field 'last_accepted_upstream_sha'"),
        (
            {
                "last_accepted_upstream_sha": "abc123",
                "last_accepted_upstream_date": "2026-04-08",
            },
            "missing required field 'last_accepted_upstream_ref'",
        ),
        (
            {
                "last_accepted_upstream_sha": "",
                "last_accepted_upstream_date": "2026-04-08",
                "last_accepted_upstream_ref": "upstream/main",
            },
            "field 'last_accepted_upstream_sha' must be a non-empty string",
        ),
        (
            {
                "last_accepted_upstream_sha": "abc123",
                "last_accepted_upstream_date": 20260408,
                "last_accepted_upstream_ref": "upstream/main",
            },
            "field 'last_accepted_upstream_date' must be a string",
        ),
    ],
)
def test_load_accepted_sync_state_invalid(
    tmp_path: Path, payload: dict[str, object], expected_error: str
) -> None:
    state_path = tmp_path / "accepted_sync.json"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=expected_error):
        load_accepted_sync_state(state_path)


def test_load_accepted_sync_state_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_accepted_sync_state(tmp_path / "accepted_sync.json")


def test_load_prep_manifest_valid(tmp_path: Path) -> None:
    manifest_path = tmp_path / "prep_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "from_upstream_sha": "oldsha123",
                "to_upstream_sha": "newsha456",
                "target_upstream_ref": "upstream/main",
                "generated_at": "2026-04-08T10:00:00+08:00",
                "changed_upstream_paths": ["db/models.py"],
                "deleted_upstream_paths": [],
                "mapped_actions": {"db/models.py": []},
                "discuss_paths": ["db/models.py"],
            }
        ),
        encoding="utf-8",
    )

    manifest = load_prep_manifest(manifest_path)

    assert manifest["to_upstream_sha"] == "newsha456"
    assert manifest["target_upstream_ref"] == "upstream/main"


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        ({}, "missing required field 'from_upstream_sha'"),
        (
            {
                "from_upstream_sha": "oldsha123",
                "to_upstream_sha": "newsha456",
                "target_upstream_ref": "upstream/main",
                "generated_at": "2026-04-08",
                "changed_upstream_paths": "db/models.py",
                "deleted_upstream_paths": [],
                "mapped_actions": {},
                "discuss_paths": [],
            },
            "field 'changed_upstream_paths' must be a list",
        ),
        (
            {
                "from_upstream_sha": "oldsha123",
                "to_upstream_sha": "",
                "target_upstream_ref": "upstream/main",
                "generated_at": "2026-04-08",
                "changed_upstream_paths": [],
                "deleted_upstream_paths": [],
                "mapped_actions": {},
                "discuss_paths": [],
            },
            "field 'to_upstream_sha' must be a non-empty string",
        ),
    ],
)
def test_load_prep_manifest_invalid(
    tmp_path: Path, payload: dict[str, object], expected_error: str
) -> None:
    manifest_path = tmp_path / "prep_manifest.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=expected_error):
        load_prep_manifest(manifest_path)


def test_build_and_write_accepted_sync_state(tmp_path: Path) -> None:
    manifest = {
        "from_upstream_sha": "oldsha123",
        "to_upstream_sha": "newsha456",
        "target_upstream_ref": "upstream/main",
        "generated_at": "2026-04-08T10:00:00+08:00",
        "changed_upstream_paths": [],
        "deleted_upstream_paths": [],
        "mapped_actions": {},
        "discuss_paths": [],
    }

    state = build_accepted_sync_state(
        manifest=manifest,
        upstream_commit_date="2026-04-09T12:00:00+08:00",
        notes="accepted after verification",
    )

    state_path = tmp_path / "accepted_sync.json"
    write_accepted_sync_state(state_path, state)

    written = load_accepted_sync_state(state_path)
    assert written["last_accepted_upstream_sha"] == "newsha456"
    assert written["last_accepted_upstream_date"] == "2026-04-09T12:00:00+08:00"
    assert written["last_accepted_upstream_ref"] == "upstream/main"
