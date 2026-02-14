from __future__ import annotations

from datetime import date
from pathlib import Path
import csv

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


def test_streaming_runner_does_not_create_phantom_equity_with_missing_symbols(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing_symbol.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]
        )
        writer.writerow(["2020-01-02", "AAA", 10, 10, 10, 10, 100, 0, 0])
        writer.writerow(["2020-01-02", "BBB", 10, 10, 10, 10, 100, 0, 0])
        writer.writerow(["2020-01-03", "AAA", 20, 20, 20, 20, 100, 0, 0])  # BBB missing
        writer.writerow(["2020-01-04", "AAA", 20, 20, 20, 20, 100, 0, 0])  # BBB still missing

    settings = RunSettings(
        initial_capital=1000.0,
        contribution_amount=0.0,
        contribution_frequency=ContributionFrequency.NONE,
        fee_bps=0.0,
        fee_fixed=0.0,
        slippage_bps=0.0,
        seed=1,
    )
    specs = [
        {"strategy_id": "eq", "type": "equal_weight", "rebalance_frequency": "daily"}
    ]

    market = load_market_data(
        input_path=path,
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 4),
    )
    in_mem = run_simulation(market=market, strategy_specs=specs, settings=settings)
    streamed = run_simulation_streaming(
        data_path=path,
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 4),
        strategy_specs=specs,
        settings=settings,
    )

    expected = [r.total_equity for r in in_mem.daily_records_by_strategy["eq"]]
    actual = [r.total_equity for r in streamed.daily_records_by_strategy["eq"]]
    assert actual == expected


def test_manual_two_stock_example_matches_expected_final_equity(tmp_path: Path) -> None:
    path = tmp_path / "manual_example.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]
        )
        writer.writerow(["2020-01-02", "AAA", 10, 10, 10, 10, 100, 0, 0])
        writer.writerow(["2020-01-02", "BBB", 10, 10, 10, 10, 100, 0, 0])
        writer.writerow(["2020-01-03", "AAA", 20, 20, 20, 20, 100, 0, 0])
        writer.writerow(["2020-01-03", "BBB", 10, 10, 10, 10, 100, 0, 0])
        writer.writerow(["2020-01-04", "AAA", 20, 20, 20, 20, 100, 0, 0])
        writer.writerow(["2020-01-04", "BBB", 20, 20, 20, 20, 100, 0, 0])

    settings = RunSettings(
        initial_capital=1000.0,
        contribution_amount=0.0,
        contribution_frequency=ContributionFrequency.NONE,
        fee_bps=0.0,
        fee_fixed=0.0,
        slippage_bps=0.0,
        seed=1,
    )
    specs = [
        {"strategy_id": "eq", "type": "equal_weight", "rebalance_frequency": "daily"}
    ]
    streamed = run_simulation_streaming(
        data_path=path,
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 4),
        strategy_specs=specs,
        settings=settings,
    )

    final_equity = streamed.daily_records_by_strategy["eq"][-1].total_equity
    # Manual check: 1000 -> 1500 on day2, then 2250 on day3.
    assert round(final_equity, 8) == 2250.0


def test_disappearing_symbol_is_written_off_not_revived(tmp_path: Path) -> None:
    path = tmp_path / "reappear.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]
        )
        writer.writerow(["2020-01-02", "AAA", 10, 10, 10, 10, 100, 0, 0])
        writer.writerow(["2020-01-02", "BBB", 10, 10, 10, 10, 100, 0, 0])
        writer.writerow(["2020-01-03", "AAA", 10, 10, 10, 10, 100, 0, 0])  # BBB missing
        writer.writerow(["2020-01-04", "AAA", 10, 10, 10, 10, 100, 0, 0])
        writer.writerow(["2020-01-04", "BBB", 1000, 1000, 1000, 1000, 100, 0, 0])  # BBB reappears huge

    settings = RunSettings(
        initial_capital=1000.0,
        contribution_amount=0.0,
        contribution_frequency=ContributionFrequency.NONE,
        fee_bps=0.0,
        fee_fixed=0.0,
        slippage_bps=0.0,
        seed=1,
    )
    specs = [
        {"strategy_id": "eq", "type": "equal_weight", "rebalance_frequency": "daily"}
    ]
    streamed = run_simulation_streaming(
        data_path=path,
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 4),
        strategy_specs=specs,
        settings=settings,
    )
    # If stale positions were kept and revived, this would explode.
    assert streamed.daily_records_by_strategy["eq"][-1].total_equity < 10_000.0
