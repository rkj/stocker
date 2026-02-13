from __future__ import annotations

from datetime import date
from pathlib import Path

from stocker.data.market_data import load_market_data


FIXTURE_PATH = Path("tests/fixtures/sample_stock_data.csv")


def test_load_market_data_builds_sorted_calendar() -> None:
    market = load_market_data(
        input_path=FIXTURE_PATH,
        start_date=date(1980, 1, 1),
        end_date=date(1980, 12, 31),
    )

    assert len(market.trading_dates) == 253
    assert market.trading_dates[0] == date(1980, 1, 2)
    assert market.trading_dates[-1] == date(1980, 12, 31)
    assert market.symbols == {"BP", "CVX", "ED", "GD", "IBM", "KO"}


def test_load_market_data_honors_symbol_filter() -> None:
    market = load_market_data(
        input_path=FIXTURE_PATH,
        start_date=date(1980, 1, 1),
        end_date=date(1980, 1, 31),
        symbols={"BP", "KO"},
    )

    assert market.symbols == {"BP", "KO"}
    first_day = market.trading_dates[0]
    assert set(market.bars_on(first_day)) == {"BP", "KO"}


def test_rolling_dollar_volume_uses_configured_window() -> None:
    market = load_market_data(
        input_path=FIXTURE_PATH,
        start_date=date(1980, 1, 2),
        end_date=date(1980, 1, 7),
        symbols={"BP"},
    )
    values = market.rolling_dollar_volume(window=2)

    # First available day has only one day of history in the rolling window.
    first = market.trading_dates[0]
    second = market.trading_dates[1]
    assert values[first]["BP"] > 0
    assert values[second]["BP"] >= values[first]["BP"] * 0.5

