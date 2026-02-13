from __future__ import annotations

from datetime import date
from pathlib import Path

from stocker.data.market_data import load_market_data
from stocker.strategies.baseline import (
    EqualWeightStrategy,
    RebalanceFrequency,
    Sp500ProxyStrategy,
    should_rebalance,
)


FIXTURE_PATH = Path("tests/fixtures/sample_stock_data.csv")


def test_should_rebalance_daily_yearly_never() -> None:
    start = date(2020, 1, 2)
    next_day = date(2020, 1, 3)
    next_year = date(2021, 1, 4)

    assert should_rebalance(None, start, RebalanceFrequency.DAILY)
    assert should_rebalance(start, next_day, RebalanceFrequency.DAILY)

    assert should_rebalance(None, start, RebalanceFrequency.YEARLY)
    assert not should_rebalance(start, next_day, RebalanceFrequency.YEARLY)
    assert should_rebalance(start, next_year, RebalanceFrequency.YEARLY)

    assert should_rebalance(None, start, RebalanceFrequency.NEVER)
    assert not should_rebalance(start, next_day, RebalanceFrequency.NEVER)


def test_equal_weight_strategy_allocates_evenly() -> None:
    market = load_market_data(
        input_path=FIXTURE_PATH,
        start_date=date(1980, 1, 2),
        end_date=date(1980, 1, 2),
    )
    strategy = EqualWeightStrategy(rebalance_frequency=RebalanceFrequency.DAILY)
    weights = strategy.target_weights(market=market, trading_day=date(1980, 1, 2))

    assert len(weights) == 6
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    for value in weights.values():
        assert abs(value - (1 / 6)) < 1e-9


def test_sp500_proxy_uses_metric_proportional_weights() -> None:
    market = load_market_data(
        input_path=FIXTURE_PATH,
        start_date=date(1980, 1, 2),
        end_date=date(1980, 1, 7),
    )
    strategy = Sp500ProxyStrategy(top_n=3, rolling_window=2)
    weights = strategy.target_weights(market=market, trading_day=date(1980, 1, 7))

    assert len(weights) == 3
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    assert all(weight > 0 for weight in weights.values())

