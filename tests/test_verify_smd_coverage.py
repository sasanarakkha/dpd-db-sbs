"""Verify SMD coverage checks include every upstream sync registry category."""

import pytest
from kamma.upstream_sync.scripts.verify_smd_coverage import (
    check_category_alignment,
    collect_registry_paths,
    extract_all_smd_entries,
    extract_smd_entries,
    check_rubric,
)


def test_extract_smd_entries_single(tmp_path):
    smd_file = tmp_path / "test.md"
    smd_file.write_text("""
**File**: `path/to/file.py`
- **Category**: shadow
- **Sync Rule**: PORT
1. Local change one.
2. Local change two.

**Watch For**:
- PITFALL_ONE
""")
    entries = extract_smd_entries(smd_file)
    assert "path/to/file.py" in entries
    assert entries["path/to/file.py"]["category"] == "shadow"
    assert entries["path/to/file.py"]["sync_rule"] == "PORT"
    assert entries["path/to/file.py"]["local_changes_count"] == 2
    assert entries["path/to/file.py"]["watch_for_count"] == 1


def test_extract_all_smd_entries_aggregate(tmp_path):
    (tmp_path / "db.md").write_text(
        "**File**: `db/mod.py`\n**Sync Rule**: PORT\n1.\n2.\n**Watch For**:\n-"
    )
    (tmp_path / "gui.md").write_text(
        "**File**: `gui/main.py`\n**Sync Rule**: PORT\n1.\n2.\n**Watch For**:\n-"
    )
    (tmp_path / "index.md").write_text("Should be ignored")

    entries = extract_all_smd_entries(tmp_path)
    assert len(entries) == 2
    assert "db/mod.py" in entries
    assert "gui/main.py" in entries


def test_fail_on_duplicate_file_entry(tmp_path):
    (tmp_path / "db1.md").write_text("**File**: `db/mod.py`\n")
    (tmp_path / "db2.md").write_text("**File**: `db/mod.py`\n")

    with pytest.raises(ValueError, match="Duplicate SMD entry for 'db/mod.py'"):
        extract_all_smd_entries(tmp_path)


def test_check_rubric_inspired_only() -> None:
    # inspired_only skips min local changes but requires Watch For
    entry: dict[str, object] = {
        "sync_rule": "inspired_only",
        "local_changes_count": 0,
        "watch_for_count": 1,
    }
    violations = check_rubric("path", "category", entry)
    assert not violations

    entry_no_watch: dict[str, object] = {
        "sync_rule": "inspired_only",
        "local_changes_count": 0,
        "watch_for_count": 0,
    }
    violations = check_rubric("path", "category", entry_no_watch)
    assert any("missing Watch For section" in v for v in violations)


def test_check_rubric_strict_requires_min() -> None:
    entry: dict[str, object] = {
        "sync_rule": "PORT",
        "local_changes_count": 1,
        "watch_for_count": 1,
    }
    violations = check_rubric("path", "category", entry)
    assert any("only 1 local-change(s), need 2" in v for v in violations)


def test_collect_registry_paths_includes_russian_copies() -> None:
    data: dict[str, object] = {
        "modified_upstream_files": [],
        "russian_copies": {"exporter/webapp/main_ru.py": "exporter/webapp/main.py"},
        "sbs_copies": {},
        "dps_copies": {},
        "tamil_copies": {},
        "inspired_by_upstream": {},
    }

    paths = collect_registry_paths(data)

    assert ("exporter/webapp/main_ru.py", "russian_copy") in paths


def test_collect_registry_paths_includes_tamil_copies() -> None:
    data: dict[str, object] = {
        "modified_upstream_files": [],
        "russian_copies": {},
        "sbs_copies": {},
        "dps_copies": {},
        "tamil_copies": {"db/tpd/tpd_to_lookup.py": "db/epd/epd_to_lookup.py"},
        "inspired_by_upstream": {},
    }

    paths = collect_registry_paths(data)

    assert ("db/tpd/tpd_to_lookup.py", "tamil_copy") in paths


def test_check_category_alignment_rejects_smd_registry_mismatch() -> None:
    smd_entries: dict[str, dict[str, object]] = {
        "scripts/backup/backup_dps.py": {
            "category": "sbs_copy",
            "sync_rule": "PORT",
            "local_changes_count": 2,
            "watch_for_count": 1,
        }
    }

    violations = check_category_alignment(
        [("scripts/backup/backup_dps.py", "dps_copy")],
        smd_entries,
    )

    assert violations == [
        "  [dps_copy] scripts/backup/backup_dps.py: SMD category is 'sbs_copy'"
    ]
