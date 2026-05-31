from datetime import date

from wfh.calendar import expand_weekdays, financial_year_for, fy_bounds, is_business_day


class TestIsBusinessDay:
    def test_regular_weekday(self):
        assert is_business_day(date(2026, 4, 2)) is True  # Thursday

    def test_saturday(self):
        assert is_business_day(date(2026, 4, 4)) is False

    def test_sunday(self):
        assert is_business_day(date(2026, 4, 5)) is False

    def test_good_friday(self):
        assert is_business_day(date(2026, 4, 3)) is False  # Good Friday 2026

    def test_easter_monday(self):
        assert is_business_day(date(2026, 4, 6)) is False  # Easter Monday 2026

    def test_christmas_day(self):
        assert is_business_day(date(2025, 12, 25)) is False

    def test_australia_day(self):
        assert is_business_day(date(2026, 1, 26)) is False  # Monday


class TestExpandWeekdays:
    def test_all_weekdays_excludes_weekend(self):
        days = expand_weekdays(date(2026, 5, 4), date(2026, 5, 10))
        for d in days:
            assert d.weekday() < 5

    def test_specific_weekdays_monday_wednesday(self):
        # Week of May 4–8 2026: no public holidays
        days = expand_weekdays(date(2026, 5, 4), date(2026, 5, 8), weekdays=[0, 2])
        assert date(2026, 5, 4) in days  # Monday
        assert date(2026, 5, 5) not in days  # Tuesday
        assert date(2026, 5, 6) in days  # Wednesday
        assert date(2026, 5, 7) not in days  # Thursday
        assert date(2026, 5, 8) not in days  # Friday

    def test_excludes_public_holidays(self):
        # Easter week 2026: Apr 6 is Easter Monday
        days = expand_weekdays(date(2026, 4, 6), date(2026, 4, 10))
        assert date(2026, 4, 6) not in days  # Easter Monday — holiday
        assert date(2026, 4, 7) in days  # Tuesday — regular

    def test_empty_range_when_end_before_start(self):
        days = expand_weekdays(date(2026, 5, 10), date(2026, 5, 1))
        assert days == []

    def test_single_holiday_day_returns_empty(self):
        days = expand_weekdays(date(2026, 4, 3), date(2026, 4, 3))  # Good Friday
        assert days == []

    def test_single_business_day(self):
        days = expand_weekdays(date(2026, 5, 19), date(2026, 5, 19))  # Tuesday
        assert days == [date(2026, 5, 19)]

    def test_good_friday_excluded(self):
        # Apr 3 2026 is Good Friday (a Friday), should not appear even with weekdays=[4]
        days = expand_weekdays(date(2026, 4, 1), date(2026, 4, 10), weekdays=[4])
        assert date(2026, 4, 3) not in days  # Good Friday
        assert date(2026, 4, 10) in days  # Regular Friday


class TestFinancialYearFor:
    def test_july_starts_new_fy(self):
        assert financial_year_for(date(2025, 7, 1)) == "FY2025-26"

    def test_june_ends_fy(self):
        assert financial_year_for(date(2026, 6, 30)) == "FY2025-26"

    def test_january_mid_fy(self):
        assert financial_year_for(date(2026, 1, 15)) == "FY2025-26"

    def test_june_30_previous_fy(self):
        assert financial_year_for(date(2025, 6, 30)) == "FY2024-25"

    def test_new_year_day(self):
        assert financial_year_for(date(2026, 1, 1)) == "FY2025-26"


class TestFyBounds:
    def test_fy_bounds(self):
        start, end = fy_bounds("FY2025-26")
        assert start == date(2025, 7, 1)
        assert end == date(2026, 6, 30)

    def test_fy_bounds_earlier_year(self):
        start, end = fy_bounds("FY2024-25")
        assert start == date(2024, 7, 1)
        assert end == date(2025, 6, 30)
