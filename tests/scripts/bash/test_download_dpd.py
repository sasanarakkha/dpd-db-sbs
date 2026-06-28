"""Test structural properties of download_dpd.sh.

Golden-master tests captured against unedited code, then augmented after edit.
"""

import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "bash" / "download_dpd.sh"


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash")


def test_DPD_links_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "DPD_links" in content
    assert content.count("digitalpalidictionary/dpd-db/releases") == 7


def test_SBS_links_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "DPD_SBS_links" in content
    assert content.count("dpd+sbs-goldendict") == 1


def test_RU_links_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "DPD_RU_links" in content
    assert content.count("ru-dpd-") >= 3


def test_commented_sbs_block_in_ask_format() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert '# ask_and_run "Download SBS files?"' in content


def test_commented_ru_block_in_ask_format() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert '# ask_and_run "Download RU files?"' in content


def test_ask_and_run_function_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "ask_and_run()" in content
    assert "tools/ask.py" in content


def test_no_raw_ansi_codes() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "\\033[" not in content


def test_curl_download_command() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "curl -q -# -L -O" in content


def test_ask_print_for_status() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "ask.py --print" in content


def test_ask_print_red_for_error() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "ask.py --print -c red" in content
    assert "Error: No internet connection" in content


def test_no_raw_echo_for_output() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith(("echo '", 'echo "')):
            assert False, f"raw echo for output on line: {stripped}"
