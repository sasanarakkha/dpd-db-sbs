"""Verify example bolding helpers used by the analysis pipeline."""

from unittest.mock import MagicMock

from exporter.analysis.example_bolding import bold_component_in_token


def _mock_session() -> MagicMock:
    """Return a mock DB session where all headword queries return None."""
    mock = MagicMock()
    mock.query.return_value.filter_by.return_value.first.return_value = None
    return mock


def test_bold_component_in_token_first_component() -> None:
    """First component is bolded precisely."""
    result = bold_component_in_token(
        "micchādiṭṭhisamādānā",
        "micchā",
        99998,
        _mock_session(),
        is_first_component=True,
    )
    assert result == "<b>micchā</b>diṭṭhisamādānā"


def test_bold_component_in_token_middle_component() -> None:
    """Component with a suffix in the token is bolded precisely, not to end.

    Covers the real DHP316 case: diṭṭhi is last in sub-compound micchādiṭṭhi
    but the verse token is micchādiṭṭhisamādānā — suffix exists, so bold only diṭṭhi.
    """
    result = bold_component_in_token(
        "micchādiṭṭhisamādānā",
        "diṭṭhi",
        32479,
        _mock_session(),
        is_first_component=False,
    )
    assert result == "micchā<b>diṭṭhi</b>samādānā"


def test_bold_component_in_token_last_component() -> None:
    """Component at end of token is bolded to end."""
    result = bold_component_in_token(
        "micchādiṭṭhisamādānā",
        "samādānā",
        99999,
        _mock_session(),
        is_first_component=False,
    )
    assert result == "micchādiṭṭhi<b>samādānā</b>"
