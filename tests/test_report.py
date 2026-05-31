import csv
import io
from datetime import date

import pytest

from wfh.records import WFHRecord
from wfh.report import RATE_PER_HOUR, summary, to_csv


@pytest.fixture
def records():
    return [
        WFHRecord(date=date(2026, 5, 4), hours=8.0),  # Monday
        WFHRecord(date=date(2026, 5, 5), hours=8.0),  # Tuesday
        WFHRecord(date=date(2026, 5, 6), hours=7.5, note="Early finish"),  # Wednesday
    ]


def parse_data_rows(csv_str: str) -> list[list[str]]:
    reader = csv.reader(io.StringIO(csv_str))
    next(reader)  # skip header
    return [r for r in reader if r and r[0] not in ("", "TOTAL")]


class TestToCsv:
    def test_returns_string(self, records):
        assert isinstance(to_csv(records), str)

    def test_header_columns(self, records):
        reader = csv.reader(io.StringIO(to_csv(records)))
        header = next(reader)
        assert "Date" in header
        assert "Day" in header
        assert "Hours WFH" in header

    def test_data_row_count(self, records):
        assert len(parse_data_rows(to_csv(records))) == 3

    def test_running_total_accumulates(self, records):
        rows = parse_data_rows(to_csv(records))
        assert float(rows[0][3]) == 8.0
        assert float(rows[1][3]) == 16.0
        assert float(rows[2][3]) == 23.5

    def test_deduction_on_last_row(self, records):
        rows = parse_data_rows(to_csv(records))
        expected = round(23.5 * RATE_PER_HOUR, 2)
        assert float(rows[2][4]) == pytest.approx(expected)

    def test_note_included(self, records):
        assert "Early finish" in to_csv(records)

    def test_day_name_included(self, records):
        assert "Monday" in to_csv(records)

    def test_writes_to_file(self, records, tmp_path):
        path = tmp_path / "report.csv"
        to_csv(records, path=path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_sorted_by_date_regardless_of_input_order(self):
        unsorted = [
            WFHRecord(date=date(2026, 5, 6), hours=8.0),
            WFHRecord(date=date(2026, 5, 4), hours=8.0),
        ]
        rows = parse_data_rows(to_csv(unsorted))
        assert rows[0][0] == "2026-05-04"
        assert rows[1][0] == "2026-05-06"

    def test_total_row_present(self, records):
        reader = csv.reader(io.StringIO(to_csv(records)))
        rows = list(reader)
        total_rows = [r for r in rows if r and r[0] == "TOTAL"]
        assert len(total_rows) == 1

    def test_total_row_hours(self, records):
        reader = csv.reader(io.StringIO(to_csv(records)))
        rows = list(reader)
        total_row = next(r for r in rows if r and r[0] == "TOTAL")
        assert float(total_row[2]) == 23.5

    def test_total_row_deduction(self, records):
        reader = csv.reader(io.StringIO(to_csv(records)))
        rows = list(reader)
        total_row = next(r for r in rows if r and r[0] == "TOTAL")
        assert float(total_row[4]) == pytest.approx(23.5 * RATE_PER_HOUR)


class TestSummary:
    def test_counts_days_hours_deduction(self, records):
        s = summary(records)
        assert s["days"] == 3
        assert s["hours"] == 23.5
        assert s["deduction"] == pytest.approx(23.5 * RATE_PER_HOUR)

    def test_empty_records(self):
        s = summary([])
        assert s["days"] == 0
        assert s["hours"] == 0
        assert s["deduction"] == 0
