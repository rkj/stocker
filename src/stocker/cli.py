"""CLI entrypoint for Stocker."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import Sequence

from stocker.config import ContributionFrequency, SimulationConfig


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
    )


def main(argv: Sequence[str] | None = None) -> int:
    cfg = parse_args(argv if argv is not None else sys.argv[1:])
    print(
        "stocker scaffold: data=%s start=%s end=%s initial=%.2f"
        % (cfg.data_path, cfg.start_date, cfg.end_date, cfg.initial_capital)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
