"""CLI entrypoint for Stocker."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

from stocker.config import ContributionFrequency, SimulationConfig
from stocker.data.market_data import load_market_data
from stocker.reporting.exports import write_run_outputs
from stocker.simulation.config_parser import parse_strategy_file
from stocker.simulation.runner import (
    ContributionFrequency as RunnerContributionFrequency,
    RunSettings,
    run_simulation,
)
from stocker.simulation.streaming import run_simulation_streaming


def _date_type(value: str) -> date:
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stocker",
        description="Run stock strategy simulations over historical data.",
    )
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--start-date", type=_date_type, required=True)
    parser.add_argument("--end-date", type=_date_type, required=True)
    parser.add_argument("--initial-capital", type=float, required=True)
    parser.add_argument("--contribution-amount", type=float, default=0.0)
    parser.add_argument(
        "--contribution-frequency",
        choices=[f.value for f in ContributionFrequency],
        default=ContributionFrequency.NONE.value,
    )
    parser.add_argument("--fee-bps", type=float, default=0.0)
    parser.add_argument("--fee-fixed", type=float, default=0.0)
    parser.add_argument("--slippage-bps", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--strategy-file")
    parser.add_argument("--progress", action="store_true")
    parser.add_argument("--engine", choices=["streaming", "in_memory"], default="streaming")
    parser.add_argument("--min-price", type=float, default=0.01)
    parser.add_argument("--max-price", type=float, default=100_000.0)
    parser.add_argument("--min-volume", type=float, default=0.0)
    return parser


def parse_args(argv: Sequence[str]) -> SimulationConfig:
    args = build_parser().parse_args(argv)
    return SimulationConfig(
        data_path=args.data_path,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.initial_capital,
        contribution_amount=args.contribution_amount,
        contribution_frequency=ContributionFrequency(args.contribution_frequency),
        fee_bps=args.fee_bps,
        fee_fixed=args.fee_fixed,
        slippage_bps=args.slippage_bps,
        seed=args.seed,
        output_dir=args.output_dir,
        strategy_file=args.strategy_file,
        progress=args.progress,
        engine=args.engine,
        min_price=args.min_price,
        max_price=args.max_price,
        min_volume=args.min_volume,
    )


def main(argv: Sequence[str] | None = None) -> int:
    cfg = parse_args(argv if argv is not None else sys.argv[1:])
    strategy_specs = (
        parse_strategy_file(Path(cfg.strategy_file))
        if cfg.strategy_file
        else []
    )
    if not strategy_specs:
        strategy_specs = [
            {
                "strategy_id": "equal_weight_daily_default",
                "type": "equal_weight",
                "rebalance_frequency": "daily",
            }
        ]

    run_settings = RunSettings(
        initial_capital=cfg.initial_capital,
        contribution_amount=cfg.contribution_amount,
        contribution_frequency=RunnerContributionFrequency(
            cfg.contribution_frequency.value
        ),
        fee_bps=cfg.fee_bps,
        fee_fixed=cfg.fee_fixed,
        slippage_bps=cfg.slippage_bps,
        seed=cfg.seed,
    )
    if cfg.engine == "streaming":
        result = run_simulation_streaming(
            data_path=Path(cfg.data_path),
            start_date=cfg.start_date,
            end_date=cfg.end_date,
            strategy_specs=strategy_specs,
            settings=run_settings,
            progress_years=cfg.progress,
            min_price=cfg.min_price,
            max_price=cfg.max_price,
            min_volume=cfg.min_volume,
        )
    else:
        market = load_market_data(
            input_path=Path(cfg.data_path),
            start_date=cfg.start_date,
            end_date=cfg.end_date,
            progress_years=cfg.progress,
            min_price=cfg.min_price,
            max_price=cfg.max_price,
            min_volume=cfg.min_volume,
        )
        result = run_simulation(
            market=market,
            strategy_specs=strategy_specs,
            settings=run_settings,
            progress_years=cfg.progress,
        )
    manifest = {
        "data_path": cfg.data_path,
        "start_date": cfg.start_date.isoformat(),
        "end_date": cfg.end_date.isoformat(),
        "initial_capital": cfg.initial_capital,
        "contribution_amount": cfg.contribution_amount,
        "contribution_frequency": cfg.contribution_frequency.value,
        "fee_bps": cfg.fee_bps,
        "fee_fixed": cfg.fee_fixed,
        "slippage_bps": cfg.slippage_bps,
        "seed": cfg.seed,
        "strategy_file": cfg.strategy_file,
        "strategy_count": len(strategy_specs),
        "engine": cfg.engine,
        "min_price": cfg.min_price,
        "max_price": cfg.max_price,
        "min_volume": cfg.min_volume,
    }
    outputs = write_run_outputs(
        result=result,
        output_dir=Path(cfg.output_dir),
        manifest=manifest,
    )
    final_rows = []
    for strategy_id, records in result.daily_records_by_strategy.items():
        if records:
            final_rows.append((strategy_id, records[-1].total_equity))
    final_rows.sort(key=lambda row: row[1], reverse=True)
    print("run complete")
    print(
        json.dumps(
            {"outputs": {k: str(v) for k, v in asdict(outputs).items()}},
            indent=2,
        )
    )
    for strategy_id, final_equity in final_rows:
        print(f"{strategy_id}: final_equity={final_equity:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
