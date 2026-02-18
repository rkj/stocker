from __future__ import annotations

from datetime import date
from pathlib import Path
import csv

from stocker.data.market_data import load_market_data
from stocker.reporting.exports import write_run_outputs
from stocker.simulation.runner import ContributionFrequency, RunSettings, run_simulation


def test_write_run_outputs_creates_required_files(tmp_path: Path, synthetic_market_csv: Path) -> None:
    market = load_market_data(
        input_path=synthetic_market_csv,
        start_date=date(1980, 1, 2),
        end_date=date(1980, 1, 10),
    )
    result = run_simulation(
        market=market,
        strategy_specs=[{"strategy_id": "eq_daily", "type": "equal_weight"}],
        settings=RunSettings(
            initial_capital=10_000.0,
            contribution_amount=0.0,
            contribution_frequency=ContributionFrequency.NONE,
            fee_bps=0.0,
            fee_fixed=0.0,
            slippage_bps=0.0,
        ),
    )

    paths = write_run_outputs(
        result=result,
        output_dir=tmp_path,
        manifest={"window": "1980-01-02..1980-01-10"},
    )

    assert paths.daily_equity.exists()
    assert paths.trades.exists()
    assert paths.annual_summary.exists()
    assert paths.terminal_summary.exists()
    assert paths.manifest.exists()

    daily_lines = paths.daily_equity.read_text(encoding="utf-8").strip().splitlines()
    assert daily_lines[0].startswith("date,strategy_id")
    assert len(daily_lines) > 2


def test_annual_and_terminal_summaries_include_strategy_id(
    tmp_path: Path, synthetic_market_csv: Path
) -> None:
    market = load_market_data(
        input_path=synthetic_market_csv,
        start_date=date(1980, 1, 2),
        end_date=date(1980, 3, 10),
    )
    result = run_simulation(
        market=market,
        strategy_specs=[{"strategy_id": "eq_daily", "type": "equal_weight"}],
        settings=RunSettings(
            initial_capital=10_000.0,
            contribution_amount=100.0,
            contribution_frequency=ContributionFrequency.MONTHLY,
            fee_bps=0.0,
            fee_fixed=0.0,
            slippage_bps=0.0,
        ),
    )

    paths = write_run_outputs(result=result, output_dir=tmp_path, manifest={})
    annual = paths.annual_summary.read_text(encoding="utf-8")
    terminal = paths.terminal_summary.read_text(encoding="utf-8")

    assert "strategy_id" in annual
    assert "eq_daily" in annual
    assert "strategy_id" in terminal
    assert "eq_daily" in terminal


def test_reporting_returns_are_flow_adjusted_with_contributions(tmp_path: Path) -> None:
    csv_path = tmp_path / "flat.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Date", "Ticker", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits"]
        )
        writer.writerow(["2020-01-02", "AAA", 10, 10, 10, 10, 100, 0, 0])
        writer.writerow(["2020-01-03", "AAA", 10, 10, 10, 10, 100, 0, 0])
        writer.writerow(["2020-01-06", "AAA", 10, 10, 10, 10, 100, 0, 0])

    market = load_market_data(
        input_path=csv_path,
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 6),
    )
    result = run_simulation(
        market=market,
        strategy_specs=[{"strategy_id": "aaa", "type": "explicit_symbols", "params": {"symbols": ["AAA"]}}],
        settings=RunSettings(
            initial_capital=1000.0,
            contribution_amount=100.0,
            contribution_frequency=ContributionFrequency.DAILY,
            fee_bps=0.0,
            fee_fixed=0.0,
            slippage_bps=0.0,
        ),
    )
    paths = write_run_outputs(result=result, output_dir=tmp_path, manifest={})

    annual_row = next(csv.DictReader(paths.annual_summary.open(newline="", encoding="utf-8")))
    terminal_row = next(csv.DictReader(paths.terminal_summary.open(newline="", encoding="utf-8")))
    # Flat prices + only external cash flows => zero strategy return.
    assert round(float(annual_row["return_year"]), 10) == 0.0
    assert round(float(terminal_row["cagr"]), 10) == 0.0
