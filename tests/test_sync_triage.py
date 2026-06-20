"""Verify sync_triage.is_localized_noop correctly flags localized-impact syncs."""

from kamma.upstream_sync.scripts.sync_triage import is_localized_noop


def _base_manifest() -> dict[str, object]:
    return {
        "from_upstream_sha": "0" * 40,
        "to_upstream_sha": "1" * 40,
        "target_upstream_ref": "upstream/main",
        "generated_at": "2026-06-20T00:00:00+08:00",
        "changed_upstream_paths": [".github/workflows/ci.yml"],
        "deleted_upstream_paths": [],
        "blocker_paths": [],
        "discuss_paths": [],
        "needs_classification_paths": [],
        "unregistered_local_paths": [],
        "upstream_deleted_orphans": [],
        "mapped_actions": {
            ".github/workflows/ci.yml": [
                {
                    "category": "unique_paths",
                    "local_path": ".github/workflows/ci.yml",
                }
            ]
        },
    }


def test_no_localized_impact_is_noop() -> None:
    manifest = _base_manifest()
    assert is_localized_noop(manifest) is True


def test_dps_copies_mapped_action_blocks_noop() -> None:
    manifest = _base_manifest()
    manifest["mapped_actions"]["db/some_file.py"] = [
        {"category": "dps_copies", "local_path": "db/some_file_dps.py"}
    ]
    assert is_localized_noop(manifest) is False


def test_nonempty_discuss_paths_blocks_noop() -> None:
    manifest = _base_manifest()
    manifest["discuss_paths"] = ["some/upstream/file.py"]
    assert is_localized_noop(manifest) is False


def test_docs_path_in_changed_upstream_paths_blocks_noop() -> None:
    manifest = _base_manifest()
    manifest["changed_upstream_paths"] = ["docs/technical/quick_start.md"]
    assert is_localized_noop(manifest) is False
