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
from kamma.upstream_sync.scripts.sync_runtime import verify_manifest


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


@pytest.mark.parametrize(
    ("payload_update", "expected_error"),
    [
        (
            {"mapped_actions": {"db/models.py": "not-a-list"}},
            "field 'mapped_actions\\['db/models.py'\\]' must be a list",
        ),
        (
            {"mapped_actions": {"db/models.py": ["not-an-object"]}},
            "field 'mapped_actions\\['db/models.py'\\]\\[0\\]' must be a JSON object",
        ),
        (
            {"mapped_actions": {"db/models.py": [{"local_path": "db/models_ru.py"}]}},
            "field 'mapped_actions\\['db/models.py'\\]\\[0\\]': missing required field 'category'",
        ),
        (
            {"mapped_actions": {"db/models.py": [{"category": "russian_copy"}]}},
            "field 'mapped_actions\\['db/models.py'\\]\\[0\\]': missing required field 'local_path'",
        ),
        (
            {
                "mapped_actions": {
                    "db/models.py": [
                        {
                            "category": "russian_copy",
                            "local_path": "db/models_ru.py",
                            "local_target_path": 123,
                        }
                    ]
                }
            },
            "field 'mapped_actions\\['db/models.py'\\]\\[0\\]': field 'local_target_path' must be a string",
        ),
    ],
)
def test_load_prep_manifest_rejects_invalid_mapped_actions(
    tmp_path: Path, payload_update: dict[str, object], expected_error: str
) -> None:
    payload = valid_manifest_payload()
    payload.update(payload_update)
    manifest_path = tmp_path / "prep_manifest.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=expected_error):
        load_prep_manifest(manifest_path)


def test_build_and_write_accepted_sync_state(tmp_path: Path) -> None:
    manifest: dict[str, object] = {
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


def write_manifest(thread_dir: Path, payload: dict[str, object]) -> None:
    (thread_dir / "prep_manifest.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def valid_manifest_payload() -> dict[str, object]:
    return {
        "from_upstream_sha": "oldsha123",
        "to_upstream_sha": "newsha456",
        "target_upstream_ref": "upstream/main",
        "generated_at": "2026-04-08T10:00:00+08:00",
        "changed_upstream_paths": [],
        "deleted_upstream_paths": [],
        "mapped_actions": {},
        "discuss_paths": [],
    }


def test_verify_manifest_rejects_discuss_paths_for_execution(tmp_path: Path) -> None:
    payload = valid_manifest_payload()
    payload["discuss_paths"] = ["db/models.py"]
    write_manifest(tmp_path, payload)

    result = verify_manifest(str(tmp_path), allow_discuss=False)

    assert result == 1


def test_verify_manifest_rejects_accepted_state_mismatch(tmp_path: Path) -> None:
    write_manifest(tmp_path, valid_manifest_payload())

    result = verify_manifest(
        str(tmp_path),
        accepted_sync_state={
            "last_accepted_upstream_sha": "different",
            "last_accepted_upstream_date": "2026-04-08",
            "last_accepted_upstream_ref": "upstream/main",
        },
    )

    assert result == 1


def test_verify_manifest_rejects_target_sha_mismatch(tmp_path: Path) -> None:
    write_manifest(tmp_path, valid_manifest_payload())

    result = verify_manifest(str(tmp_path), target_sha="newer_upstream_sha")

    assert result == 1


def test_verify_manifest_rejects_malformed_accepted_sync_state(tmp_path: Path) -> None:
    write_manifest(tmp_path, valid_manifest_payload())

    result = verify_manifest(
        str(tmp_path),
        accepted_sync_state={
            "last_accepted_upstream_date": "2026-04-08",
            "last_accepted_upstream_ref": "upstream/main",
        },
    )

    assert result == 1
