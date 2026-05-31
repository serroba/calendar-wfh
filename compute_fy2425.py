"""
FY2024-25 WFH computation and record generation.

Usage:
    uv run python compute_fy2425.py           # dry-run: show monthly breakdown
    uv run python compute_fy2425.py --write   # write records.json + CSV
"""

import argparse
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from wfh.calendar import expand_weekdays, is_business_day
from wfh.records import add, save
from wfh.report import to_csv

HOURS = 8.5  # 9:30am – 6pm
STATE = "NSW"
FY_START = date(2024, 7, 1)
FY_END = date(2025, 6, 30)
RECORDS_FILE = Path(__file__).parent / "records.json"

# ── Away trips (inclusive dates) ──────────────────────────────────────────────
AWAY = [
    (date(2024, 7, 29), date(2024, 8, 4)),   # Kangaroo Valley → Meroo Meadow → Moss Vale
    (date(2024, 11, 3), date(2024, 11, 8)),   # Fingal Bay
    (date(2025, 1, 11), date(2025, 1, 19)),   # Mooroobool + Sawyers Gully
    (date(2025, 6, 4),  date(2025, 6, 8)),    # Stuart Park
]

# ── December specifics ────────────────────────────────────────────────────────
# Second week was more in-person (Tue–Thu); Friday was a company-wide day off.
DEC_OFFICE = {date(2024, 12, 10), date(2024, 12, 11), date(2024, 12, 12)}
DEC_COMPANY_OFF = {date(2024, 12, 13)}

# ── February weeks 1–3: all in office ────────────────────────────────────────
FEB_INOFFICE_START = date(2025, 2, 3)
FEB_INOFFICE_END = date(2025, 2, 21)


def date_range(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def month_end(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date | None:
    """Return the nth occurrence of weekday (0=Mon…6=Sun) in month, or None."""
    count = 0
    for d in date_range(date(year, month, 1), month_end(year, month)):
        if d.weekday() == weekday:
            count += 1
            if count == n:
                return d
    return None


def build_excluded() -> set[date]:
    excluded: set[date] = set()

    # Away trips
    for start, end in AWAY:
        excluded.update(date_range(start, end))

    # February weeks 1–3
    excluded.update(date_range(FEB_INOFFICE_START, FEB_INOFFICE_END))

    # December: office days + company day off
    excluded.update(DEC_OFFICE)
    excluded.update(DEC_COMPANY_OFF)

    # Normal months: 2nd and 4th Wednesday = office visits
    # Covers all months except December (special) and January (separate pattern)
    WED, THU = 2, 3
    normal_months = [
        (2024, 7), (2024, 8), (2024, 9), (2024, 10), (2024, 11),
        (2025, 2), (2025, 3), (2025, 4), (2025, 5), (2025, 6),
    ]
    for year, month in normal_months:
        second_wed = nth_weekday(year, month, WED, 2)
        if second_wed:
            excluded.add(second_wed)

        fourth_wed = nth_weekday(year, month, WED, 4)
        if fourth_wed:
            excluded.add(fourth_wed)
        else:
            # Rare: month has < 4 Wednesdays — fall back to 4th Thursday
            fourth_thu = nth_weekday(year, month, THU, 4)
            if fourth_thu:
                excluded.add(fourth_thu)

    return excluded


def compute_wfh_days() -> list[date]:
    excluded = build_excluded()

    # January 2025: WFH only on Tue + Wed (much more in-office that month)
    jan_days = [
        d for d in expand_weekdays(date(2025, 1, 1), date(2025, 1, 31), [1, 2], STATE)
        if d not in excluded
    ]

    # All other months: every business day except excluded
    other_days = [
        d for d in date_range(FY_START, FY_END)
        if not (d.year == 2025 and d.month == 1)
        and is_business_day(d, STATE)
        and d not in excluded
    ]

    return sorted(other_days + jan_days)


MONTH_ORDER = [
    "Jul 2024", "Aug 2024", "Sep 2024", "Oct 2024", "Nov 2024", "Dec 2024",
    "Jan 2025", "Feb 2025", "Mar 2025", "Apr 2025", "May 2025", "Jun 2025",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="Save records.json and generate CSV")
    args = parser.parse_args()

    days = compute_wfh_days()

    by_month: dict[str, list[date]] = defaultdict(list)
    for d in days:
        by_month[d.strftime("%b %Y")].append(d)

    print(f"\n{'Month':<12}  {'WFH days':>8}")
    print("-" * 23)
    for m in MONTH_ORDER:
        print(f"{m:<12}  {len(by_month.get(m, [])):>8}")

    total_hours = len(days) * HOURS
    print(f"\nTotal WFH days : {len(days)}")
    print(f"Hours per day  : {HOURS}")
    print(f"Total hours    : {total_hours:.1f}")
    print(f"Deduction (70c): ${total_hours * 0.70:.2f}")

    if args.write:
        if RECORDS_FILE.exists():
            print(f"\nError: {RECORDS_FILE} already exists. Remove it first.", file=sys.stderr)
            sys.exit(1)
        records = add([], days, hours=HOURS, note="FY2024-25 reconstruction")
        save(records, RECORDS_FILE)
        csv_path = Path(__file__).parent / "wfh_FY2024-25.csv"
        to_csv(records, path=csv_path)
        print(f"\nWrote {len(records)} records → {RECORDS_FILE}")
        print(f"Wrote CSV      → {csv_path}")
    else:
        print("\nRun with --write to persist records and generate CSV.")


if __name__ == "__main__":
    main()
