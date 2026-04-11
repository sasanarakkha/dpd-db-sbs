import pytest
from kamma.upstream_sync.scripts.validate_registry import (
    validate_registry_core,
    validate_inspired_by_upstream,
    validate_skip_sync_patterns,
    validate_cross_section_overlaps,
)


@pytest.fixture
def base_data():
    return {
        "modified_upstream_files": [
            {"path": "db/models.py", "discuss": True, "discuss_reason": "Reason"}
        ],
        "russian_copies": {},
        "sbs_copies": {},
        "dps_copies": {},
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
        "local.py": {"upstream": "upstream.py", "divergence_reason": "One sentence."}
    }
    errors = validate_inspired_by_upstream(base_data, tmp_path)
    assert not errors


def test_inspired_by_upstream_missing_upstream(base_data):
    base_data["inspired_by_upstream"] = {
        "local.py": {"divergence_reason": "One sentence."}
    }
    errors = validate_inspired_by_upstream(base_data)
    assert any("missing or invalid 'upstream' path" in e for e in errors)


def test_inspired_by_upstream_missing_divergence_reason(base_data):
    base_data["inspired_by_upstream"] = {"local.py": {"upstream": "upstream.py"}}
    errors = validate_inspired_by_upstream(base_data)
    assert any("missing or empty 'divergence_reason'" in e for e in errors)


def test_inspired_by_upstream_empty_divergence_reason(base_data):
    base_data["inspired_by_upstream"] = {
        "local.py": {"upstream": "upstream.py", "divergence_reason": "  "}
    }
    errors = validate_inspired_by_upstream(base_data)
    assert any("missing or empty 'divergence_reason'" in e for e in errors)


def test_inspired_by_upstream_missing_upstream_target_path(base_data, tmp_path):
    local_file = tmp_path / "local.py"
    local_file.touch()
    # Upstream file does NOT exist

    base_data["inspired_by_upstream"] = {
        "local.py": {"upstream": "upstream.py", "divergence_reason": "Reason"}
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


def test_ignored_files_rejected(base_data):
    base_data["ignored_files"] = ["old/"]
    errors = validate_registry_core(base_data)
    assert any("'ignored_files' is no longer valid" in e for e in errors)


def test_folders_to_check_rejected(base_data):
    base_data["folders_to_check"] = ["dir/"]
    errors = validate_registry_core(base_data)
    assert any("'folders_to_check' is no longer valid" in e for e in errors)


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
    base_data["russian_copies"] = {"exporter/webapp/main_ru.py": "exporter/webapp/main.py"}
    base_data["unique_paths"] = ["exporter/webapp/main_ru.py"]

    errors = validate_cross_section_overlaps(base_data)

    assert any(
        "Overlap: 'exporter/webapp/main_ru.py' exists in both russian_copies and unique_paths"
        in e
        for e in errors
    )
