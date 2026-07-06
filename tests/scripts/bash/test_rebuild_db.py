"""Structural golden-master tests for rebuild_db.sh.

Captured against unedited code, then augmented after echo→ask.py conversion.
"""

import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "bash" / "rebuild_db.sh"


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


def test_git_checkout_sbs_ru() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "git checkout sbs-ru" in content


def test_calls_backup_dps() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "db/backup_tsv/backup_dps.py" in content


def test_calls_additions_processor() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "scripts/work_with_csv/additions_processor.py" in content


def test_calls_db_rebuild_from_tsv() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "scripts/build/db_rebuild_from_tsv.py" in content


def test_calls_db_rebuild_from_tsv_dps() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "scripts/build/db_rebuild_from_tsv_dps.py" in content


def test_calls_generate_components() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "scripts/bash/generate_components.sh" in content


def test_calls_add_combined_view() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "scripts/export/add_combined_view.py" in content


def test_calls_apply_all_corrections() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "scripts/change_in_db/apply_all_corrections.py" in content


def test_calls_update_yojana_km() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "scripts/change_in_db/update_yojana_km.py" in content


def test_calls_goldendict_main_sbs() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "exporter/goldendict/main_sbs.py" in content


def test_config_update_call_uses_uv() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "config_update" in content
    assert "uv run python3" in content
    assert "regenerate" in content
    assert "db_rebuild" in content


def test_ask_used_for_all_prompts() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.count("uv run tools/ask.py") == 3


def test_no_while_read_loops() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "while true; do" not in content
    assert "read -n 1 -s" not in content


def test_no_raw_ansi_codes() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "\\033[" not in content


def test_no_commented_out_make_dpd() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Make dpd?" not in content


def test_no_echo_statements_for_output() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("echo"):
            assert False, f"echo found on line: {stripped}"


def test_no_abort_by_user_message() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Aborted by user." not in content
