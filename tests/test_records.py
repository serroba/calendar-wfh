import json
import pytest
from datetime import date
from pathlib import Path
from wfh.records import WFHRecord, load, save, add, remove, filter_fy


@pytest.fixture
def sample_records():
    return [
        WFHRecord(date=date(2025, 8, 1), hours=8.0),
        WFHRecord(date=date(2025, 8, 4), hours=7.5, note="Short day"),
        WFHRecord(date=date(2026, 3, 2), hours=8.0),
    ]


class TestWFHRecord:
    def test_fy_auto_set_mid_year(self):
        r = WFHRecord(date=date(2026, 3, 2), hours=8.0)
        assert r.fy == "FY2025-26"

    def test_fy_auto_set_july(self):
        r = WFHRecord(date=date(2025, 7, 1), hours=8.0)
        assert r.fy == "FY2025-26"

    def test_logged_at_auto_set(self):
        r = WFHRecord(date=date(2026, 5, 1), hours=8.0)
        assert r.logged_at != ""


class TestAdd:
    def test_add_single_day(self):
        result = add([], [date(2026, 5, 1)], hours=8.0)
        assert len(result) == 1
        assert result[0].date == date(2026, 5, 1)
        assert result[0].hours == 8.0

    def test_add_multiple_days(self):
        days = [date(2026, 5, 4), date(2026, 5, 5), date(2026, 5, 6)]
        result = add([], days, hours=8.0)
        assert len(result) == 3

    def test_add_preserves_sort_order(self):
        existing = [WFHRecord(date=date(2026, 5, 10), hours=8.0)]
        result = add(existing, [date(2026, 5, 5)], hours=8.0)
        assert result[0].date == date(2026, 5, 5)
        assert result[1].date == date(2026, 5, 10)

    def test_add_duplicate_raises(self):
        existing = [WFHRecord(date=date(2026, 5, 4), hours=8.0)]
        with pytest.raises(ValueError, match="already exist"):
            add(existing, [date(2026, 5, 4)], hours=8.0)

    def test_add_with_note(self):
        result = add([], [date(2026, 5, 1)], hours=8.0, note="project day")
        assert result[0].note == "project day"

    def test_add_does_not_mutate_input(self):
        original = [WFHRecord(date=date(2026, 5, 1), hours=8.0)]
        add(original, [date(2026, 5, 2)], hours=8.0)
        assert len(original) == 1


class TestRemove:
    def test_remove_existing(self, sample_records):
        result = remove(sample_records, [date(2025, 8, 1)])
        assert len(result) == 2
        assert all(r.date != date(2025, 8, 1) for r in result)

    def test_remove_nonexistent_is_noop(self, sample_records):
        result = remove(sample_records, [date(2099, 1, 1)])
        assert len(result) == len(sample_records)

    def test_remove_multiple(self, sample_records):
        result = remove(sample_records, [date(2025, 8, 1), date(2025, 8, 4)])
        assert len(result) == 1


class TestFilterFy:
    def test_filter_returns_correct_fy(self, sample_records):
        # Aug 2025 and Mar 2026 are both FY2025-26
        result = filter_fy(sample_records, "FY2025-26")
        assert len(result) == 3

    def test_filter_excludes_other_fy(self):
        records = [
            WFHRecord(date=date(2024, 10, 1), hours=8.0),  # FY2024-25
            WFHRecord(date=date(2025, 10, 1), hours=8.0),  # FY2025-26
        ]
        result = filter_fy(records, "FY2025-26")
        assert len(result) == 1
        assert result[0].date == date(2025, 10, 1)

    def test_filter_empty(self, sample_records):
        result = filter_fy(sample_records, "FY2000-01")
        assert result == []


class TestPersistence:
    def test_save_and_load_roundtrip(self, tmp_path, sample_records):
        path = tmp_path / "records.json"
        save(sample_records, path)
        loaded = load(path)
        assert len(loaded) == len(sample_records)
        assert loaded[0].date == date(2025, 8, 1)
        assert loaded[1].hours == 7.5
        assert loaded[1].note == "Short day"

    def test_load_missing_file_returns_empty(self, tmp_path):
        assert load(tmp_path / "nonexistent.json") == []

    def test_save_sorts_by_date(self, tmp_path):
        records = [
            WFHRecord(date=date(2026, 5, 10), hours=8.0),
            WFHRecord(date=date(2026, 5, 5), hours=8.0),
        ]
        path = tmp_path / "records.json"
        save(records, path)
        data = json.loads(path.read_text())
        assert data[0]["date"] == "2026-05-05"
        assert data[1]["date"] == "2026-05-10"

    def test_load_preserves_fy(self, tmp_path):
        records = [WFHRecord(date=date(2026, 5, 1), hours=8.0)]
        path = tmp_path / "records.json"
        save(records, path)
        loaded = load(path)
        assert loaded[0].fy == "FY2025-26"
