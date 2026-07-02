"""Verify typed upstream sync metadata schema parsing and validation."""

from collections.abc import Callable

import pytest

from kamma.upstream_sync.scripts.sync_schema import (
    AcceptedSyncState,
    MappedAction,
    PrepManifest,
    RegistryData,
    ShadowCopyEntry,
)

FULL_OLD_SHA = "a" * 40
FULL_NEW_SHA = "b" * 40


def test_accepted_sync_state_from_raw_valid_with_notes() -> None:
    state = AcceptedSyncState.from_raw(
        {
            "last_accepted_upstream_sha": FULL_OLD_SHA,
            "last_accepted_upstream_date": "2026-05-31T12:00:00+08:00",
            "last_accepted_upstream_ref": "upstream/main",
            "notes": "verified baseline",
        }
    )

    assert state.last_accepted_upstream_sha == FULL_OLD_SHA
    assert state.last_accepted_upstream_date == "2026-05-31T12:00:00+08:00"
    assert state.last_accepted_upstream_ref == "upstream/main"
    assert state.notes == "verified baseline"
    assert state.to_json() == {
        "last_accepted_upstream_sha": FULL_OLD_SHA,
        "last_accepted_upstream_date": "2026-05-31T12:00:00+08:00",
        "last_accepted_upstream_ref": "upstream/main",
        "notes": "verified baseline",
    }


def test_accepted_sync_state_accepts_bootstrap_sentinel() -> None:
    state = AcceptedSyncState.from_raw(
        {
            "last_accepted_upstream_sha": "BOOTSTRAP_REQUIRED",
            "last_accepted_upstream_date": "BOOTSTRAP_REQUIRED",
            "last_accepted_upstream_ref": "upstream/main",
        }
    )

    assert state.last_accepted_upstream_sha == "BOOTSTRAP_REQUIRED"


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
                "last_accepted_upstream_sha": FULL_OLD_SHA,
                "last_accepted_upstream_date": 20260531,
                "last_accepted_upstream_ref": "upstream/main",
            },
            "field 'last_accepted_upstream_date' must be a string",
        ),
        (
            {
                "last_accepted_upstream_sha": FULL_OLD_SHA,
                "last_accepted_upstream_date": "2026-05-31T12:00:00+08:00",
                "last_accepted_upstream_ref": " ",
            },
            "field 'last_accepted_upstream_ref' must be a non-empty string",
        ),
        (
            {
                "last_accepted_upstream_sha": FULL_OLD_SHA,
                "last_accepted_upstream_date": "2026-05-31T12:00:00+08:00",
                "last_accepted_upstream_ref": "upstream/main",
                "notes": ["not", "a", "string"],
            },
            "field 'notes' must be a string",
        ),
        (
            {
                "last_accepted_upstream_sha": "abc123",
                "last_accepted_upstream_date": "2026-05-31T12:00:00+08:00",
                "last_accepted_upstream_ref": "upstream/main",
            },
            "field 'last_accepted_upstream_sha' must be a full 40-character lowercase git SHA",
        ),
    ],
)
def test_accepted_sync_state_from_raw_rejects_invalid_payload(
    payload: object, expected_error: str
) -> None:
    with pytest.raises((ValueError, TypeError), match=expected_error):
        AcceptedSyncState.from_raw(payload)


def test_mapped_action_from_raw_valid_with_local_target_path() -> None:
    action = MappedAction.from_raw(
        {
            "category": "russian_copies",
            "local_path": "db/models_ru.py",
            "local_target_path": "db/models_ru.py",
        }
    )

    assert action.category == "russian_copies"
    assert action.local_path == "db/models_ru.py"
    assert action.local_target_path == "db/models_ru.py"
    assert action.to_json() == {
        "category": "russian_copies",
        "local_path": "db/models_ru.py",
        "local_target_path": "db/models_ru.py",
    }


