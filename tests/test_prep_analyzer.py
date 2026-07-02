"""Verify Prep analyzer builds stage-one sync report and manifest from explicit sync state."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kamma.upstream_sync.scripts.prep_analyzer import PrepAnalyzer, get_upstream_changes
from kamma.upstream_sync.scripts.sync_schema import (
    AcceptedSyncState,
    InspiredByUpstreamEntry,
    ModifiedUpstreamEntry,
    RegistryData,
    ShadowCopyEntry,
)

FULL_OLD_SHA = "a" * 40
FULL_NEW_SHA = "b" * 40


@pytest.fixture(autouse=True)
def mock_git_methods():
    with (
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.get_upstream_tree_paths",
            return_value=set(),
        ),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.get_upstream_ever_added_paths",
            return_value=set(),
        ),
    ):
        yield


@pytest.fixture
def mock_registry() -> RegistryData:
    return RegistryData(
        modified_upstream_files=[
            ModifiedUpstreamEntry(
                path="db/models.py",
                discuss=True,
                discuss_reason="Reason",
                sync_rule="MIRROR_EXACTLY",
            )
        ],
        russian_copies={
            "db/families/family_compound_ru.py": ShadowCopyEntry(
                upstream="db/families/family_compound.py"
            ),
            "db/families/deleted_source_ru.py": ShadowCopyEntry(
                upstream="db/families/deleted_source.py"
            ),
            "exporter/webapp/main_ru.py": ShadowCopyEntry(
                upstream="exporter/webapp/main.py"
            ),
            "exporter/webapp/ru_templates/": ShadowCopyEntry(
                upstream="exporter/webapp/templates/"
            ),
        },
        sbs_copies={},
        dps_copies={},
        tamil_copies={
            "db/tpd/tpd_to_lookup.py": ShadowCopyEntry(
                upstream="db/epd/epd_to_lookup.py"
            )
        },
        inspired_by_upstream={
            "scripts/bash/make_dpd.sh": InspiredByUpstreamEntry(
                upstream="scripts/bash/makedict.py",
                divergence_reason="Reason",
                sync_rule="MIRROR_EXACTLY",
            )
        },
        unique_paths=[],
        no_sync_files=[],
        skip_sync_patterns=["tests/"],
    )


@pytest.fixture
def accepted_sync_state() -> AcceptedSyncState:
    return AcceptedSyncState(
        last_accepted_upstream_sha=FULL_OLD_SHA,
        last_accepted_upstream_date="2026-04-08",
        last_accepted_upstream_ref="upstream/main",
    )


@patch("kamma.upstream_sync.scripts.prep_analyzer.load_registry")
@patch("kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state")
@patch("kamma.upstream_sync.scripts.prep_analyzer.get_upstream_changes")
@patch("kamma.upstream_sync.scripts.prep_analyzer.resolve_target_upstream_sha")
def test_prep_analyzer_report_generation(
    mock_target,
    mock_changes,
    mock_state,
    mock_load,
    mock_registry,
    accepted_sync_state,
    tmp_path: Path,
) -> None:
    mock_load.return_value = mock_registry
    mock_state.return_value = accepted_sync_state
    mock_target.return_value = FULL_NEW_SHA
    mock_changes.return_value = [
        ("M", "db/models.py"),  # Tracked modified
        ("M", "db/families/family_compound.py"),  # Shadow source modified
        ("M", "exporter/webapp/main.py"),  # Russian source modified
        ("M", "exporter/webapp/templates/components/card.jinja"),  # Directory shadow
        ("M", "db/epd/epd_to_lookup.py"),  # Tamil source modified
        ("M", "scripts/bash/makedict.py"),  # Inspired source modified
        ("M", "new_file.py"),  # Untracked
        ("A", "new_unmapped.py"),  # New upstream file needing classification
        ("D", "db/families/deleted_source.py"),  # Deleted shadow source
        ("D", "deleted_file.py"),  # Deleted
        ("M", "tests/ignore_me.py"),  # Skipped
    ]

    analyzer = PrepAnalyzer(tmp_path)
    # Mocking validate_registry and verify_smd_coverage to avoid complex setup
    with (
        patch.object(analyzer, "_path_exists", return_value=False),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.validate_registry_core",
            return_value=[],
        ),
    ):
        analyzer.run()

    report_path = tmp_path / "prep_report.md"
    manifest_path = tmp_path / "prep_manifest.json"
    assert report_path.exists()
    assert manifest_path.exists()

    content = report_path.read_text()

    assert "db/models.py" in content
    assert "db/families/family_compound.py" in content
    assert "exporter/webapp/main.py" in content
    assert "scripts/bash/makedict.py" in content
    assert "new_file.py" in content
    assert "deleted_file.py" in content
    assert "tests/ignore_me.py" not in content
    assert "## New Or Unmapped Upstream Changes" in content
    assert "## Untracked Changes" not in content

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["from_upstream_sha"] == FULL_OLD_SHA
    assert manifest["to_upstream_sha"] == FULL_NEW_SHA
    assert manifest["discuss_paths"] == ["db/models.py"]
    assert manifest["changed_upstream_paths"] == [
        "db/epd/epd_to_lookup.py",
        "db/families/family_compound.py",
        "db/models.py",
        "exporter/webapp/main.py",
        "exporter/webapp/templates/components/card.jinja",
        "new_file.py",
        "new_unmapped.py",
        "scripts/bash/makedict.py",
    ]
    assert manifest["deleted_upstream_paths"] == [
        "db/families/deleted_source.py",
        "deleted_file.py",
    ]
    assert manifest["blocker_paths"] == [
        "db/families/deleted_source.py",
        "deleted_file.py",
    ]
    assert manifest["needs_classification_paths"] == ["new_unmapped.py"]

    mapped = manifest["mapped_actions"]
    assert (
        mapped["db/families/family_compound.py"][0]["local_path"]
        == "db/families/family_compound_ru.py"
    )
    assert (
        mapped["db/families/deleted_source.py"][0]["local_path"]
        == "db/families/deleted_source_ru.py"
    )
    assert mapped["exporter/webapp/main.py"][0]["category"] == "russian_copies"
    assert (
        mapped["exporter/webapp/main.py"][0]["local_target_path"]
        == "exporter/webapp/main_ru.py"
    )
    assert (
        mapped["exporter/webapp/templates/components/card.jinja"][0]["local_path"]
        == "exporter/webapp/ru_templates/"
    )
    assert (
        mapped["exporter/webapp/templates/components/card.jinja"][0][
            "local_target_path"
        ]
        == "exporter/webapp/ru_templates/components/card.jinja"
    )
    assert mapped["db/epd/epd_to_lookup.py"][0]["category"] == "tamil_copies"
    assert mapped["scripts/bash/makedict.py"][0]["category"] == "inspired_by_upstream"
    assert manifest["generated_at"] != accepted_sync_state.last_accepted_upstream_date


@patch("kamma.upstream_sync.scripts.prep_analyzer.load_registry")
@patch("kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state")
@patch("kamma.upstream_sync.scripts.prep_analyzer.get_upstream_changes")
@patch("kamma.upstream_sync.scripts.prep_analyzer.resolve_target_upstream_sha")
def test_prep_analyzer_treats_renames_as_delete_and_add(
    mock_target,
    mock_changes,
    mock_state,
    mock_load,
    mock_registry,
    accepted_sync_state,
    tmp_path: Path,
) -> None:
    mock_load.return_value = mock_registry
    mock_state.return_value = accepted_sync_state
    mock_target.return_value = FULL_NEW_SHA
    mock_changes.return_value = [
        ("D", "db/families/deleted_source.py"),
        ("A", "db/families/family_compound.py"),
    ]

    analyzer = PrepAnalyzer(tmp_path)
    with (
        patch.object(analyzer, "_path_exists", return_value=False),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.validate_registry_core",
            return_value=[],
        ),
    ):
        analyzer.run()

    manifest = json.loads((tmp_path / "prep_manifest.json").read_text(encoding="utf-8"))
    assert manifest["deleted_upstream_paths"] == ["db/families/deleted_source.py"]
    assert manifest["changed_upstream_paths"] == ["db/families/family_compound.py"]
    assert (
        manifest["mapped_actions"]["db/families/deleted_source.py"][0]["local_path"]
        == "db/families/deleted_source_ru.py"
    )
    assert (
        manifest["mapped_actions"]["db/families/family_compound.py"][0]["local_path"]
        == "db/families/family_compound_ru.py"
    )


@patch("kamma.upstream_sync.scripts.prep_analyzer.subprocess.run")
def test_get_upstream_changes_uses_nul_delimited_name_status(
    mock_run: MagicMock,
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=(
            "M\x00path with spaces.py\x00"
            "R100\x00old folder/old name.py\x00new folder/new name.py\x00"
            "A\x00added.py\x00"
        ),
        stderr="",
    )

    changes = get_upstream_changes(FULL_OLD_SHA, FULL_NEW_SHA)

    assert changes == [
        ("M", "path with spaces.py"),
        ("D", "old folder/old name.py"),
        ("A", "new folder/new name.py"),
        ("A", "added.py"),
    ]
    mock_run.assert_called_once_with(
        ["git", "diff", "--name-status", "-z", FULL_OLD_SHA, FULL_NEW_SHA],
        capture_output=True,
        text=True,
        check=True,
    )


def test_is_skipped(mock_registry, accepted_sync_state, tmp_path: Path) -> None:
    with (
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.load_registry",
            return_value=mock_registry,
        ),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state",
            return_value=accepted_sync_state,
        ),
    ):
        analyzer = PrepAnalyzer(tmp_path)
        assert analyzer.is_skipped("tests/test.py")
        assert not analyzer.is_skipped("src/main.py")


@patch("kamma.upstream_sync.scripts.prep_analyzer.load_registry")
@patch("kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state")
@patch("kamma.upstream_sync.scripts.prep_analyzer.get_upstream_changes")
@patch("kamma.upstream_sync.scripts.prep_analyzer.resolve_target_upstream_sha")
def test_added_file_under_mapped_dir_appears_only_in_shadow_section(
    mock_target,
    mock_changes,
    mock_state,
    mock_load,
    mock_registry,
    accepted_sync_state,
    tmp_path: Path,
) -> None:
    mock_load.return_value = mock_registry
    mock_state.return_value = accepted_sync_state
    mock_target.return_value = FULL_NEW_SHA
    # New file added upstream inside a directory that is mapped as a shadow
    mock_changes.return_value = [
        ("A", "exporter/webapp/templates/components/new_widget.jinja"),
    ]

    analyzer = PrepAnalyzer(tmp_path)
    with (
        patch.object(analyzer, "_path_exists", return_value=False),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.validate_registry_core",
            return_value=[],
        ),
    ):
        analyzer.run()

    report = (tmp_path / "prep_report.md").read_text()
    manifest = json.loads((tmp_path / "prep_manifest.json").read_text(encoding="utf-8"))

    # Must appear in shadow sources (matched via directory mapping)
    assert "exporter/webapp/templates/components/new_widget.jinja" in report
    assert "## Modified - Shadow Sources" in report

    # Must NOT appear in "New Or Unmapped" section
    new_unmapped_section = report.split("## New Or Unmapped Upstream Changes")[1]
    assert "new_widget.jinja" not in new_unmapped_section.split("##")[0]

    # Must NOT be a blocker (it matched a shadow mapping)
    assert (
        "exporter/webapp/templates/components/new_widget.jinja"
        not in manifest["blocker_paths"]
    )


def test_prep_analyzer_requires_bootstrapped_sync_state(
    mock_registry, tmp_path: Path
) -> None:
    with (
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.load_registry",
            return_value=mock_registry,
        ),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state",
            return_value=AcceptedSyncState(
                last_accepted_upstream_sha="BOOTSTRAP_REQUIRED",
                last_accepted_upstream_date="BOOTSTRAP_REQUIRED",
                last_accepted_upstream_ref="upstream/main",
            ),
        ),
    ):
        analyzer = PrepAnalyzer(tmp_path)

        with pytest.raises(ValueError, match="accepted sync state is not bootstrapped"):
            analyzer.run()


def _run_analyzer_with_changes(
    mock_registry: RegistryData,
    accepted_sync_state: AcceptedSyncState,
    changes: list[tuple[str, str]],
    tmp_path: Path,
    path_exists: bool = False,
) -> dict[str, object]:
    """Helper: run PrepAnalyzer with mocked changes and return the manifest."""
    with (
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.load_registry",
            return_value=mock_registry,
        ),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state",
            return_value=accepted_sync_state,
        ),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.resolve_target_upstream_sha",
            return_value=FULL_NEW_SHA,
        ),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.get_upstream_changes",
            return_value=changes,
        ),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.validate_registry_core",
            return_value=[],
        ),
    ):
        analyzer = PrepAnalyzer(tmp_path)
        with patch.object(analyzer, "_path_exists", return_value=path_exists):
            analyzer.run()

    return json.loads((tmp_path / "prep_manifest.json").read_text(encoding="utf-8"))


@patch("kamma.upstream_sync.scripts.prep_analyzer.load_registry")
@patch("kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state")
@patch("kamma.upstream_sync.scripts.prep_analyzer.get_upstream_changes")
@patch("kamma.upstream_sync.scripts.prep_analyzer.resolve_target_upstream_sha")
def test_non_colliding_add_goes_to_needs_classification(
    mock_target,
    mock_changes,
    mock_state,
    mock_load,
    mock_registry,
    accepted_sync_state,
    tmp_path: Path,
) -> None:
    mock_load.return_value = mock_registry
    mock_state.return_value = accepted_sync_state
    mock_target.return_value = FULL_NEW_SHA
    mock_changes.return_value = [("A", "brand_new_upstream.py")]

    analyzer = PrepAnalyzer(tmp_path)
    with (
        patch.object(analyzer, "_path_exists", return_value=False),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.validate_registry_core",
            return_value=[],
        ),
    ):
        analyzer.run()

    manifest = json.loads((tmp_path / "prep_manifest.json").read_text(encoding="utf-8"))
    report = (tmp_path / "prep_report.md").read_text()

    assert manifest["blocker_paths"] == []
    assert manifest["needs_classification_paths"] == ["brand_new_upstream.py"]
    assert "## Needs Classification (Stage 2)" in report
    assert "brand_new_upstream.py" in report


@patch("kamma.upstream_sync.scripts.prep_analyzer.load_registry")
@patch("kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state")
@patch("kamma.upstream_sync.scripts.prep_analyzer.get_upstream_changes")
@patch("kamma.upstream_sync.scripts.prep_analyzer.resolve_target_upstream_sha")
def test_add_colliding_with_worktree_file_remains_blocker(
    mock_target,
    mock_changes,
    mock_state,
    mock_load,
    mock_registry,
    accepted_sync_state,
    tmp_path: Path,
) -> None:
    mock_load.return_value = mock_registry
    mock_state.return_value = accepted_sync_state
    mock_target.return_value = FULL_NEW_SHA
    mock_changes.return_value = [("A", "existing_local.py")]

    analyzer = PrepAnalyzer(tmp_path)
    with (
        patch.object(analyzer, "_path_exists", return_value=True),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.validate_registry_core",
            return_value=[],
        ),
    ):
        analyzer.run()

    manifest = json.loads((tmp_path / "prep_manifest.json").read_text(encoding="utf-8"))

    assert manifest["blocker_paths"] == ["existing_local.py"]
    assert manifest["needs_classification_paths"] == []


@patch("kamma.upstream_sync.scripts.prep_analyzer.load_registry")
@patch("kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state")
@patch("kamma.upstream_sync.scripts.prep_analyzer.get_upstream_changes")
@patch("kamma.upstream_sync.scripts.prep_analyzer.resolve_target_upstream_sha")
def test_add_colliding_with_registered_local_path_remains_blocker(
    mock_target,
    mock_changes,
    mock_state,
    mock_load,
    mock_registry,
    accepted_sync_state,
    tmp_path: Path,
) -> None:
    mock_load.return_value = mock_registry
    mock_state.return_value = accepted_sync_state
    mock_target.return_value = FULL_NEW_SHA
    # db/families/family_compound_ru.py is a key in mock_registry.russian_copies
    mock_changes.return_value = [("A", "db/families/family_compound_ru.py")]

    analyzer = PrepAnalyzer(tmp_path)
    with (
        patch.object(analyzer, "_path_exists", return_value=False),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.validate_registry_core",
            return_value=[],
        ),
    ):
        analyzer.run()

    manifest = json.loads((tmp_path / "prep_manifest.json").read_text(encoding="utf-8"))

    assert manifest["blocker_paths"] == ["db/families/family_compound_ru.py"]
    assert manifest["needs_classification_paths"] == []


@patch("kamma.upstream_sync.scripts.prep_analyzer.load_registry")
@patch("kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state")
@patch("kamma.upstream_sync.scripts.prep_analyzer.get_upstream_changes")
@patch("kamma.upstream_sync.scripts.prep_analyzer.resolve_target_upstream_sha")
def test_deletion_remains_blocker_with_collision_rule(
    mock_target,
    mock_changes,
    mock_state,
    mock_load,
    mock_registry,
    accepted_sync_state,
    tmp_path: Path,
) -> None:
    mock_load.return_value = mock_registry
    mock_state.return_value = accepted_sync_state
    mock_target.return_value = FULL_NEW_SHA
    mock_changes.return_value = [("D", "deleted_upstream.py")]

    analyzer = PrepAnalyzer(tmp_path)
    with (
        patch.object(analyzer, "_path_exists", return_value=False),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.validate_registry_core",
            return_value=[],
        ),
    ):
        analyzer.run()

    manifest = json.loads((tmp_path / "prep_manifest.json").read_text(encoding="utf-8"))

    assert manifest["blocker_paths"] == ["deleted_upstream.py"]
    assert manifest["needs_classification_paths"] == []
