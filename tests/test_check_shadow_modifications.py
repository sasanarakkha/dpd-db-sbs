"""Verify shadow-modification checks include every strict-shadow category."""

from kamma.upstream_sync.scripts.registry_helper import get_shadow_mappings_by_category


def test_get_shadow_mappings_by_category_includes_dps() -> None:
    data = {
        "russian_copies": {"a_ru.py": "a.py"},
        "sbs_copies": {"a_sbs.py": "a.py"},
        "dps_copies": {"a_dps.py": "a.py"},
    }

    mappings = get_shadow_mappings_by_category(data)

    assert mappings["russian_copy"] == {"a_ru.py": "a.py"}
    assert mappings["sbs_copy"] == {"a_sbs.py": "a.py"}
    assert mappings["dps_copy"] == {"a_dps.py": "a.py"}
