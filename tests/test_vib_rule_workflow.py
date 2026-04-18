"""Tests for the Vibhanga rule workflow: word extraction and -pi/-ca clitic handling."""

from io import StringIO
from unittest.mock import MagicMock, patch

from tools.cst_sc_text_sets import make_cst_text_list_from_file
from scripts.change_in_db.copy_examples import update_column_for_some_criteria
from scripts.change_in_db.vib_rule_workflow import (
    accept_pasted_text,
    run_rule,
    get_text_from_clipboard,
    collect_tty_pasted_text,
    normalize_pat_file,
    strip_variant_readings,
    suggest_next_pat_file,
    suggest_next_source,
    save_progress,
    load_progress,
)


def test_clitics_not_skipped_from_file(tmp_path):
    """Joined forms and individual parts of hyphenated clitic words must all appear in result."""
    text_file = tmp_path / "text.txt"
    text_file.write_text("saṃgho-pi dhammo-ca bhikkhu-pi nāgo", encoding="utf-8")

    dpspth = MagicMock()
    dpspth.text_to_add_path = text_file

    result = make_cst_text_list_from_file(dpspth)

    # Joined compound forms (hyphen removed) must be present
    assert "saṃghopi" in result, f"'saṃghopi' missing: {result}"
    assert "dhammoca" in result, f"'dhammoca' missing: {result}"
    assert "bhikkhupi" in result, f"'bhikkhupi' missing: {result}"

    # Individual parts must also be present
    assert "saṃgho" in result, f"'saṃgho' missing: {result}"
    assert "pi" in result, f"'pi' missing: {result}"
    assert "dhammo" in result, f"'dhammo' missing: {result}"
    assert "ca" in result, f"'ca' missing: {result}"

    # Plain word with no hyphen must still be present
    assert "nāgo" in result, f"'nāgo' missing: {result}"


def test_clitics_order_in_result(tmp_path):
    """Joined form must appear before its individual parts in the result list."""
    text_file = tmp_path / "text.txt"
    text_file.write_text("saṃgho-pi", encoding="utf-8")

    dpspth = MagicMock()
    dpspth.text_to_add_path = text_file

    result = make_cst_text_list_from_file(dpspth)

    joined_idx = result.index("saṃghopi")
    part1_idx = result.index("saṃgho")
    part2_idx = result.index("pi")

    assert joined_idx < part1_idx, "joined form should precede part1"
    assert part1_idx < part2_idx, "part1 should precede part2"


@patch("scripts.change_in_db.copy_examples.db_session")
@patch("scripts.change_in_db.copy_examples.console")
def test_dry_run_does_not_commit(mock_console, mock_db_session):
    """Calling update_column_for_some_criteria with dry_run=True must not call db_session.commit()."""
    # Setup mock return values for queries to avoid errors during iteration
    mock_db_session.query.return_value.options.return_value.outerjoin.return_value.filter.return_value.all.return_value = []

    update_column_for_some_criteria(
        source_value="VIN2.5.6.10",
        column_to_update="",
        value_to_update="vib",
        modifier_column_to_copy="vib",
        dry_run=True,
    )

    # Verify commit was NOT called
    mock_db_session.commit.assert_not_called()

    # Verify dry run message was printed
    mock_console.print.assert_any_call(
        "[bold yellow]DRY RUN — no changes written to database[/bold yellow]"
    )


@patch("scripts.change_in_db.copy_examples.db_session")
@patch("scripts.change_in_db.copy_examples.console")
def test_dry_run_commits_by_default(mock_console, mock_db_session):
    """Calling update_column_for_some_criteria with dry_run=False (default) must call db_session.commit()."""
    # Setup mock return values for queries to avoid errors during iteration
    mock_db_session.query.return_value.options.return_value.outerjoin.return_value.filter.return_value.all.return_value = []

    update_column_for_some_criteria(
        source_value="VIN2.5.6.10",
        column_to_update="",
        value_to_update="vib",
        modifier_column_to_copy="vib",
        dry_run=False,
    )

    # Verify commit WAS called
    mock_db_session.commit.assert_called_once()


def test_strip_variant_readings():
    """Text inside curly braces must be removed."""
    input_text = "dhammo-pi {variant reading here} vinayo-ca"
    expected = "dhammo-pi  vinayo-ca"
    assert strip_variant_readings(input_text) == expected


def test_collect_tty_pasted_text_stops_at_end_marker():
    """TTY multiline input should stop at a sentinel line and keep previous text."""
    stdin = StringIO("line 1\nline 2\n__END__\nignored\n")

    assert collect_tty_pasted_text(stdin) == "line 1\nline 2\n"


