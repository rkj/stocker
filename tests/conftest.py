from __future__ import annotations

import csv
import math
from datetime import date, timedelta
from pathlib import Path

import pytest


def _iter_weekdays(start: date, end: date) -> list[date]:
    out: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            out.append(current)
        current += timedelta(days=1)
    return out


def _write_synthetic_market_csv(path: Path) -> None:
    symbols = ["BP", "CVX", "ED", "GD", "IBM", "KO"]
    base_price = {"BP": 25.0, "CVX": 18.0, "ED": 12.0, "GD": 20.0, "IBM": 35.0, "KO": 8.0}
    trend = {"BP": 0.00025, "CVX": 0.00020, "ED": 0.00012, "GD": 0.00030, "IBM": 0.00028, "KO": 0.00018}
    days = _iter_weekdays(date(1980, 1, 2), date(1980, 12, 31))

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]
        )
        for i, trading_day in enumerate(days):
            for j, symbol in enumerate(symbols):
                close = base_price[symbol] * ((1.0 + trend[symbol]) ** i) * (
                    1.0 + 0.03 * math.sin((i + 11 * j) / 17.0)
                )
                close = max(close, 0.5)
                open_price = close * (1.0 + 0.004 * math.sin((i + j) / 5.0))
                high = max(open_price, close) * 1.01
                low = min(open_price, close) * 0.99
                volume = float(120_000 + ((i * 7919 + j * 104_729) % 1_800_000))
                # Deterministic sparse dividends.
                dividend = 0.0
                if trading_day.month in {3, 6, 9, 12} and trading_day.day <= 7 and (i % 5 == 0):
                    dividend = round(0.01 + 0.002 * j, 6)
                writer.writerow(
                    [
                        trading_day.isoformat(),
                        symbol,
                        f"{open_price:.8f}",
                        f"{high:.8f}",
                        f"{low:.8f}",
                        f"{close:.8f}",
                        f"{volume:.1f}",
                        f"{dividend:.6f}",
                        "0.0",
                    ]
                )


@pytest.fixture(scope="session")
def synthetic_market_csv(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out_dir = tmp_path_factory.mktemp("synthetic_market")
    path = out_dir / "market.csv"
    _write_synthetic_market_csv(path)
    return path
