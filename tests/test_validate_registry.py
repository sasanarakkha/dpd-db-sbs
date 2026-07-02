"""Verify upstream sync registry schema and cross-section integrity."""

import pytest

from kamma.upstream_sync.scripts.validate_registry import (
    validate_cross_section_overlaps,
    validate_inspired_by_upstream,
    validate_registry_core,
    validate_shadow_mapping,
    validate_skip_sync_patterns,
)


@pytest.fixture
def base_data():
    return {
        "modified_upstream_files": [
            {
                "path": "db/models.py",
                "discuss": True,
                "discuss_reason": "Reason",
                "sync_rule": "MIRROR_EXACTLY",
            }
        ],
        "russian_copies": {},
        "sbs_copies": {},
        "dps_copies": {},
        "tamil_copies": {},
        "inspired_by_upstream": {},
        "unique_paths": [],
        "no_sync_files": [],
        "skip_sync_patterns": [],
    }


def test_inspired_by_upstream_valid(base_data, tmp_path):
    # Create dummy files
    local_file = tmp_path / "local.py"
    local_file.touch()
    upstream_file = tmp_path / "upstream.py"
    upstream_file.touch()

    base_data["inspired_by_upstream"] = {
        "local.py": {
            "upstream": "upstream.py",
            "divergence_reason": "One sentence.",
            "sync_rule": "MIRROR_EXACTLY",
        }
    }
    errors = validate_inspired_by_upstream(base_data, tmp_path)
    assert not errors


def test_inspired_by_upstream_missing_upstream(base_data):
    base_data["inspired_by_upstream"] = {
        "local.py": {
            "divergence_reason": "One sentence.",
            "sync_rule": "MIRROR_EXACTLY",
        }
    }
    errors = validate_inspired_by_upstream(base_data)
    assert any("missing or invalid 'upstream' path" in e for e in errors)


def test_inspired_by_upstream_missing_divergence_reason(base_data):
    base_data["inspired_by_upstream"] = {
        "local.py": {"upstream": "upstream.py", "sync_rule": "MIRROR_EXACTLY"}
    }
    errors = validate_inspired_by_upstream(base_data)
    assert any("missing or empty 'divergence_reason'" in e for e in errors)


def test_inspired_by_upstream_empty_divergence_reason(base_data):
    base_data["inspired_by_upstream"] = {
        "local.py": {
            "upstream": "upstream.py",
            "divergence_reason": "  ",
            "sync_rule": "MIRROR_EXACTLY",
        }
    }
    errors = validate_inspired_by_upstream(base_data)
    assert any("missing or empty 'divergence_reason'" in e for e in errors)


def test_inspired_by_upstream_missing_upstream_target_path(base_data, tmp_path):
    local_file = tmp_path / "local.py"
    local_file.touch()
    # Upstream file does NOT exist

    base_data["inspired_by_upstream"] = {
        "local.py": {
            "upstream": "upstream.py",
            "divergence_reason": "Reason",
            "sync_rule": "MIRROR_EXACTLY",
        }
    }
    errors = validate_inspired_by_upstream(base_data, tmp_path)
    assert any("upstream path 'upstream.py' does not exist" in e for e in errors)


def test_skip_sync_patterns_valid(base_data):
    base_data["skip_sync_patterns"] = ["tests/", "*.tmp"]
    errors = validate_skip_sync_patterns(base_data)
    assert not errors


def test_skip_sync_patterns_not_a_list(base_data):
    base_data["skip_sync_patterns"] = "not a list"
    errors = validate_skip_sync_patterns(base_data)
    assert any("must be a list" in e for e in errors)


def test_skip_sync_patterns_blank_item_rejected(base_data):
    base_data["skip_sync_patterns"] = ["valid", " ", ""]
    errors = validate_skip_sync_patterns(base_data)
    assert len(errors) == 2


def test_unique_paths_rejects_non_string_item(base_data):
    base_data["unique_paths"] = ["tools/local.py", 123]

    errors = validate_registry_core(base_data)

    assert "unique_paths[1]: must be a non-empty string" in errors


def test_unique_paths_rejects_blank_item(base_data):
    base_data["unique_paths"] = ["tools/local.py", " "]

    errors = validate_registry_core(base_data)

    assert "unique_paths[1]: must be a non-empty string" in errors


def test_no_sync_files_rejects_non_string_item(base_data):
    base_data["no_sync_files"] = ["docs_rus/manual.md", None]

    errors = validate_registry_core(base_data)

    assert "no_sync_files[1]: must be a non-empty string" in errors


def test_no_sync_files_rejects_blank_item(base_data):
    base_data["no_sync_files"] = ["docs_rus/manual.md", ""]

    errors = validate_registry_core(base_data)

    assert "no_sync_files[1]: must be a non-empty string" in errors


