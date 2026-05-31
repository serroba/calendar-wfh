from datetime import date, timedelta

import holidays as hols


def is_business_day(d: date, state: str = "NSW") -> bool:
    if d.weekday() >= 5:
        return False
    return d not in hols.country_holidays("AU", subdiv=state, years=d.year)


def expand_weekdays(
    start: date,
    end: date,
    weekdays: list[int] | None = None,
    state: str = "NSW",
) -> list[date]:
    """Return all days in [start, end] matching weekdays, excluding public holidays.

    weekdays: list of ints 0=Mon … 6=Sun; None means Mon–Fri (0–4).
    """
    if weekdays is None:
        weekdays = [0, 1, 2, 3, 4]
    years = set(range(start.year, end.year + 1))
    au_holidays = hols.country_holidays("AU", subdiv=state, years=years)
    result = []
    current = start
    while current <= end:
        if current.weekday() in weekdays and current not in au_holidays:
            result.append(current)
        current += timedelta(days=1)
    return result


def financial_year_for(d: date) -> str:
    start_year = d.year if d.month >= 7 else d.year - 1
    return f"FY{start_year}-{str(start_year + 1)[2:]}"


def fy_bounds(fy: str) -> tuple[date, date]:
    """Return (start, end) for a financial year label like 'FY2025-26'."""
    year = int(fy[2:6])
    return date(year, 7, 1), date(year + 1, 6, 30)
