"""Guard that stops AI runs during DeepSeek peak pricing hours (UTC, Mon-Fri, excluding Chinese public holidays)."""

import sys
from datetime import UTC, date, datetime, timedelta

from tools.printer import printer as pr

# Chinese public holidays per year, inclusive (start, end) date ranges.
# 2027: 国办发明电〔2026〕10号 (published 2026-11-05). Make-up workdays (all weekends)
# stay off-peak because DeepSeek's rule names Monday through Friday only.
# 2026: only the dates after 2026-11-16 matter for this skill; none remain, so the list
# is empty (earlier 2026 holidays are intentionally not recorded).
CN_HOLIDAYS: dict[int, list[tuple[date, date]]] = {
    2026: [],
    2027: [
        (date(2027, 1, 1), date(2027, 1, 3)),
        (date(2027, 2, 5), date(2027, 2, 13)),
        (date(2027, 4, 3), date(2027, 4, 5)),
        (date(2027, 5, 1), date(2027, 5, 5)),
        (date(2027, 6, 9), date(2027, 6, 9)),
        (date(2027, 9, 15), date(2027, 9, 15)),
        (date(2027, 10, 1), date(2027, 10, 7)),
    ],
}

# Peak windows as [start_hour, end_hour) UTC.
PEAK_WINDOWS: list[tuple[int, int]] = [(1, 4), (6, 10)]


def _is_holiday(day: date) -> bool:
    return any(start <= day <= end for start, end in CN_HOLIDAYS.get(day.year, []))


def is_deepseek_peak(now_utc: datetime) -> bool:
    """Return True when DeepSeek charges full price at this UTC moment."""
    now_utc = now_utc.astimezone(UTC)
    if now_utc.weekday() >= 5 or _is_holiday(now_utc.date()):
        return False
    return any(start <= now_utc.hour < end for start, end in PEAK_WINDOWS)


def _next_off_peak_start(now_utc: datetime) -> datetime:
    probe = now_utc.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    for _ in range(24 * 14):
        probe += timedelta(hours=1)
        if not is_deepseek_peak(probe):
            return probe
    return probe


def require_offpeak(allow_peak: bool, now_utc: datetime | None = None) -> None:
    """Exit 1 when the holiday table lacks the current year, or when in peak without allow_peak."""
    now_utc = now_utc or datetime.now(UTC)
    year = now_utc.astimezone(UTC).year
    if year not in CN_HOLIDAYS:
        pr.red(f"BLOCKED: no Chinese public holiday dates recorded for {year}.")
        pr.red(
            "Add them to CN_HOLIDAYS in kamma/translate/scripts/offpeak.py "
            f"(source: 国务院办公厅关于{year}年部分节假日安排的通知, usually published early November)."
        )
        sys.exit(1)
    if is_deepseek_peak(now_utc) and not allow_peak:
        start = _next_off_peak_start(now_utc)
        pr.red(
            "BLOCKED: DeepSeek peak hours (full price). Use --allow-peak to override."
        )
        pr.red(f"Next off-peak start: {start:%Y-%m-%d %H:%M} UTC")
        sys.exit(1)