def test_accept_pasted_text_reads_non_tty_stdin(monkeypatch):
    """Non-TTY stdin should still read the full stream unchanged."""
    stdin = StringIO("long line 1\nlong line 2\n")
    monkeypatch.setattr(stdin, "isatty", lambda: False)

    assert accept_pasted_text(stdin) == "long line 1\nlong line 2\n"


@patch("scripts.change_in_db.vib_rule_workflow.subprocess.run")
def test_get_text_from_clipboard_reads_pbpaste(mock_run):
    """Clipboard import should return pbpaste stdout."""
    mock_run.return_value.stdout = "clipboard text"

    assert get_text_from_clipboard() == "clipboard text"
    mock_run.assert_called_once()


def test_accept_pasted_text_reads_from_clipboard_choice(monkeypatch):
    """TTY input should read from clipboard by default on Enter."""
    stdin = StringIO("\n")
    monkeypatch.setattr(stdin, "isatty", lambda: True)
    monkeypatch.setattr(
        "scripts.change_in_db.vib_rule_workflow.get_text_from_clipboard",
        lambda: "from clipboard",
    )

    assert accept_pasted_text(stdin) == "from clipboard"


def test_accept_pasted_text_reads_from_terminal_choice(monkeypatch):
    """TTY input should still allow explicit terminal paste mode."""
    stdin = StringIO("paste\nline 1\n__END__\n")
    monkeypatch.setattr(stdin, "isatty", lambda: True)

    assert accept_pasted_text(stdin) == "line 1\n"


@patch("scripts.change_in_db.vib_rule_workflow.update_column_for_some_criteria")
@patch(
    "scripts.change_in_db.vib_rule_workflow.dps_make_words_to_add_list_from_text_no_field"
)
@patch("scripts.change_in_db.vib_rule_workflow.save_progress")
@patch("scripts.change_in_db.vib_rule_workflow.pr")
def test_run_rule_prints_saved_content_once(
    mock_pr,
    mock_save_progress,
    mock_extract_words,
    mock_update_column,
    monkeypatch,
    tmp_path,
):
    """Save step should print the saved content for the PAT file once."""
    pat_file = tmp_path / "pc64.txt"
    text_file = tmp_path / "text.txt"
    pth = MagicMock()
    dpspth = MagicMock()
    dpspth.text_to_add_path = text_file
    mock_extract_words.return_value = []
    monkeypatch.setattr(
        "scripts.change_in_db.vib_rule_workflow.accept_pasted_text",
        lambda: "line 1\nline 2\n",
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": "")

    result = run_rule("VIN2.5.6.10", str(pat_file), pth, dpspth, MagicMock())

    assert result is True
    assert pat_file.read_text() == "line 1\nline 2"
    assert text_file.read_text() == "line 1\nline 2"
    mock_pr.yes.assert_any_call(f"Saved to {pat_file}:")
    mock_pr.cyan.assert_any_call("line 1\nline 2")
    assert mock_pr.cyan.call_args_list.count((("line 1\nline 2",), {})) == 1
    mock_extract_words.assert_called_once_with(
        pth, dpspth, mock_extract_words.call_args.args[2], ["vib_source", "pat_source"]
    )


def test_suggest_next_pat_file_pc():
    """Suggest pc61.txt after pc60.txt."""
    assert suggest_next_pat_file("misc/pat/pc60.txt") == "misc/pat/pc61.txt"


def test_suggest_next_pat_file_np():
    """Suggest np26.txt after np25.txt."""
    assert suggest_next_pat_file("misc/pat/np25.txt") == "misc/pat/np26.txt"


def test_suggest_next_source_increments_rule():
    """Increment the last rule number component."""
    assert suggest_next_source("VIN2.5.7.2") == "VIN2.5.7.3"


def test_normalize_pat_file_bare_stem():
    """Bare stem like 'pc64' expands to full path."""
    assert normalize_pat_file("pc64") == "misc/pat/pc64.txt"


def test_normalize_pat_file_full_path_unchanged():
    """Full path passthrough — no double-wrapping."""
    assert normalize_pat_file("misc/pat/pc64.txt") == "misc/pat/pc64.txt"


def test_suggest_next_source_at_vagga_end():
    """Still increments — user manually overrides for vagga transitions."""
    assert suggest_next_source("VIN2.5.6.10") == "VIN2.5.6.11"


def test_save_and_load_progress(tmp_path, monkeypatch):
    """Progress must be saved to and loaded from JSON."""
    progress_file = tmp_path / "vib_progress.json"
    monkeypatch.setattr(
        "scripts.change_in_db.vib_rule_workflow.VIB_PROGRESS_PATH", progress_file
    )

    save_progress("VIN2.5.6.10", "misc/pat/pc60.txt")
    loaded = load_progress()

    assert loaded == {
        "last_source": "VIN2.5.6.10",
        "last_pat_file": "misc/pat/pc60.txt",
        "complete": True,
    }
