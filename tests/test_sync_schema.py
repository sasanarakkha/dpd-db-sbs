"""Verify typed upstream sync metadata schema parsing and validation."""

import pytest
from collections.abc import Callable

from kamma.upstream_sync.scripts.sync_schema import (
    AcceptedSyncState,
    MappedAction,
    PrepManifest,
    RegistryData,
)


def test_accepted_sync_state_from_raw_valid_with_notes() -> None:
    state = AcceptedSyncState.from_raw(
        {
            "last_accepted_upstream_sha": "abc123",
            "last_accepted_upstream_date": "2026-05-31T12:00:00+08:00",
            "last_accepted_upstream_ref": "upstream/main",
            "notes": "verified baseline",
        }
    )

    assert state.last_accepted_upstream_sha == "abc123"
    assert state.last_accepted_upstream_date == "2026-05-31T12:00:00+08:00"
    assert state.last_accepted_upstream_ref == "upstream/main"
    assert state.notes == "verified baseline"
    assert state.to_json() == {
        "last_accepted_upstream_sha": "abc123",
        "last_accepted_upstream_date": "2026-05-31T12:00:00+08:00",
        "last_accepted_upstream_ref": "upstream/main",
        "notes": "verified baseline",
    }


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        ({}, "missing required field 'last_accepted_upstream_sha'"),
        (
            {
                "last_accepted_upstream_date": "2026-05-31T12:00:00+08:00",
                "last_accepted_upstream_ref": "upstream/main",
            },
            "missing required field 'last_accepted_upstream_sha'",
        ),
        (
            {
                "last_accepted_upstream_sha": "abc123",
                "last_accepted_upstream_date": 20260531,
                "last_accepted_upstream_ref": "upstream/main",
            },
            "field 'last_accepted_upstream_date' must be a string",
        ),
        (
            {
                "last_accepted_upstream_sha": "abc123",
                "last_accepted_upstream_date": "2026-05-31T12:00:00+08:00",
                "last_accepted_upstream_ref": " ",
            },
            "field 'last_accepted_upstream_ref' must be a non-empty string",
        ),
        (
            {
                "last_accepted_upstream_sha": "abc123",
                "last_accepted_upstream_date": "2026-05-31T12:00:00+08:00",
                "last_accepted_upstream_ref": "upstream/main",
                "notes": ["not", "a", "string"],
            },
            "field 'notes' must be a string",
        ),
    ],
)
def test_accepted_sync_state_from_raw_rejects_invalid_payload(
    payload: object, expected_error: str
) -> None:
    with pytest.raises(ValueError, match=expected_error):
        AcceptedSyncState.from_raw(payload)


def test_mapped_action_from_raw_valid_with_local_target_path() -> None:
    action = MappedAction.from_raw(
        {
            "category": "russian_copy",
            "local_path": "db/models_ru.py",
            "local_target_path": "db/models_ru.py",
        }
    )

    assert action.category == "russian_copy"
    assert action.local_path == "db/models_ru.py"
    assert action.local_target_path == "db/models_ru.py"
    assert action.to_json() == {
        "category": "russian_copy",
        "local_path": "db/models_ru.py",
        "local_target_path": "db/models_ru.py",
    }


def test_mapped_action_from_raw_accepts_backward_compatible_payload() -> None:
    action = MappedAction.from_raw(
        {
            "category": "russian_copy",
            "local_path": "db/models_ru.py",
        }
    )

    assert action.category == "russian_copy"
    assert action.local_path == "db/models_ru.py"
    assert action.local_target_path is None
    assert action.to_json() == {
        "category": "russian_copy",
        "local_path": "db/models_ru.py",
    }


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        ({"local_path": "db/models_ru.py"}, "missing required field 'category'"),
        (
            {"category": "russian_copy", "local_path": " "},
            "field 'local_path' must be a non-empty string",
        ),
        (
            {
                "category": "russian_copy",
                "local_path": "db/models_ru.py",
                "local_target_path": 123,
            },
            "field 'local_target_path' must be a string",
        ),
    ],
)
def test_mapped_action_from_raw_rejects_invalid_payload(
    payload: object, expected_error: str
) -> None:
    with pytest.raises(ValueError, match=expected_error):
        MappedAction.from_raw(payload)


def valid_manifest_payload() -> dict[str, object]:
    return {
        "from_upstream_sha": "oldsha",
        "to_upstream_sha": "newsha",
        "target_upstream_ref": "upstream/main",
        "generated_at": "2026-05-31T12:00:00+08:00",
        "changed_upstream_paths": ["db/models.py"],
        "deleted_upstream_paths": ["old.py"],
        "blocker_paths": ["new_unmapped.py"],
        "discuss_paths": ["db/models.py"],
        "mapped_actions": {
            "db/models.py": [
                {
                    "category": "russian_copy",
                    "local_path": "db/models_ru.py",
                    "local_target_path": "db/models_ru.py",
                }
            ]
        },
    }


