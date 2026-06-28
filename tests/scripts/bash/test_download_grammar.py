"""Structural golden-master tests for download_grammar.sh.

Captured against current code, then verified after echo→ask.py conversion.
"""

import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "bash" / "download_grammar.sh"


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash")


def test_set_e_present() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "set -e" in content


def test_google_sheet_url_present() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "1-iNYm9R86162zFzLd9kraEqNP7DpAFczFMPTVttJSrs" in content


def test_curl_download_command() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "curl -L -A" in content
    assert "export?format=xlsx" in content


def test_xlsx_file_validation() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Zip archive data" in content
    assert "Microsoft Excel 2007+" in content


def test_no_raw_echo_for_output() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith(("echo '", 'echo "')):
            assert False, f"raw echo for output on line: {stripped}"


def test_no_raw_ansi_codes() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "\\033[" not in content


def test_ask_wrapper_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "ask()" in content
    assert "ask.py" in content
    assert "--print" in content


def test_ask_red_for_error() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "ask -c red" in content


def test_ask_green_for_success() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "ask -c green" in content


def test_no_ping_command_internet_check() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "ping -c" not in content


def test_curl_head_internet_check() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "curl -sS --head" in content


def test_temp_directory_handling() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert 'mkdir -p "$REPO_ROOT/temp"' in content or "mkdir -p" in content
