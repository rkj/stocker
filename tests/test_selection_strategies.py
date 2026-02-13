from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from stocker.data.market_data import load_market_data
from stocker.strategies.selection import (
    BottomNRankedStrategy,
    ExplicitSymbolsEqualStrategy,
    RandomNEqualStrategy,
    TopNRankedStrategy,
)


def _write_single_day_csv(path: Path) -> None:
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
    rows = [
        ["2020-01-02", "AAA", 10, 10, 10, 10, 100, 0, 0],
        ["2020-01-02", "BBB", 20, 20, 20, 20, 100, 0, 0],
        ["2020-01-02", "CCC", 30, 30, 30, 30, 100, 0, 0],
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        writer.writerows(rows)


def test_explicit_symbols_strategy_uses_requested_subset(tmp_path: Path) -> None:
    csv_path = tmp_path / "single_day.csv"
    _write_single_day_csv(csv_path)
    market = load_market_data(
        input_path=csv_path,
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 2),
    )
    strategy = ExplicitSymbolsEqualStrategy(symbols=["AAA", "ZZZ"])
    weights = strategy.target_weights(market=market, trading_day=date(2020, 1, 2))

    assert weights == {"AAA": 1.0}


def test_random_n_strategy_is_seed_deterministic(tmp_path: Path) -> None:
    csv_path = tmp_path / "single_day.csv"
    _write_single_day_csv(csv_path)
    market = load_market_data(
        input_path=csv_path,
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 2),
    )
    strategy = RandomNEqualStrategy(n=2, seed=7)

    first = strategy.target_weights(market=market, trading_day=date(2020, 1, 2))
    second = strategy.target_weights(market=market, trading_day=date(2020, 1, 2))
    assert first == second
    assert len(first) == 2


def test_top_and_bottom_ranked_strategies_use_close_metric(tmp_path: Path) -> None:
    csv_path = tmp_path / "single_day.csv"
    _write_single_day_csv(csv_path)
    market = load_market_data(
        input_path=csv_path,
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 2),
    )

    top = TopNRankedStrategy(n=2, metric="close_price")
    bottom = BottomNRankedStrategy(n=1, metric="close_price")
    top_weights = top.target_weights(market=market, trading_day=date(2020, 1, 2))
    bottom_weights = bottom.target_weights(market=market, trading_day=date(2020, 1, 2))

    assert set(top_weights) == {"BBB", "CCC"}
    assert set(bottom_weights) == {"AAA"}

