import pytest
from unittest.mock import patch
from kamma.upstream_sync.scripts.prep_analyzer import PrepAnalyzer

@pytest.fixture
def mock_registry():
    return {
        "modified_upstream_files": [
            {"path": "db/models.py", "discuss": True, "discuss_reason": "Reason"}
        ],
        "russian_copies": {
            "db/families/family_compound_ru.py": "db/families/family_compound.py"
        },
        "sbs_copies": {},
        "inspired_by_upstream": {
            "scripts/bash/make_dpd.sh": {
                "upstream": "scripts/bash/makedict.py",
                "divergence_reason": "Reason"
            }
        },
        "unique_paths": [],
        "no_sync_files": [],
        "skip_sync_patterns": ["tests/"]
    }

@patch("kamma.upstream_sync.scripts.prep_analyzer.load_registry")
@patch("kamma.upstream_sync.scripts.prep_analyzer.get_git_changes")
def test_prep_analyzer_report_generation(mock_git, mock_load, mock_registry, tmp_path):
    mock_load.return_value = mock_registry
    # Simulate some changes
    mock_git.return_value = [
        ("M", "db/models.py"),                # Tracked modified
        ("M", "db/families/family_compound.py"), # Shadow source modified
        ("M", "scripts/bash/makedict.py"),       # Inspired source modified
        ("M", "new_file.py"),                  # Untracked
        ("D", "deleted_file.py"),               # Deleted
        ("M", "tests/ignore_me.py")           # Skipped
    ]
    
    analyzer = PrepAnalyzer(tmp_path)
    # Mocking validate_registry and verify_smd_coverage to avoid complex setup
    with patch("kamma.upstream_sync.scripts.prep_analyzer.validate_registry_core", return_value=[]), \
         patch("kamma.upstream_sync.scripts.prep_analyzer.extract_all_smd_entries", return_value={}), \
         patch("kamma.upstream_sync.scripts.prep_analyzer.collect_registry_paths", return_value=[]):
        
        analyzer.run()
        
    report_path = tmp_path / "prep_report.md"
    assert report_path.exists()
    content = report_path.read_text()
    
    assert "db/models.py" in content
    assert "db/families/family_compound.py" in content
    assert "scripts/bash/makedict.py" in content
    assert "new_file.py" in content
    assert "deleted_file.py" in content
    assert "tests/ignore_me.py" not in content

def test_is_skipped(mock_registry, tmp_path):
    with patch("kamma.upstream_sync.scripts.prep_analyzer.load_registry", return_value=mock_registry):
        analyzer = PrepAnalyzer(tmp_path)
        assert analyzer.is_skipped("tests/test.py")
        assert not analyzer.is_skipped("src/main.py")
