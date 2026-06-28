"""Golden-master tests for for_release.py — output of the asset manifest."""

import json
import subprocess
import sys
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "test_for_release_fixtures.json"
FIXTURES: dict = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_output_matches_fixture() -> None:
    script = PROJECT_ROOT / "scripts" / "export" / "for_release.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == FIXTURES["output"]
