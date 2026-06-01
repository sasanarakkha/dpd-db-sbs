"""Verify Prep analyzer builds stage-one sync report and manifest from explicit sync state."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from kamma.upstream_sync.scripts.prep_analyzer import PrepAnalyzer

FULL_OLD_SHA = "a" * 40
FULL_NEW_SHA = "b" * 40


@pytest.fixture
def mock_registry():
    return {
        "modified_upstream_files": [
            {"path": "db/models.py", "discuss": True, "discuss_reason": "Reason"}
        ],
        "russian_copies": {
            "db/families/family_compound_ru.py": "db/families/family_compound.py",
            "db/families/deleted_source_ru.py": "db/families/deleted_source.py",
            "exporter/webapp/main_ru.py": "exporter/webapp/main.py",
            "exporter/webapp/ru_templates/": "exporter/webapp/templates/",
        },
        "sbs_copies": {},
        "dps_copies": {},
        "tamil_copies": {"db/tpd/tpd_to_lookup.py": "db/epd/epd_to_lookup.py"},
        "inspired_by_upstream": {
            "scripts/bash/make_dpd.sh": {
                "upstream": "scripts/bash/makedict.py",
                "divergence_reason": "Reason",
            }
        },
        "unique_paths": [],
        "no_sync_files": [],
        "skip_sync_patterns": ["tests/"],
    }


@pytest.fixture
def accepted_sync_state() -> dict[str, str]:
    return {
        "last_accepted_upstream_sha": FULL_OLD_SHA,
        "last_accepted_upstream_date": "2026-04-08",
        "last_accepted_upstream_ref": "upstream/main",
    }


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
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.validate_registry_core",
            return_value=[],
        ),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.extract_all_smd_entries",
            return_value={},
        ),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.collect_registry_paths",
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
        "new_unmapped.py",
    ]

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
    assert (
        manifest["generated_at"] != accepted_sync_state["last_accepted_upstream_date"]
    )


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
        ("R100", "db/families/deleted_source.py db/families/family_compound.py")
    ]

    analyzer = PrepAnalyzer(tmp_path)
    with (
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.validate_registry_core",
            return_value=[],
        ),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.extract_all_smd_entries",
            return_value={},
        ),
        patch(
            "kamma.upstream_sync.scripts.prep_analyzer.collect_registry_paths",
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


def test_is_skipped(mock_registry, accepted_sync_state, tmp_path: Path) -> None:
    with patch(
        "kamma.upstream_sync.scripts.prep_analyzer.load_registry",
        return_value=mock_registry,
    ):
        with patch(
            "kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state",
            return_value=accepted_sync_state,
        ):
            analyzer = PrepAnalyzer(tmp_path)
            assert analyzer.is_skipped("tests/test.py")
            assert not analyzer.is_skipped("src/main.py")


def test_prep_analyzer_requires_bootstrapped_sync_state(
    mock_registry, tmp_path: Path
) -> None:
    with patch(
        "kamma.upstream_sync.scripts.prep_analyzer.load_registry",
        return_value=mock_registry,
    ):
        with patch(
            "kamma.upstream_sync.scripts.prep_analyzer.load_accepted_sync_state",
            return_value={
                "last_accepted_upstream_sha": "BOOTSTRAP_REQUIRED",
                "last_accepted_upstream_date": "BOOTSTRAP_REQUIRED",
                "last_accepted_upstream_ref": "upstream/main",
            },
        ):
            analyzer = PrepAnalyzer(tmp_path)

            with pytest.raises(
                ValueError, match="accepted sync state is not bootstrapped"
            ):
                analyzer.run()