def test_registry_paths_reject_unsafe_values(base_data):
    base_data["modified_upstream_files"] = [
        {
            "path": "/tmp/outside.py",
            "discuss": False,
            "discuss_reason": "",
            "sync_rule": "MIRROR_EXACTLY",
        }
    ]
    base_data["no_sync_files"] = ["../outside.py"]
    base_data["russian_copies"] = {
        "-bad.py": {"upstream": "db/source.py", "sync_rule": "MIRROR_EXACTLY"}
    }

    errors = validate_registry_core(base_data)

    assert any("modified_upstream_files[0].path" in e for e in errors)
    assert any("must be a repo-relative path" in e for e in errors)
    assert any("no_sync_files[0]" in e for e in errors)
    assert any("must stay inside the repository" in e for e in errors)
    assert any("russian_copies key '-bad.py'" in e for e in errors)
    assert any("must not start with '-'" in e for e in errors)


def test_registry_path_validation_allows_inventory_globs(base_data):
    base_data["unique_paths"] = ["gui2/dps_*"]
    base_data["skip_sync_patterns"] = ["*.tmp"]

    errors = validate_registry_core(base_data)

    assert not any("pathspec metacharacters" in e for e in errors)


def test_ignored_files_rejected(base_data):
    base_data["ignored_files"] = ["old/"]
    errors = validate_registry_core(base_data)
    assert any("'ignored_files' is no longer valid" in e for e in errors)


def test_folders_to_check_rejected(base_data):
    base_data["folders_to_check"] = ["dir/"]
    errors = validate_registry_core(base_data)
    assert any("'folders_to_check' is no longer valid" in e for e in errors)


def test_missing_required_top_level_section_rejected(base_data):
    del base_data["tamil_copies"]

    errors = validate_registry_core(base_data)

    assert "registry: missing required top-level section 'tamil_copies'" in errors


def test_cross_category_overlap_rejected(base_data):
    base_data["unique_paths"] = ["db/models.py"]
    # db/models.py is already in modified_upstream_files in base_data
    errors = validate_cross_section_overlaps(base_data)
    assert any(
        "Overlap: 'db/models.py' exists in both modified_upstream_files and unique_paths"
        in e
        for e in errors
    )


def test_russian_copy_overlap_rejected(base_data):
    base_data["russian_copies"] = {
        "exporter/webapp/main_ru.py": {
            "upstream": "exporter/webapp/main.py",
            "sync_rule": "MIRROR_EXACTLY",
        }
    }
    base_data["unique_paths"] = ["exporter/webapp/main_ru.py"]

    errors = validate_cross_section_overlaps(base_data)

    assert any(
        "Overlap: 'exporter/webapp/main_ru.py' exists in both russian_copies and unique_paths"
        in e
        for e in errors
    )


def test_dps_copy_must_not_also_be_registered_as_locale_copy(base_data):
    base_data["russian_copies"] = {
        "exporter/goldendict/data_classes_dps.py": {
            "upstream": "exporter/goldendict/data_classes.py",
            "sync_rule": "MIRROR_EXACTLY",
        }
    }
    base_data["sbs_copies"] = {
        "exporter/goldendict/data_classes_dps.py": {
            "upstream": "exporter/goldendict/data_classes.py",
            "sync_rule": "MIRROR_EXACTLY",
        }
    }

    errors = validate_cross_section_overlaps(base_data)

    assert any(
        "Overlap: 'exporter/goldendict/data_classes_dps.py' exists in both russian_copies and sbs_copies"
        in e
        for e in errors
    )


def test_shadow_mapping_rejects_non_object(base_data):
    base_data["russian_copies"] = ["not-a-mapping"]

    errors = validate_shadow_mapping("russian_copies", base_data)

    assert errors == ["russian_copies: must be an object"]


def test_shadow_mapping_rejects_non_string_source(base_data):
    base_data["russian_copies"] = {"db/families/family_compound_ru.py": 123}

    errors = validate_shadow_mapping("russian_copies", base_data)

    assert errors == [
        "russian_copies['db/families/family_compound_ru.py']: entry must be an object"
    ]


def test_shadow_mapping_rejects_missing_upstream_source(base_data, tmp_path):
    shadow_file = tmp_path / "db/families/family_compound_ru.py"
    shadow_file.parent.mkdir(parents=True)
    shadow_file.touch()
    base_data["russian_copies"] = {
        "db/families/family_compound_ru.py": {
            "upstream": "db/families/family_compound.py",
            "sync_rule": "MIRROR_EXACTLY",
        }
    }

    errors = validate_registry_core(base_data, tmp_path)

    assert any(
        "russian_copies: upstream source 'db/families/family_compound.py' does not exist"
        in e
        for e in errors
    )


def test_rubric_allows_single_local_change(base_data, capsys):
    base_data["modified_upstream_files"] = [
        {
            "path": ".pre-commit-config.yaml",
            "discuss": False,
            "discuss_reason": "",
            "sync_rule": "DISCUSS",
            "local_changes": ["pyrefly hook added"],
            "watch_for": ["upstream hook list changes"],
        }
    ]

    validate_registry_core(base_data)

    assert "local-change(s)" not in capsys.readouterr().out
