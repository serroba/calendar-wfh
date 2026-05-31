from __future__ import annotations

import csv
import io
from pathlib import Path

from wfh.records import WFHRecord

RATE_PER_HOUR = 0.70


def to_csv(records: list[WFHRecord], path: Path | None = None) -> str:
    records = sorted(records, key=lambda r: r.date)

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        ["Date", "Day", "Hours WFH", "Running Total (hrs)", f"Deduction @ ${RATE_PER_HOUR}/hr ($)", "Note"]
    )

    running = 0.0
    for r in records:
        running += r.hours
        writer.writerow([
            r.date.isoformat(),
            r.date.strftime("%A"),
            f"{r.hours:.1f}",
            f"{running:.1f}",
            f"{running * RATE_PER_HOUR:.2f}",
            r.note,
        ])

    total_hours = sum(r.hours for r in records)
    writer.writerow([])
    writer.writerow(["TOTAL", "", f"{total_hours:.1f}", "", f"{total_hours * RATE_PER_HOUR:.2f}", ""])

    csv_str = out.getvalue()

    if path is not None:
        with open(path, "w", newline="") as f:
            f.write(csv_str)

    return csv_str


def summary(records: list[WFHRecord]) -> dict:
    total_hours = sum(r.hours for r in records)
    return {
        "days": len(records),
        "hours": total_hours,
        "deduction": round(total_hours * RATE_PER_HOUR, 2),
    }
