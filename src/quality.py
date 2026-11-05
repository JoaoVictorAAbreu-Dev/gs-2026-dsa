"""Validação inicial de uma série hídrica normalizada; não estima risco."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


REQUIRED = {"date", "system", "storage_pct"}


@dataclass(frozen=True)
class QualityReport:
    source: str
    rows: int
    systems: list[str]
    first_date: str | None
    last_date: str | None
    duplicate_system_dates: int
    invalid_rows: int
    date_gaps: dict[str, int]
    errors: list[str]

    @property
    def usable(self) -> bool:
        return self.rows > 0 and self.invalid_rows == 0 and self.duplicate_system_dates == 0


def inspect_csv(path: Path, source: str) -> QualityReport:
    """Check normalized date/system/storage values without inferring missing data."""
    errors: list[str] = []
    dates_by_system: dict[str, set[date]] = {}
    all_dates: list[date] = []
    invalid = duplicates = rows = 0

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
        for line, record in enumerate(reader, start=2):
            rows += 1
            try:
                observed = date.fromisoformat((record["date"] or "").strip())
                system = (record["system"] or "").strip()
                if not system:
                    raise ValueError("empty system")
                storage = float((record["storage_pct"] or "").replace(",", "."))
                if not 0 <= storage <= 100:
                    raise ValueError("storage_pct outside 0..100")
            except (ValueError, TypeError) as exc:
                invalid += 1
                errors.append(f"line {line}: {exc}")
                continue
            seen = dates_by_system.setdefault(system, set())
            if observed in seen:
                duplicates += 1
                errors.append(f"line {line}: duplicate date for system {system}")
            seen.add(observed)
            all_dates.append(observed)

    gaps: dict[str, int] = {}
    for system, observations in dates_by_system.items():
        ordered = sorted(observations)
        gaps[system] = sum((b - a).days - 1 for a, b in zip(ordered, ordered[1:]))

    return QualityReport(
        source=source,
        rows=rows,
        systems=sorted(dates_by_system),
        first_date=min(all_dates).isoformat() if all_dates else None,
        last_date=max(all_dates).isoformat() if all_dates else None,
        duplicate_system_dates=duplicates,
        invalid_rows=invalid,
        date_gaps=gaps,
        errors=errors,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect normalized reservoir CSV quality")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--source", required=True, help="Verifiable source URL or identifier")
    args = parser.parse_args()
    report = inspect_csv(args.csv, args.source)
    print(json.dumps({**asdict(report), "usable": report.usable}, ensure_ascii=False, indent=2))
    return 0 if report.usable else 2


if __name__ == "__main__":
    raise SystemExit(main())