def test_mapped_action_from_raw_accepts_backward_compatible_payload() -> None:
    action = MappedAction.from_raw(
        {
            "category": "russian_copies",
            "local_path": "db/models_ru.py",
        }
    )

    assert action.category == "russian_copies"
    assert action.local_path == "db/models_ru.py"
    assert action.local_target_path is None
    assert action.to_json() == {
        "category": "russian_copies",
        "local_path": "db/models_ru.py",
    }


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        ({"local_path": "db/models_ru.py"}, "missing required field 'category'"),
        (
            {"category": "russian_copies", "local_path": " "},
            "field 'local_path' must be a non-empty string",
        ),
        (
            {
                "category": "russian_copies",
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
    with pytest.raises((ValueError, TypeError), match=expected_error):
        MappedAction.from_raw(payload, "action")


def valid_manifest_payload() -> dict[str, object]:
    return {
        "from_upstream_sha": FULL_OLD_SHA,
        "to_upstream_sha": FULL_NEW_SHA,
        "target_upstream_ref": "upstream/main",
        "generated_at": "2026-05-31T12:00:00+08:00",
        "changed_upstream_paths": ["db/models.py"],
        "deleted_upstream_paths": ["old.py"],
        "blocker_paths": ["new_unmapped.py"],
        "discuss_paths": ["db/models.py"],
        "mapped_actions": {
            "db/models.py": [
                {
                    "category": "russian_copies",
                    "local_path": "db/models_ru.py",
                    "local_target_path": "db/models_ru.py",
                }
            ]
        },
    }


def test_prep_manifest_from_raw_valid_with_current_fields() -> None:
    manifest = PrepManifest.from_raw(valid_manifest_payload())

    assert manifest.from_upstream_sha == FULL_OLD_SHA
    assert manifest.to_upstream_sha == FULL_NEW_SHA
    assert manifest.target_upstream_ref == "upstream/main"
    assert manifest.changed_upstream_paths == ["db/models.py"]
    assert manifest.deleted_upstream_paths == ["old.py"]
    assert manifest.blocker_paths == ["new_unmapped.py"]
    assert manifest.discuss_paths == ["db/models.py"]
    assert manifest.mapped_actions["db/models.py"][0].category == "russian_copies"
    assert manifest.to_json()["blocker_paths"] == ["new_unmapped.py"]
    assert manifest.to_json()["mapped_actions"] == {
        "db/models.py": [
            {
                "category": "russian_copies",
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
            lambda payload: payload.__setitem__("to_upstream_sha", "newsha"),
            "field 'to_upstream_sha' must be a full 40-character lowercase git SHA",
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
            lambda payload: payload["changed_upstream_paths"].append("../outside.py"),
            "changed_upstream_paths\\[1\\] must stay inside the repository",
        ),
        (
            lambda payload: payload["deleted_upstream_paths"].append("/tmp/outside.py"),
            "deleted_upstream_paths\\[1\\] must be a repo-relative path",
        ),
        (
            lambda payload: payload["blocker_paths"].append("exporter/**/*.py"),
            "blocker_paths\\[1\\] must not contain git pathspec metacharacters",
        ),
        (
            lambda payload: payload["discuss_paths"].append(" spaced.py "),
            "discuss_paths\\[1\\] must not contain surrounding whitespace",
        ),
        (
            lambda payload: payload.__setitem__(
                "mapped_actions",
                {
                    "../outside.py": [
                        {
                            "category": "russian_copies",
                            "local_path": "db/models_ru.py",
                        }
                    ]
                },
            ),
            "mapped_actions key '../outside.py' must stay inside the repository",
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
                {"db/models.py": [{"category": "russian_copies"}]},
            ),
            "field 'mapped_actions\\['db/models.py'\\]\\[0\\]': missing required field 'local_path'",
        ),
        (
            lambda payload: payload.__setitem__(
                "mapped_actions",
                {
                    "db/models.py": [
                        {
                            "category": "russian_copies",
                            "local_path": "-danger",
                        }
                    ]
                },
            ),
            "field 'mapped_actions\\['db/models.py'\\]\\[0\\]': "
            "local_path must not start with '-'",
        ),
        (
            lambda payload: payload.__setitem__(
                "mapped_actions",
                {
                    "db/models.py": [
                        {
                            "category": "russian_copies",
                            "local_path": "db/models_ru.py",
                            "local_target_path": "db/../outside.py",
                        }
                    ]
                },
            ),
            "field 'mapped_actions\\['db/models.py'\\]\\[0\\]': "
            "local_target_path must stay inside the repository",
        ),
    ],
)
def test_prep_manifest_from_raw_rejects_invalid_payload(
    mutator: Callable[[dict[str, object]], object], expected_error: str
) -> None:
    payload = valid_manifest_payload()
    mutator(payload)

    with pytest.raises((ValueError, TypeError), match=expected_error):
        PrepManifest.from_raw(payload)


def test_prep_manifest_from_raw_accepts_legacy_payload_without_blockers() -> None:
    payload = valid_manifest_payload()
    payload.pop("blocker_paths")

    manifest = PrepManifest.from_raw(payload)

    assert manifest.blocker_paths == []
    assert manifest.to_json()["blocker_paths"] == []


def test_prep_manifest_needs_classification_paths_defaults_to_empty() -> None:
    manifest = PrepManifest.from_raw(valid_manifest_payload())

    assert manifest.needs_classification_paths == []
    assert manifest.to_json()["needs_classification_paths"] == []


def test_prep_manifest_needs_classification_paths_round_trips() -> None:
    payload = valid_manifest_payload()
    payload["needs_classification_paths"] = ["new_upstream.py", "tools/new_tool.py"]

    manifest = PrepManifest.from_raw(payload)

    assert manifest.needs_classification_paths == [
        "new_upstream.py",
        "tools/new_tool.py",
    ]
    assert manifest.to_json()["needs_classification_paths"] == [
        "new_upstream.py",
        "tools/new_tool.py",
    ]


@pytest.mark.parametrize(
    ("paths", "expected_error"),
    [
        (
            ["exporter/**/*.py"],
            "needs_classification_paths\\[0\\] must not contain git pathspec metacharacters",
        ),
        (
            ["../outside.py"],
            "needs_classification_paths\\[0\\] must stay inside the repository",
        ),
        (
            ["/tmp/outside.py"],
            "needs_classification_paths\\[0\\] must be a repo-relative path",
        ),
        (
            [" spaced.py "],
            "needs_classification_paths\\[0\\] must not contain surrounding whitespace",
        ),
    ],
)
def test_prep_manifest_rejects_invalid_needs_classification_paths(
    paths: list[str], expected_error: str
) -> None:
    payload = valid_manifest_payload()
    payload["needs_classification_paths"] = paths

    with pytest.raises(ValueError, match=expected_error):
        PrepManifest.from_raw(payload)


def valid_registry_payload() -> dict[str, object]:
    return {
        "modified_upstream_files": [
            {
                "path": "db/models.py",
                "discuss": True,
                "discuss_reason": "review",
                "sync_rule": "MIRROR_EXACTLY",
            }
        ],
        "russian_copies": {
            "db/models_ru.py": {
                "upstream": "db/models.py",
                "sync_rule": "MIRROR_EXACTLY",
            }
        },
        "sbs_copies": {},
        "dps_copies": {},
        "tamil_copies": {},
        "inspired_by_upstream": {
            "tools/example_dps.py": {
                "upstream": "tools/example.py",
                "divergence_reason": "localized behavior",
                "sync_rule": "MIRROR_EXACTLY",
            }
        },
        "unique_paths": ["tools/local_only.py"],
        "no_sync_files": ["docs_rus/manual.md"],
        "skip_sync_patterns": ["resources/"],
    }


def test_registry_data_from_raw_valid_minimal_registry() -> None:
    registry = RegistryData.from_raw(valid_registry_payload())

    assert registry.modified_upstream_files[0].path == "db/models.py"
    assert registry.russian_copies == {
        "db/models_ru.py": ShadowCopyEntry(
            upstream="db/models.py", sync_rule="MIRROR_EXACTLY"
        )
    }
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
            "field 'russian_copies\\['db/models_ru.py'\\]' must be a JSON object",
        ),
        (
            lambda payload: payload.__setitem__(
                "modified_upstream_files", [{"path": "db/models.py"}]
            ),
            "missing required field 'discuss'",
        ),
        (
            lambda payload: payload.__setitem__(
                "inspired_by_upstream",
                {"tools/example_dps.py": {"upstream": "tools/example.py"}},
            ),
            "missing required field 'divergence_reason'",
        ),
    ],
)
def test_registry_data_from_raw_rejects_invalid_payload(
    mutator: Callable[[dict[str, object]], object], expected_error: str
) -> None:
    payload = valid_registry_payload()
    mutator(payload)

    with pytest.raises((ValueError, TypeError), match=expected_error):
        RegistryData.from_raw(payload)
