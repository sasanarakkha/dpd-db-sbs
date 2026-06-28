"""Structural golden-master tests for move_class.sh.

Captured after echo→ask.py conversion, dead-param removal, and
silent-on-success / explicit-failure final summary.
"""

import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "bash" / "move_class.sh"


def test_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    mode = SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR


def test_shebang() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert content.startswith("#!/usr/bin/env bash")


def test_path_variables_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "ANKI_DECKS_DIR" in content
    assert "PALI_CLASS_CSVS_SRC_DIR" in content
    assert "TEMP_PUSH_DEST_DIR" in content
    assert "FILESRV_BASE_DEST_DIR" in content
    assert "FILESRV_CSVS_DEST_DIR" in content


def test_failures_array_declared() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "FAILURES=()" in content


def test_helper_functions_defined() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "safe_copy_file()" in content
    assert "safe_copy_dir_contents()" in content


def test_no_cp_options_parameter() -> None:
    """cp_options was dead code — never used; confirm it's gone."""
    content = SCRIPT.read_text(encoding="utf-8")
    assert "cp_options" not in content


def test_no_echo_statements() -> None:
    """All output must go through tools/ask.py."""
    content = SCRIPT.read_text(encoding="utf-8")
    # Only the shebang line and sub-shell invocations avoid ask.py
    for line in content.splitlines():
        stripped = line.strip()
        # Skip comments, shebang, set flags, empty lines, variable assignments, esac/fi/done
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
        # Catch raw echo used for output
        if "echo" in stripped:
            assert False, f"echo found at line: {stripped}"


def test_ask_used_for_warnings() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Source file" in content
    assert "not found" in content
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
    # Destination directory checks should exit 1
    assert "Destination directory" in content
    assert "exit 1" in content


def test_no_per_file_success_messages() -> None:
    """Success messages are aggregated — no per-file 'Successfully copied'."""
    content = SCRIPT.read_text(encoding="utf-8")
    assert "Successfully copied" not in content


def test_final_summary_present() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "All files copied successfully" in content
    assert "The following copies failed" in content


def test_copy_calls_use_or_true() -> None:
    """|| true prevents set -e from aborting on the first rsync failure."""
    content = SCRIPT.read_text(encoding="utf-8")
    count = content.count("|| true")
    # Every safe_copy_file and safe_copy_dir_contents call should use || true
    assert count >= 21, f"Expected >=21 || true guards, got {count}"


def test_rsync_invocation_present() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "rsync --times --no-perms --no-owner --no-group" in content


def test_rsync_excludes_ds_store() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "--exclude '.DS_Store'" in content or "--exclude .DS_Store" in content


def test_empty_dir_silent() -> None:
    """Empty source directory returns 0 silently — no echo or ask.py."""
    content = SCRIPT.read_text(encoding="utf-8")
    assert "ls -A" in content
    assert "return 0" in content