def test_prep_manifest_from_raw_valid_with_current_fields() -> None:
    manifest = PrepManifest.from_raw(valid_manifest_payload())

    assert manifest.from_upstream_sha == "oldsha"
    assert manifest.to_upstream_sha == "newsha"
    assert manifest.target_upstream_ref == "upstream/main"
    assert manifest.changed_upstream_paths == ["db/models.py"]
    assert manifest.deleted_upstream_paths == ["old.py"]
    assert manifest.blocker_paths == ["new_unmapped.py"]
    assert manifest.discuss_paths == ["db/models.py"]
    assert manifest.mapped_actions["db/models.py"][0].category == "russian_copy"
    assert manifest.to_json()["blocker_paths"] == ["new_unmapped.py"]
    assert manifest.to_json()["mapped_actions"] == {
        "db/models.py": [
            {
                "category": "russian_copy",
                "local_path": "db/models_ru.py",
                "local_target_path": "db/models_ru.py",
            }
        ]
    }


@pytest.mark.parametrize(
    ("mutator", "expected_error"),
    [
        (
            lambda payload: payload.pop("mapped_actions"),
            "missing required field 'mapped_actions'",
        ),
        (
            lambda payload: payload["changed_upstream_paths"].append(123),
            "field 'changed_upstream_paths\\[1\\]' must be a string",
        ),
        (
            lambda payload: payload["deleted_upstream_paths"].append(" "),
            "field 'deleted_upstream_paths\\[1\\]' must be a non-empty string",
        ),
        (
            lambda payload: payload["discuss_paths"].append(None),
            "field 'discuss_paths\\[1\\]' must be a string",
        ),
        (
            lambda payload: payload.__setitem__(
                "mapped_actions", {"db/models.py": "copy"}
            ),
            "field 'mapped_actions\\['db/models.py'\\]' must be a list",
        ),
        (
            lambda payload: payload.__setitem__(
                "mapped_actions",
                {"db/models.py": [{"category": "russian_copy"}]},
            ),
            "field 'mapped_actions\\['db/models.py'\\]\\[0\\]': missing required field 'local_path'",
        ),
    ],
)
def test_prep_manifest_from_raw_rejects_invalid_payload(
    mutator: Callable[[dict[str, object]], object], expected_error: str
) -> None:
    payload = valid_manifest_payload()
    mutator(payload)

    with pytest.raises(ValueError, match=expected_error):
        PrepManifest.from_raw(payload)


def test_prep_manifest_from_raw_accepts_legacy_payload_without_blockers() -> None:
    payload = valid_manifest_payload()
    payload.pop("blocker_paths")

    manifest = PrepManifest.from_raw(payload)

    assert manifest.blocker_paths == []
    assert manifest.to_json()["blocker_paths"] == []


def valid_registry_payload() -> dict[str, object]:
    return {
        "modified_upstream_files": [
            {"path": "db/models.py", "discuss": True, "discuss_reason": "review"}
        ],
        "russian_copies": {"db/models_ru.py": "db/models.py"},
        "sbs_copies": {},
        "dps_copies": {},
        "tamil_copies": {},
        "inspired_by_upstream": {
            "tools/example_dps.py": {
                "upstream": "tools/example.py",
                "divergence_reason": "localized behavior",
            }
        },
        "unique_paths": ["tools/local_only.py"],
        "no_sync_files": ["docs_rus/manual.md"],
        "skip_sync_patterns": ["resources/"],
    }


def test_registry_data_from_raw_valid_minimal_registry() -> None:
    registry = RegistryData.from_raw(valid_registry_payload())

    assert registry.modified_upstream_files[0].path == "db/models.py"
    assert registry.russian_copies == {"db/models_ru.py": "db/models.py"}
    assert registry.inspired_by_upstream["tools/example_dps.py"].upstream == (
        "tools/example.py"
    )
    assert registry.unique_paths == ["tools/local_only.py"]
    assert registry.no_sync_files == ["docs_rus/manual.md"]
    assert registry.skip_sync_patterns == ["resources/"]


@pytest.mark.parametrize(
    ("mutator", "expected_error"),
    [
        (
            lambda payload: payload["unique_paths"].append(123),
            "field 'unique_paths\\[1\\]' must be a string",
        ),
        (
            lambda payload: payload["unique_paths"].append(" "),
            "field 'unique_paths\\[1\\]' must be a non-empty string",
        ),
        (
            lambda payload: payload["no_sync_files"].append(None),
            "field 'no_sync_files\\[1\\]' must be a string",
        ),
        (
            lambda payload: payload["no_sync_files"].append(" "),
            "field 'no_sync_files\\[1\\]' must be a non-empty string",
        ),
        (
            lambda payload: payload.__setitem__(
                "russian_copies", {"db/models_ru.py": 123}
            ),
            "field 'russian_copies\\['db/models_ru.py'\\]' must be a string",
        ),
        (
            lambda payload: payload.__setitem__(
                "modified_upstream_files", [{"path": "db/models.py"}]
            ),
            "field 'modified_upstream_files\\[0\\]': missing required field 'discuss'",
        ),
        (
            lambda payload: payload.__setitem__(
                "inspired_by_upstream",
                {"tools/example_dps.py": {"upstream": "tools/example.py"}},
            ),
            "field 'inspired_by_upstream\\['tools/example_dps.py'\\]': missing required field 'divergence_reason'",
        ),
    ],
)
def test_registry_data_from_raw_rejects_invalid_payload(
    mutator: Callable[[dict[str, object]], object], expected_error: str
) -> None:
    payload = valid_registry_payload()
    mutator(payload)

    with pytest.raises(ValueError, match=expected_error):
        RegistryData.from_raw(payload)
