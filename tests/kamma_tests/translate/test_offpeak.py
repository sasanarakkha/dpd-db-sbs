"""Tests for the DeepSeek off-peak guard used by the translate skill."""

from datetime import UTC, datetime

import pytest

from kamma.translate.scripts.offpeak import is_deepseek_peak, require_offpeak


def _utc(y: int, m: int, d: int, h: int) -> datetime:
    return datetime(y, m, d, h, 0, tzinfo=UTC)


def test_weekday_morning_is_peak() -> None:
    assert is_deepseek_peak(_utc(2027, 3, 3, 2))  # Wed 02:00


def test_weekday_gap_hour_is_off_peak() -> None:
    assert not is_deepseek_peak(_utc(2027, 3, 3, 5))  # Wed 05:00


def test_second_peak_window_is_peak() -> None:
    assert is_deepseek_peak(_utc(2027, 3, 3, 8))  # Wed 08:00
    assert not is_deepseek_peak(_utc(2027, 3, 3, 10))  # window end is exclusive


def test_weekend_is_off_peak() -> None:
    assert not is_deepseek_peak(_utc(2027, 3, 6, 2))  # Sat 02:00


def test_holiday_weekday_is_off_peak() -> None:
    assert not is_deepseek_peak(_utc(2027, 2, 8, 2))  # Mon in Spring Festival


def test_makeup_workday_stays_off_peak() -> None:
    assert not is_deepseek_peak(_utc(2027, 1, 31, 2))  # make-up Sunday


def test_missing_holiday_year_blocks_even_with_allow_peak() -> None:
    with pytest.raises(SystemExit) as exc:
        require_offpeak(True, now_utc=_utc(2028, 3, 1, 5))
    assert exc.value.code == 1


def test_peak_blocks_without_allow_peak() -> None:
    with pytest.raises(SystemExit) as exc:
        require_offpeak(False, now_utc=_utc(2027, 3, 3, 2))
    assert exc.value.code == 1


def test_peak_with_allow_peak_returns_none() -> None:
    assert require_offpeak(True, now_utc=_utc(2027, 3, 3, 2)) is None


def test_off_peak_returns_none() -> None:
    assert require_offpeak(False, now_utc=_utc(2027, 3, 3, 5)) is None


def test_current_2026_year_is_not_blocked() -> None:
    assert require_offpeak(False, now_utc=_utc(2026, 11, 17, 5)) is None  # Tue 05:00
