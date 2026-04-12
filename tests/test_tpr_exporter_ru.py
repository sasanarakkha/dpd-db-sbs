import pytest
from exporter.tpr.tpr_exporter_ru import update_tpr_download_list

def test_update_tpr_download_list_not_last():
    """List with RU entry at non-last position -> after fix, RU entry is at end."""
    download_list = [
        {"name": "Other 1"},
        {"name": "DPD with Russian"},
        {"name": "Other 2"}
    ]
    info = {"name": "DPD with Russian", "data": "new"}
    updated_list = update_tpr_download_list(download_list, info)
    
    assert len(updated_list) == 3
    assert updated_list[-1]["name"] == "DPD with Russian"
    assert updated_list[-1]["data"] == "new"
    # Ensure "Other 1" and "Other 2" are still there
    assert updated_list[0]["name"] == "Other 1"
    assert updated_list[1]["name"] == "Other 2"

def test_update_tpr_download_list_absent():
    """List with no RU entry -> RU entry appended at end."""
    download_list = [
        {"name": "Other 1"},
        {"name": "Other 2"}
    ]
    info = {"name": "DPD with Russian", "data": "new"}
    updated_list = update_tpr_download_list(download_list, info)
    
    assert len(updated_list) == 3
    assert updated_list[-1]["name"] == "DPD with Russian"
    assert updated_list[-1]["data"] == "new"

def test_update_tpr_download_list_is_last():
    """List with RU entry already at end -> still at end, no duplicate."""
    download_list = [
        {"name": "Other 1"},
        {"name": "DPD with Russian"}
    ]
    info = {"name": "DPD with Russian", "data": "new"}
    updated_list = update_tpr_download_list(download_list, info)
    
    assert len(updated_list) == 2
    assert updated_list[-1]["name"] == "DPD with Russian"
    assert updated_list[-1]["data"] == "new"
