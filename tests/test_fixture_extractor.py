from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from stocker.tools.fixture_extractor import extract_fixture


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
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
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_extract_fixture_filters_and_sorts_rows(tmp_path: Path) -> None:
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "fixture.csv"
    _write_csv(
        input_path,
        [
            {
                "Date": "2020-01-03",
                "Ticker": "BBB",
                "Open": "1",
                "High": "1",
                "Low": "1",
                "Close": "1",
                "Volume": "10",
                "Dividends": "0",
                "Stock Splits": "0",
            },
            {
                "Date": "2020-01-02",
                "Ticker": "AAA",
                "Open": "1",
                "High": "1",
                "Low": "1",
                "Close": "1",
                "Volume": "10",
                "Dividends": "0",
                "Stock Splits": "0",
            },
            {
                "Date": "2020-01-02",
                "Ticker": "CCC",
                "Open": "1",
                "High": "1",
                "Low": "1",
                "Close": "1",
                "Volume": "10",
                "Dividends": "0",
                "Stock Splits": "0",
            },
        ],
    )

    summary = extract_fixture(
        input_path=input_path,
        output_path=output_path,
        symbols={"AAA", "BBB"},
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 3),
    )

    assert summary.rows_written == 2
    with output_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert [r["Date"] for r in rows] == ["2020-01-02", "2020-01-03"]
    assert [r["Ticker"] for r in rows] == ["AAA", "BBB"]


def test_extract_fixture_is_deterministic_for_max_rows(tmp_path: Path) -> None:
    input_path = tmp_path / "input.csv"
    out_a = tmp_path / "a.csv"
    out_b = tmp_path / "b.csv"
    _write_csv(
        input_path,
        [
            {
                "Date": "2020-01-02",
                "Ticker": ticker,
                "Open": "1",
                "High": "1",
                "Low": "1",
                "Close": "1",
                "Volume": "10",
                "Dividends": "0",
                "Stock Splits": "0",
            }
            for ticker in ["CCC", "AAA", "BBB"]
        ],
    )

    extract_fixture(
        input_path=input_path,
        output_path=out_a,
        symbols={"AAA", "BBB", "CCC"},
        start_date=date(2020, 1, 1),
        end_date=date(2020, 1, 5),
        max_rows=2,
    )
    extract_fixture(
        input_path=input_path,
        output_path=out_b,
        symbols={"AAA", "BBB", "CCC"},
        start_date=date(2020, 1, 1),
        end_date=date(2020, 1, 5),
        max_rows=2,
    )

    assert out_a.read_text(encoding="utf-8") == out_b.read_text(encoding="utf-8")

