"""Create deterministic fixture slices from a production-format dataset."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


REQUIRED_COLUMNS = [
    "Date",
    "Ticker",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Dividends",
    "Stock Splits",
]


@dataclass(frozen=True, slots=True)
class FixtureSummary:
    rows_scanned: int
    rows_written: int


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _validate_header(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise ValueError("input CSV has no header row")
    missing = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
    if missing:
        raise ValueError(f"missing required columns: {missing}")


def extract_fixture(
    *,
    input_path: Path,
    output_path: Path,
    symbols: set[str],
    start_date: date,
    end_date: date,
    max_rows: int | None = None,
) -> FixtureSummary:
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")
    if max_rows is not None and max_rows <= 0:
        raise ValueError("max_rows must be positive when provided")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    scanned = 0
    selected_rows: list[dict[str, str]] = []
    with input_path.open(newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        _validate_header(reader.fieldnames)
        for row in reader:
            scanned += 1
            row_date = _parse_date(row["Date"])
            if row_date < start_date or row_date > end_date:
                continue
            if symbols and row["Ticker"] not in symbols:
                continue
            selected_rows.append({column: row[column] for column in REQUIRED_COLUMNS})

    selected_rows.sort(key=lambda row: (row["Date"], row["Ticker"]))
    if max_rows is not None:
        selected_rows = selected_rows[:max_rows]

    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(selected_rows)

    return FixtureSummary(rows_scanned=scanned, rows_written=len(selected_rows))


def _parse_symbols(raw: str) -> set[str]:
    return {part.strip().upper() for part in raw.split(",") if part.strip()}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stocker-extract-fixture",
        description="Extract deterministic test fixtures from market CSV data.",
    )
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--symbols", default="")
    parser.add_argument("--start-date", required=True, type=_parse_date)
    parser.add_argument("--end-date", required=True, type=_parse_date)
    parser.add_argument("--max-rows", type=int, default=None)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    summary = extract_fixture(
        input_path=Path(args.input_path),
        output_path=Path(args.output_path),
        symbols=_parse_symbols(args.symbols),
        start_date=args.start_date,
        end_date=args.end_date,
        max_rows=args.max_rows,
    )
    print(
        f"fixture generated: scanned={summary.rows_scanned} "
        f"written={summary.rows_written} output={args.output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

