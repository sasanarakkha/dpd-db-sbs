"""Verify smoke-test helpers keep config mutations isolated from config.ini."""

import importlib.util
from pathlib import Path
from types import ModuleType


def load_smoke_test_sync() -> ModuleType:
    """Load the smoke test script as a testable module."""
    script_path = Path("tests/smoke_test_sync.py")
    spec = importlib.util.spec_from_file_location(
        "smoke_test_sync_script",
        script_path,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_isolated_config_keeps_real_config_file_unchanged() -> None:
    smoke = load_smoke_test_sync()
    config_path = Path("config.ini")
    before = config_path.read_bytes()

    with smoke.isolated_config():
        smoke.configger.config_update("dictionary", "data_limit", "98765", silent=True)
        assert smoke.configger.config_read("dictionary", "data_limit") == "98765"

    after = config_path.read_bytes()
    assert after == before
