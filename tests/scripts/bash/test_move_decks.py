"""Structural golden-master tests for move_decks.sh.

Follows same pattern as test_move_class.py — identical safe_copy_file
refactoring (dead param removed, echo→ask.py, silent-on-success, FAILURES).
"""

import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "bash" / "move_decks.sh"


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/bin/bash")


def test_path_variables_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "ANKI_CSVS_SRC_DIR" in content
    assert "ANKI_DECKS_DIR" in content
    assert "FILESRV_DEST_BASE_DIR" in content
    assert "FILESRV_PAT_DIR" in content
    assert "TEMP_PUSH_DEST_DIR" in content


def test_failures_array_declared() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "FAILURES=()" in content


def test_helper_function_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "safe_copy_file()" in content


def test_no_cp_options_parameter() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "cp_options" not in content


def test_no_echo_statements() -> None:
    """All output must go through tools/ask.py."""
    content = SCRIPT.read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith(
            (
                "#",
                "set ",
                "#!/",
                "local ",
                "return ",
                "exit ",
                "if",
                "elif",
                "else",
                "then",
                "fi",
                "do",
                "done",
                "}",
                "esac",
                ";;",
                "in",
                "for ",
                "while ",
                "case ",
            )
        ):
            continue
        if "=" in stripped and not stripped.startswith("uv "):
            continue
        if stripped.startswith(("]]", "[")):
            continue
        if stripped in ("|| true", "|| true;"):
            continue
        if "echo" in stripped:
            assert False, f"echo found at line: {stripped}"


def test_ask_used_for_warnings() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Warning" in content
    assert "tools/ask.py" in content
    assert "yellow" in content


def test_ask_used_for_errors() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Error:" in content
    assert "Failed to copy" in content
    assert "tools/ask.py" in content
    assert "-c red" in content


def test_dest_dir_check_exits() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Destination directory" in content
    assert "exit 1" in content


def test_no_per_file_success_messages() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Successfully copied" not in content


def test_final_summary_present() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "All files copied successfully" in content
    assert "The following copies failed" in content


def test_copy_calls_use_or_true() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    count = content.count("|| true")
    assert count >= 27, f"Expected >=27 || true guards, got {count}"


def test_commented_out_copies_removed() -> None:
    """Commented-out safe_copy_file calls from original are dead code — removed."""
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Ñāṇatiloka" not in content
    assert "reading-common-pali-phrases" not in content


def test_no_decorative_end_output() -> None:
    """Old decorative banners replaced by the single final summary."""
    content = SCRIPT.read_text(encoding="utf-8")
    assert "the job is done" not in content
    assert "moved for share" not in content
