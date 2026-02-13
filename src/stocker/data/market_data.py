"""Date-indexed market data loader and trading calendar model."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


REQUIRED_COLUMNS = (
    "Date",
    "Ticker",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Dividends",
    "Stock Splits",
)


@dataclass(frozen=True, slots=True)
class MarketBar:
    date: date
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    dividends: float
    stock_splits: float


class MarketData:
    """Market snapshot access by trading date."""

    def __init__(self, bars_by_date: dict[date, dict[str, MarketBar]]) -> None:
        self._bars_by_date = bars_by_date
        self.trading_dates = sorted(bars_by_date.keys())
        self.symbols = {
            ticker
            for per_date in bars_by_date.values()
            for ticker in per_date.keys()
        }

    def bars_on(self, trading_day: date) -> dict[str, MarketBar]:
        return self._bars_by_date.get(trading_day, {})

    def close_on(self, trading_day: date, ticker: str) -> float | None:
        bar = self._bars_by_date.get(trading_day, {}).get(ticker)
        return None if bar is None else bar.close

    def rolling_dollar_volume(self, *, window: int) -> dict[date, dict[str, float]]:
        if window <= 0:
            raise ValueError("window must be positive")

        per_symbol_series: dict[str, list[float]] = {
            symbol: [] for symbol in sorted(self.symbols)
        }
        for day in self.trading_dates:
            day_rows = self._bars_by_date[day]
            for symbol in per_symbol_series:
                bar = day_rows.get(symbol)
                per_symbol_series[symbol].append(
                    0.0 if bar is None else bar.close * bar.volume
                )

        prefix_sums: dict[str, list[float]] = {}
        for symbol, series in per_symbol_series.items():
            sums = [0.0]
            running = 0.0
            for value in series:
                running += value
                sums.append(running)
            prefix_sums[symbol] = sums

        out: dict[date, dict[str, float]] = {}
        for idx, day in enumerate(self.trading_dates):
            start = max(0, idx - window + 1)
            out[day] = {}
            for symbol, sums in prefix_sums.items():
                rolling_sum = sums[idx + 1] - sums[start]
                if rolling_sum > 0:
                    out[day][symbol] = rolling_sum
        return out


def _parse_date(raw: str) -> date:
    return date.fromisoformat(raw)


def _validate_header(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise ValueError("missing CSV header")
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing:
        raise ValueError(f"missing required columns: {missing}")


def _parse_optional_float(row: dict[str, str], key: str) -> float | None:
    raw = row.get(key)
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def load_market_data(
    *,
    input_path: Path,
    start_date: date,
    end_date: date,
    symbols: set[str] | None = None,
    progress_years: bool = False,
) -> MarketData:
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    symbol_filter = None if symbols is None else {sym.upper() for sym in symbols}
    bars_by_date: dict[date, dict[str, MarketBar]] = {}
    last_reported_year: int | None = None

    with input_path.open(newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        _validate_header(reader.fieldnames)
        for row in reader:
            row_date = _parse_date(row["Date"])
            if row_date < start_date or row_date > end_date:
                continue
            if progress_years and row_date.year != last_reported_year:
                print(f"[load] year={row_date.year}", flush=True)
                last_reported_year = row_date.year
            ticker = row["Ticker"].upper()
            if symbol_filter is not None and ticker not in symbol_filter:
                continue

            close = _parse_optional_float(row, "Close")
            if close is None or close <= 0:
                continue
            open_price = _parse_optional_float(row, "Open")
            high = _parse_optional_float(row, "High")
            low = _parse_optional_float(row, "Low")
            volume = _parse_optional_float(row, "Volume")
            dividends = _parse_optional_float(row, "Dividends")
            stock_splits = _parse_optional_float(row, "Stock Splits")

            bar = MarketBar(
                date=row_date,
                ticker=ticker,
                open=close if open_price is None else open_price,
                high=close if high is None else high,
                low=close if low is None else low,
                close=close,
                volume=0.0 if volume is None else volume,
                dividends=0.0 if dividends is None else dividends,
                stock_splits=0.0 if stock_splits is None else stock_splits,
            )
            bars_by_date.setdefault(row_date, {})[ticker] = bar

    return MarketData(bars_by_date)
