"""Tests for SBS Anki backup fail-closed behavior."""

from unittest.mock import MagicMock, patch

from scripts.export import sbs_anki_updater


def test_backup_anki_db_returns_false_when_copy_fails() -> None:
    """Backup failure should be reported to the caller."""
    with (
        patch(
            "scripts.export.sbs_anki_updater.config_read",
            side_effect=["/missing/collection.anki2", "/backup"],
        ),
        patch("scripts.export.sbs_anki_updater.os.makedirs"),
        patch(
            "scripts.export.sbs_anki_updater.shutil.copy2",
            side_effect=FileNotFoundError("missing collection"),
        ),
    ):
        assert sbs_anki_updater.backup_anki_db() is False


def test_run_pipeline_aborts_before_collection_update_when_backup_fails() -> None:
    """The updater must not open or mutate the collection after backup failure."""
    db_session = MagicMock()
    db_session.query.return_value.options.return_value.all.return_value = []

    with (
        patch(
            "scripts.export.sbs_anki_updater.get_db_session",
            return_value=db_session,
        ),
        patch("scripts.export.sbs_anki_updater.recalculate_all_sbs_indices"),
        patch("scripts.export.sbs_anki_updater.backup_anki_db", return_value=False),
        patch("scripts.export.sbs_anki_updater.setup_anki_updater") as setup_anki,
    ):
        sbs_anki_updater.run_pipeline(skip_collection=False)

    setup_anki.assert_not_called()
