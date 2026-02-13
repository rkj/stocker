from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from stocker.validation.benchmark import run_sp500_proxy_streaming


def _write_csv(path: Path) -> None:
    rows = [
        ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"],
        ["2020-01-02", "AAA", "10", "10", "10", "10", "100", "0", "0"],
        ["2020-01-02", "BBB", "10", "10", "10", "20", "100", "0", "0"],
        ["2020-01-03", "AAA", "10", "10", "10", "11", "100", "0", "0"],
        ["2020-01-03", "BBB", "10", "10", "10", "22", "100", "0", "0"],
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def test_streaming_benchmark_runs_and_produces_metrics(tmp_path: Path) -> None:
    data_path = tmp_path / "tiny.csv"
    _write_csv(data_path)

    result = run_sp500_proxy_streaming(
        data_path=data_path,
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 3),
        initial_capital=1000.0,
        top_n=1,
        rolling_window=2,
    )

    assert result.trading_days == 2
    assert result.final_equity > 1000.0
    assert result.cagr > 0
