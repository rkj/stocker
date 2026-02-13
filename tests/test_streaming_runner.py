from __future__ import annotations

from datetime import date
from pathlib import Path

from stocker.data.market_data import load_market_data
from stocker.simulation.runner import ContributionFrequency, RunSettings, run_simulation
from stocker.simulation.streaming import run_simulation_streaming


FIXTURE_PATH = Path("tests/fixtures/sample_stock_data.csv")


def test_streaming_runner_matches_in_memory_for_fixture_window() -> None:
    settings = RunSettings(
        initial_capital=10_000.0,
        contribution_amount=100.0,
        contribution_frequency=ContributionFrequency.MONTHLY,
        fee_bps=1.0,
        fee_fixed=0.0,
        slippage_bps=1.0,
        seed=42,
    )
    specs = [
        {"strategy_id": "eq_daily", "type": "equal_weight", "rebalance_frequency": "daily"},
        {"strategy_id": "top3", "type": "top_n_ranked", "rebalance_frequency": "monthly", "params": {"n": 3, "metric": "dollar_volume_1d"}},
        {"strategy_id": "rand2", "type": "random_n", "rebalance_frequency": "monthly", "params": {"n": 2, "seed": 7}},
    ]
    in_memory_market = load_market_data(
        input_path=FIXTURE_PATH,
        start_date=date(1980, 1, 2),
        end_date=date(1980, 3, 31),
    )
    in_mem = run_simulation(
        market=in_memory_market,
        strategy_specs=specs,
        settings=settings,
    )
    streamed = run_simulation_streaming(
        data_path=FIXTURE_PATH,
        start_date=date(1980, 1, 2),
        end_date=date(1980, 3, 31),
        strategy_specs=specs,
        settings=settings,
    )

    assert set(in_mem.daily_records_by_strategy) == set(streamed.daily_records_by_strategy)
    for strategy_id in in_mem.daily_records_by_strategy:
        a = in_mem.daily_records_by_strategy[strategy_id]
        b = streamed.daily_records_by_strategy[strategy_id]
        assert len(a) == len(b)
        assert round(a[-1].total_equity, 8) == round(b[-1].total_equity, 8)


def test_streaming_runner_is_deterministic_for_random_strategy() -> None:
    settings = RunSettings(
        initial_capital=10_000.0,
        contribution_amount=0.0,
        contribution_frequency=ContributionFrequency.NONE,
        fee_bps=0.0,
        fee_fixed=0.0,
        slippage_bps=0.0,
        seed=99,
    )
    specs = [
        {"strategy_id": "rand2", "type": "random_n", "rebalance_frequency": "daily", "params": {"n": 2, "seed": 123}}
    ]
    first = run_simulation_streaming(
        data_path=FIXTURE_PATH,
        start_date=date(1980, 1, 2),
        end_date=date(1980, 1, 20),
        strategy_specs=specs,
        settings=settings,
    )
    second = run_simulation_streaming(
        data_path=FIXTURE_PATH,
        start_date=date(1980, 1, 2),
        end_date=date(1980, 1, 20),
        strategy_specs=specs,
        settings=settings,
    )

    f_records = first.daily_records_by_strategy["rand2"]
    s_records = second.daily_records_by_strategy["rand2"]
    assert len(f_records) == len(s_records)
    assert [round(r.total_equity, 10) for r in f_records] == [
        round(r.total_equity, 10) for r in s_records
    ]

