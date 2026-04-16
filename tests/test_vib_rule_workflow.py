"""Tests for the Vibhanga rule workflow: word extraction and -pi/-ca clitic handling."""

from unittest.mock import MagicMock, patch

from tools.cst_sc_text_sets import make_cst_text_list_from_file
from scripts.change_in_db.copy_examples import update_column_for_some_criteria
from scripts.change_in_db.vib_rule_workflow import (
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
