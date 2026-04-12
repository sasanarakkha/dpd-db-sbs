import json
import subprocess
from pathlib import Path
import pytest

def test_tpr_index_check_not_last(tmp_path):
    """RU entry exists but is not last."""
    submodule_path = tmp_path / "resources" / "tpr_downloads"
    json_path = submodule_path / "download_source_files" / "download_list.json"
    json_path.parent.mkdir(parents=True)
    
    mock_data = [
        {"name": "Other 1"},
        {"name": "DPD with Russian"},
        {"name": "Other 2"}
    ]
    with open(json_path, "w") as f:
        json.dump(mock_data, f)
    
    script_path = Path("scripts/rus_exporter/check_tpr_download_index.py")
    result = subprocess.run(["python3", str(script_path), "--test-path", str(submodule_path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert "at 1" in result.stdout
    assert "last is 2" in result.stdout
    assert "Run exporter/tpr/tpr_exporter_ru.py to fix" in result.stdout

def test_tpr_index_check_is_last(tmp_path):
    """RU entry is last."""
    submodule_path = tmp_path / "resources" / "tpr_downloads"
    json_path = submodule_path / "download_source_files" / "download_list.json"
    json_path.parent.mkdir(parents=True)
    
    mock_data = [
        {"name": "Other 1"},
        {"name": "DPD with Russian"}
    ]
    with open(json_path, "w") as f:
        json.dump(mock_data, f)
        
    script_path = Path("scripts/rus_exporter/check_tpr_download_index.py")
    result = subprocess.run(["python3", str(script_path), "--test-path", str(submodule_path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert "index 1" in result.stdout
    assert "OK" in result.stdout

def test_tpr_index_check_absent(tmp_path):
    """RU entry absent."""
    submodule_path = tmp_path / "resources" / "tpr_downloads"
    json_path = submodule_path / "download_source_files" / "download_list.json"
    json_path.parent.mkdir(parents=True)
    
    mock_data = [
        {"name": "Other 1"},
        {"name": "Other 2"}
    ]
    with open(json_path, "w") as f:
        json.dump(mock_data, f)
        
    script_path = Path("scripts/rus_exporter/check_tpr_download_index.py")
    result = subprocess.run(["python3", str(script_path), "--test-path", str(submodule_path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert "not found" in result.stdout
