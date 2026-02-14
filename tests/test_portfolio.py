from __future__ import annotations

from stocker.engine.portfolio import Portfolio, RebalanceCosts


def test_contribution_updates_cash_and_cumulative_amount() -> None:
    p = Portfolio(initial_cash=10_000.0)
    p.contribute(500.0)

    assert p.cash == 10_500.0
    assert p.cumulative_contributions == 500.0


def test_rebalance_from_cash_to_equal_weights_without_costs() -> None:
    p = Portfolio(initial_cash=1_000.0)
    fills = p.rebalance_to_weights(
        target_weights={"AAA": 0.5, "BBB": 0.5},
        prices={"AAA": 10.0, "BBB": 20.0},
        costs=RebalanceCosts(),
    )

    assert len(fills) == 2
    assert round(p.holdings["AAA"], 6) == 50.0
    assert round(p.holdings["BBB"], 6) == 25.0
    assert abs(p.cash) < 1e-9


def test_rebalance_applies_transaction_costs() -> None:
    p = Portfolio(initial_cash=1_000.0)
    p.rebalance_to_weights(
        target_weights={"AAA": 1.0},
        prices={"AAA": 10.0},
        costs=RebalanceCosts(fee_bps=10.0, fee_fixed=1.0, slippage_bps=5.0),
    )

    assert p.holdings["AAA"] > 0
    assert p.cash >= 0
    assert p.cumulative_costs > 0


def test_total_equity_matches_cash_plus_market_value() -> None:
    p = Portfolio(initial_cash=500.0)
    p.rebalance_to_weights(
        target_weights={"AAA": 1.0},
        prices={"AAA": 10.0},
        costs=RebalanceCosts(),
    )

    equity = p.total_equity({"AAA": 11.0})
    assert abs(equity - (p.cash + p.total_market_value({"AAA": 11.0}))) < 1e-9


def test_apply_dividends_credits_cash_for_held_shares() -> None:
    p = Portfolio(initial_cash=0.0)
    p.holdings["AAA"] = 10.0

    credited = p.apply_dividends({"AAA": 0.5, "BBB": 1.0})
    assert credited == 5.0
    assert p.cash == 5.0
    assert p.cumulative_dividends == 5.0


def test_rebalance_respects_volume_participation_cap() -> None:
    p = Portfolio(initial_cash=10_000.0)
    p.rebalance_to_weights(
        target_weights={"AAA": 1.0},
        prices={"AAA": 10.0},
        volumes={"AAA": 1_000.0},
        costs=RebalanceCosts(),
        max_trade_participation=0.01,
    )
    # At most 1% of 1000 shares volume => 10 shares.
    assert round(p.holdings["AAA"], 8) == 10.0


def test_rebalance_skips_symbol_with_zero_volume() -> None:
    p = Portfolio(initial_cash=10_000.0)
    fills = p.rebalance_to_weights(
        target_weights={"AAA": 1.0},
        prices={"AAA": 10.0},
        volumes={"AAA": 0.0},
        costs=RebalanceCosts(),
        max_trade_participation=0.01,
    )
    assert fills == []
    assert p.holdings == {}
    assert p.cash == 10_000.0
