"""Golden-master tests for stage_study_tools.sh.

Runtime tests: create source files, run the script, verify output matches
the captured fixture. Works identically for both safe_copy_file and
data-mapping implementations.
"""

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "bash" / "stage_study_tools.sh"
FIXTURE_PATH = (
    REPO_ROOT / "tests" / "scripts" / "bash" / "test_stage_study_tools_fixtures.json"
)

# Source files the script expects — (subdir, filename) pairs
SOURCE_FILES: list[tuple[str, str]] = [
    ("anki_csvs", "anki_patimokkha.csv"),
    ("anki_csvs", "anki_dps.csv"),
    ("anki_csvs", "anki_sbs.csv"),
    ("anki_csvs", "anki_dhp.csv"),
    ("anki_csvs", "anki_parittas.csv"),
    ("anki_csvs", "anki_vibhanga.csv"),
    ("anki_csvs", "sbs_rus.csv"),
    ("anki_csvs/pali_class", "class_all.csv"),
    ("anki_csvs/pali_class", "phonetic_class.csv"),
    ("anki_csvs/pali_class", "roots_class.csv"),
    ("anki_csvs/pali_class", "suttas_class.csv"),
    ("anki_csvs/pali_class", "common_roots.csv"),
    ("anki_csvs/pali_class", "ru_common_roots.csv"),
    ("anki_csvs/pali_class/grammar", "cl_sum_abbr.csv"),
    ("anki_csvs/pali_class/grammar", "cl_sum_gramm.csv"),
    ("anki_csvs/pali_class/grammar", "cl_sum_sandhi.csv"),
    ("anki_csvs/pali_class/grammar", "ru_cl_sum_gramm.csv"),
    ("anki_decks", "pali_patimokkha_word_by_word.apkg"),
    ("anki_decks", "pali_slovar.apkg"),
    ("anki_decks", "sbs_pali_english_vocab.apkg"),
    ("anki_decks", "pali_dhp_vocab.apkg"),
    ("anki_decks", "pali_parittas.apkg"),
    ("anki_decks", "pali_bhikkhu_vibhanga.apkg"),
    ("anki_decks", "grammar_pali_class.apkg"),
    ("anki_decks", "phonetic_changes_pali_class.apkg"),
    ("anki_decks", "roots_pali_class.apkg"),
    ("anki_decks", "suttas_advanced_pali_class.apkg"),
    ("anki_decks", "vocab_pali_class.apkg"),
    ("anki_decks", "common_roots.apkg"),
]


@pytest.fixture(scope="module")
def fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _create_source_files(root: Path) -> None:
    for subdir, filename in SOURCE_FILES:
        parent = root / subdir
        parent.mkdir(parents=True, exist_ok=True)
        (parent / filename).touch()


def _count_files(root: Path) -> set[str]:
    return {f.name for f in root.iterdir() if f.is_file()}


def test_script_exists() -> None:
    assert SCRIPT.exists()


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash")


def test_produces_correct_files(fixture: dict) -> None:
    """Runtime test: create source files, run script, verify output matches fixture."""
    # Create source directory structure and files
    _create_source_files(REPO_ROOT / "temp")

    try:
        # Run the script
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Script failed:\n{result.stderr}"

        # Check output files match fixture
        dest = REPO_ROOT / "temp" / "study_tools_release"
        actual_files = _count_files(dest)
        expected_files = set(fixture["destination_files"])
        assert actual_files == expected_files, (
            f"Missing: {expected_files - actual_files}\n"
            f"Unexpected: {actual_files - expected_files}"
        )
        assert len(actual_files) == fixture["count"]
    finally:
        # Clean up
        for subdir, _ in SOURCE_FILES:
            target = REPO_ROOT / "temp" / subdir
            if target.exists():
                subprocess.run(["rm", "-rf", str(target)], check=False)
        dest = REPO_ROOT / "temp" / "study_tools_release"
        if dest.exists():
            subprocess.run(["rm", "-rf", str(dest)], check=False)


def test_handles_missing_source_gracefully() -> None:
    """Script should warn but not fail when a source file is missing."""
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, f"Script failed on missing sources:\n{result.stderr}"
    assert "Warning" in result.stdout or "Warning" in result.stderr


def test_no_exit_on_missing_source() -> None:
    """Missing source files should produce a warning, not exit 1."""
    content = SCRIPT.read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "exit 1" in stripped and ("safe_copy_file" in stripped or "cp " in stripped):
            pytest.fail(f"exit 1 in copy-related line: {stripped}")
