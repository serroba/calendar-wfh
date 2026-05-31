from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from wfh.calendar import financial_year_for


@dataclass
class WFHRecord:
    date: date
    hours: float
    note: str = ""
    fy: str = field(default="")
    logged_at: str = field(default="")

    def __post_init__(self) -> None:
        if not self.fy:
            self.fy = financial_year_for(self.date)
        if not self.logged_at:
            self.logged_at = datetime.now().isoformat(timespec="seconds")


def load(path: Path) -> list[WFHRecord]:
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return [
        WFHRecord(
            date=date.fromisoformat(r["date"]),
            hours=r["hours"],
            note=r.get("note", ""),
            fy=r.get("fy", ""),
            logged_at=r.get("logged_at", ""),
        )
        for r in data
    ]


def save(records: list[WFHRecord], path: Path) -> None:
    data = [
        {
            "date": r.date.isoformat(),
            "hours": r.hours,
            "note": r.note,
            "fy": r.fy,
            "logged_at": r.logged_at,
        }
        for r in sorted(records, key=lambda r: r.date)
    ]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def add(
    records: list[WFHRecord],
    days: list[date],
    hours: float,
    note: str = "",
) -> list[WFHRecord]:
    existing = {r.date for r in records}
    duplicates = [d for d in days if d in existing]
    if duplicates:
        raise ValueError(
            f"Records already exist for: {', '.join(d.isoformat() for d in duplicates)}"
        )
    new = [WFHRecord(date=d, hours=hours, note=note) for d in days]
    return sorted(records + new, key=lambda r: r.date)


def remove(records: list[WFHRecord], dates: list[date]) -> list[WFHRecord]:
    drop = set(dates)
    return [r for r in records if r.date not in drop]


def filter_fy(records: list[WFHRecord], fy: str) -> list[WFHRecord]:
    return [r for r in records if r.fy == fy]
