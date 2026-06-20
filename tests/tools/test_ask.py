import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "ask.py"
FIXTURES = json.loads(
    (Path(__file__).resolve().parent / "test_ask_fixtures.json").read_text(
        encoding="utf-8"
    )
)


def _run(args: list[str], stdin: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def test_fixtures_match_current_behavior() -> None:
    for name, case in FIXTURES.items():
        proc = _run(case["args"], case["stdin"])
        assert proc.stdout == case["stdout"], name
        assert proc.stderr == case["stderr"], name
        assert proc.returncode == case["returncode"], name
