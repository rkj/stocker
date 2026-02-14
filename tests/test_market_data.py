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


def test_loader_skips_rows_with_blank_close(tmp_path: Path) -> None:
    path = tmp_path / "blank_close.csv"
    path.write_text(
        "\n".join(
            [
                "Date,Ticker,Open,High,Low,Close,Volume,Dividends,Stock Splits",
                "2020-01-02,AAA,1,1,1,,100,0,0",
                "2020-01-02,BBB,2,2,2,2,100,0,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    market = load_market_data(
        input_path=path,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 1, 10),
    )
    assert market.trading_dates == [date(2020, 1, 2)]
    assert market.symbols == {"BBB"}


def test_loader_applies_price_and_volume_filters(tmp_path: Path) -> None:
    path = tmp_path / "filters.csv"
    path.write_text(
        "\n".join(
            [
                "Date,Ticker,Open,High,Low,Close,Volume,Dividends,Stock Splits",
                "2020-01-02,LOWVOL,10,10,10,10,10,0,0",
                "2020-01-02,TINYP,0.001,0.001,0.001,0.001,10000,0,0",
                "2020-01-02,OK,10,10,10,10,10000,0,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    market = load_market_data(
        input_path=path,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 1, 10),
        min_price=0.01,
        max_price=100_000.0,
        min_volume=1_000.0,
    )
    assert market.symbols == {"OK"}


def test_loader_can_reconstruct_price_only_close_from_adjusted_series(tmp_path: Path) -> None:
    path = tmp_path / "adjusted.csv"
    path.write_text(
        "\n".join(
            [
                "Date,Ticker,Open,High,Low,Close,Volume,Dividends,Stock Splits",
                "2020-01-02,AAA,99.0990990991,99.0990990991,99.0990990991,99.0990990991,100,0,0",
                "2020-01-03,AAA,110,110,110,110,100,1,0",
                "2020-01-06,AAA,121,121,121,121,100,0,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    market = load_market_data(
        input_path=path,
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 6),
        price_series_mode="raw_reconstructed",
    )
    closes = [market.close_on(day, "AAA") for day in market.trading_dates]
    assert round(closes[0] or 0.0, 8) == 100.0
    assert round(closes[1] or 0.0, 8) == 110.0
    assert round(closes[2] or 0.0, 8) == 121.0
