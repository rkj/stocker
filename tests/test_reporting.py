from __future__ import annotations

from datetime import date
from pathlib import Path

from stocker.data.market_data import load_market_data
from stocker.reporting.exports import write_run_outputs
from stocker.simulation.runner import ContributionFrequency, RunSettings, run_simulation


FIXTURE_PATH = Path("tests/fixtures/sample_stock_data.csv")


def test_write_run_outputs_creates_required_files(tmp_path: Path) -> None:
    market = load_market_data(
        input_path=FIXTURE_PATH,
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


def test_annual_and_terminal_summaries_include_strategy_id(tmp_path: Path) -> None:
    market = load_market_data(
        input_path=FIXTURE_PATH,
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

