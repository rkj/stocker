from __future__ import annotations

import json
import csv
from datetime import date
from pathlib import Path

from stocker.data.market_data import load_market_data
from stocker.simulation.config_parser import parse_strategy_file
from stocker.simulation.runner import ContributionFrequency, RunSettings, run_simulation


FIXTURE_PATH = Path("tests/fixtures/sample_stock_data.csv")


def test_parse_strategy_file_loads_multiple_strategies(tmp_path: Path) -> None:
    config_path = tmp_path / "strategies.json"
    config_path.write_text(
        json.dumps(
            {
                "strategies": [
                    {"strategy_id": "eq_daily", "type": "equal_weight"},
                    {
                        "strategy_id": "rand2",
                        "type": "random_n",
                        "params": {"n": 2, "seed": 123},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    parsed = parse_strategy_file(config_path)
    assert [s.strategy_id for s in parsed] == ["eq_daily", "rand2"]
    assert parsed[1].params["n"] == 2


def test_run_simulation_produces_daily_records_for_each_strategy() -> None:
    market = load_market_data(
        input_path=FIXTURE_PATH,
        start_date=date(1980, 1, 2),
        end_date=date(1980, 1, 10),
    )
    settings = RunSettings(
        initial_capital=10_000.0,
        contribution_amount=0.0,
        contribution_frequency=ContributionFrequency.NONE,
        fee_bps=0.0,
        fee_fixed=0.0,
        slippage_bps=0.0,
    )
    strategies = [
        {"strategy_id": "eq_daily", "type": "equal_weight"},
        {"strategy_id": "eq_yearly", "type": "equal_weight", "rebalance_frequency": "yearly"},
    ]

    result = run_simulation(market=market, strategy_specs=strategies, settings=settings)

    assert set(result.daily_records_by_strategy.keys()) == {"eq_daily", "eq_yearly"}
    for records in result.daily_records_by_strategy.values():
        assert len(records) == len(market.trading_dates)
        assert records[0].date == market.trading_dates[0]
        assert records[-1].date == market.trading_dates[-1]


def test_monthly_contribution_is_applied_on_first_trading_day_of_month() -> None:
    market = load_market_data(
        input_path=FIXTURE_PATH,
        start_date=date(1980, 1, 2),
        end_date=date(1980, 2, 5),
    )
    settings = RunSettings(
        initial_capital=1_000.0,
        contribution_amount=100.0,
        contribution_frequency=ContributionFrequency.MONTHLY,
        fee_bps=0.0,
        fee_fixed=0.0,
        slippage_bps=0.0,
    )
    strategies = [{"strategy_id": "eq_daily", "type": "equal_weight"}]
    result = run_simulation(market=market, strategy_specs=strategies, settings=settings)

    final = result.daily_records_by_strategy["eq_daily"][-1]
    assert final.cumulative_contributions == 200.0


def test_dividends_are_credited_to_portfolio_cash(tmp_path: Path) -> None:
    csv_path = tmp_path / "dividends.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]
        )
        writer.writerow(["2020-01-02", "AAA", 10, 10, 10, 10, 100, 0, 0])
        writer.writerow(["2020-01-03", "AAA", 10, 10, 10, 10, 100, 1, 0])

    market = load_market_data(
        input_path=csv_path,
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 3),
    )
    result = run_simulation(
        market=market,
        strategy_specs=[
            {
                "strategy_id": "aaa",
                "type": "explicit_symbols",
                "params": {"symbols": ["AAA"]},
            }
        ],
        settings=RunSettings(
            initial_capital=1000.0,
            contribution_amount=0.0,
            contribution_frequency=ContributionFrequency.NONE,
            fee_bps=0.0,
            fee_fixed=0.0,
            slippage_bps=0.0,
            credit_dividends=True,
        ),
    )
    final = result.daily_records_by_strategy["aaa"][-1]
    assert final.cumulative_dividends == 100.0
    assert final.total_equity == 1100.0
