"""Golden-master tests for docs_check_ru.py."""

import json
from pathlib import Path

from scripts.rus_exporter.docs_check_ru import check_file

FIXTURE_PATH = Path(__file__).parent / "test_docs_check_ru_fixtures.json"


def _relative_broken(broken: list[str], file_path: Path) -> list[str]:
    """Strip the temp-absolute file path prefix from broken image entries."""
    prefix = f"{file_path}: "
    return [item.removeprefix(prefix) for item in broken]


def test_check_file_on_real_file():
    """check_file produces stable output on a real docs_rus markdown file."""
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    input_text: str = fixture["input_text"]
    expected_output: str = fixture["output_text"]
    expected_broken: list[str] = fixture["broken_relative"]

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        copy = tmp_path / "dpd_rus.md"
        copy.write_text(input_text, encoding="utf-8")

        broken = check_file(copy)

        assert _relative_broken(broken, copy) == expected_broken
        assert copy.read_text(encoding="utf-8") == expected_output
