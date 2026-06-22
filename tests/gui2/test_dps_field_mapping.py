"""Golden-master test for gui2/dps_field_mapping.py.

Locks in the exact (control, params) structure of every field so the planned
type-hint cleanup and factory-function restructuring cannot silently change
the form configuration consumed by gui2/dps_fields.py.

The fixture intentionally omits the no-op "disabled": False entries that were
dropped from the source: Flet's Control.disabled getter defaults to False when
unset (flet/core/control.py), so the rendered control behavior is unchanged.
The hidden test-only fields' real "disabled": True is preserved.
"""

import json
from pathlib import Path
from typing import Any

from gui2.dps_field_mapping import dps_field_mapping

FIXTURE_PATH = Path(__file__).parent / "test_dps_field_mapping_fixtures.json"


def _serialize(mapping: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for name, spec in mapping.items():
        control = spec["control"]
        params = spec["params"]
        ser_params = {}
        for key, value in params.items():
            if key == "options":
                ser_params[key] = [[opt.key, opt.text] for opt in value]
            elif hasattr(value, "name") and not isinstance(value, (bool, int, str)):
                ser_params[key] = str(value)
            else:
                ser_params[key] = value
        out[name] = {
            "control": f"{control.__module__}.{control.__qualname__}",
            "params": ser_params,
        }
    return out


def test_dps_field_mapping_matches_golden_master() -> None:
    expected = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    actual = _serialize(dps_field_mapping)
    assert actual == expected


def test_dps_field_mapping_has_expected_field_count() -> None:
    assert len(dps_field_mapping) == 61
