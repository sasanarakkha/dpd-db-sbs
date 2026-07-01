"""Verify SMD scaffold generation preserves registry category names."""

from unittest.mock import patch

from kamma.upstream_sync.scripts import gen_smd_scaffold
from kamma.upstream_sync.scripts.gen_smd_scaffold import make_stub
from kamma.upstream_sync.scripts.sync_schema import RegistryData


def test_make_stub_preserves_explicit_strict_shadow_category() -> None:
    output = make_stub("db/backup_tsv/backup_dps.py", "dps_copies")

    assert "- **Category**: dps_copies" in output
    assert "- **Sync Rule**: PORT" in output


def test_main_emits_dps_and_tamil_categories(capsys) -> None:
    registry = RegistryData(
        modified_upstream_files=[],
        russian_copies={},
        sbs_copies={},
        dps_copies={
            "db/backup_tsv/backup_dps.py": "db/backup_tsv/backup_dpd_headwords_and_roots.py"
        },
        tamil_copies={"db/tpd/tpd_to_lookup.py": "db/epd/epd_to_lookup.py"},
        inspired_by_upstream={},
        unique_paths=[],
        no_sync_files=[],
        skip_sync_patterns=[],
    )

    with patch.object(gen_smd_scaffold, "load_registry", return_value=registry):
        gen_smd_scaffold.main()

    output = capsys.readouterr().out
    assert "**File**: `db/backup_tsv/backup_dps.py`" in output
    assert "- **Category**: dps_copies" in output
    assert "**File**: `db/tpd/tpd_to_lookup.py`" in output
    assert "- **Category**: tamil_copies" in output
