"""CSV/JSON export helpers for simulation outputs."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import pstdev
from typing import Any

from stocker.simulation.runner import DailyRecord, SimulationResult


@dataclass(frozen=True, slots=True)
class OutputPaths:
    daily_equity: Path
    trades: Path
    annual_summary: Path
    terminal_summary: Path
    manifest: Path


def write_run_outputs(
    *,
    result: SimulationResult,
    output_dir: Path,
    manifest: dict[str, Any],
) -> OutputPaths:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = OutputPaths(
        daily_equity=output_dir / "daily_equity.csv",
        trades=output_dir / "trades.csv",
        annual_summary=output_dir / "annual_summary.csv",
        terminal_summary=output_dir / "terminal_summary.csv",
        manifest=output_dir / "run_manifest.json",
    )

    _write_daily_equity(paths.daily_equity, result.daily_records_by_strategy)
    _write_trades(paths.trades, result)
    _write_annual_summary(paths.annual_summary, result.daily_records_by_strategy)
    _write_terminal_summary(paths.terminal_summary, result.daily_records_by_strategy, result)
    paths.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return paths


def _write_daily_equity(path: Path, by_strategy: dict[str, list[DailyRecord]]) -> None:
    fieldnames = [
        "date",
        "strategy_id",
        "cash",
        "positions_market_value",
        "total_equity",
        "daily_return",
        "cumulative_return",
        "contribution_cumulative",
        "trade_count_day",
        "turnover_day",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for strategy_id in sorted(by_strategy):
            records = by_strategy[strategy_id]
            if not records:
                continue
            first_equity = records[0].total_equity
            for record in records:
                cumulative_return = 0.0 if first_equity == 0 else (record.total_equity / first_equity) - 1.0
                writer.writerow(
                    {
                        "date": record.date.isoformat(),
                        "strategy_id": strategy_id,
                        "cash": f"{record.cash:.10f}",
                        "positions_market_value": f"{record.positions_market_value:.10f}",
                        "total_equity": f"{record.total_equity:.10f}",
                        "daily_return": f"{record.daily_return:.10f}",
                        "cumulative_return": f"{cumulative_return:.10f}",
                        "contribution_cumulative": f"{record.cumulative_contributions:.10f}",
                        "trade_count_day": record.trade_count_day,
                        "turnover_day": f"{record.turnover_day:.10f}",
                    }
                )


def _write_trades(path: Path, result: SimulationResult) -> None:
    fieldnames = [
        "date",
        "strategy_id",
        "symbol",
        "side",
        "shares",
        "price",
        "gross_value",
        "slippage_cost",
        "fee_cost",
        "net_cash_impact",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for trade in result.trades:
            writer.writerow(
                {
                    "date": trade.date.isoformat(),
                    "strategy_id": trade.strategy_id,
                    "symbol": trade.fill.symbol,
                    "side": trade.fill.side,
                    "shares": f"{trade.fill.shares:.10f}",
                    "price": f"{trade.fill.price:.10f}",
                    "gross_value": f"{trade.fill.gross_value:.10f}",
                    "slippage_cost": f"{trade.fill.slippage_cost:.10f}",
                    "fee_cost": f"{trade.fill.fee_cost:.10f}",
                    "net_cash_impact": f"{trade.fill.net_cash_impact:.10f}",
                }
            )


def _write_annual_summary(path: Path, by_strategy: dict[str, list[DailyRecord]]) -> None:
    fieldnames = [
        "strategy_id",
        "year",
        "start_equity",
        "end_equity",
        "net_contributions_year",
        "return_year",
        "max_drawdown_year",
        "volatility_year",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for strategy_id in sorted(by_strategy):
            rows = by_strategy[strategy_id]
            by_year: dict[int, list[DailyRecord]] = {}
            for row in rows:
                by_year.setdefault(row.date.year, []).append(row)
            for year in sorted(by_year):
                yearly = by_year[year]
                start = yearly[0]
                end = yearly[-1]
                start_contrib = start.cumulative_contributions
                prior_contrib = 0.0
                if rows and rows[0].date.year == year:
                    prior_contrib = 0.0
                else:
                    # Find last contribution level from prior year.
                    for r in rows:
                        if r.date.year < year:
                            prior_contrib = r.cumulative_contributions
                net_contrib = end.cumulative_contributions - prior_contrib
                yearly_returns = [r.daily_return for r in yearly]
                writer.writerow(
                    {
                        "strategy_id": strategy_id,
                        "year": year,
                        "start_equity": f"{start.total_equity:.10f}",
                        "end_equity": f"{end.total_equity:.10f}",
                        "net_contributions_year": f"{net_contrib:.10f}",
                        "return_year": f"{_period_return(start.total_equity, end.total_equity):.10f}",
                        "max_drawdown_year": f"{_max_drawdown(yearly):.10f}",
                        "volatility_year": f"{_annualized_volatility(yearly_returns):.10f}",
                    }
                )


def _write_terminal_summary(
    path: Path,
    by_strategy: dict[str, list[DailyRecord]],
    result: SimulationResult,
) -> None:
    fieldnames = [
        "strategy_id",
        "final_equity",
        "total_contributions",
        "net_profit",
        "cagr",
        "max_drawdown",
        "annualized_volatility",
        "sharpe_proxy",
        "total_trades",
        "avg_turnover",
    ]
    trades_by_strategy: dict[str, int] = {}
    for trade in result.trades:
        trades_by_strategy[trade.strategy_id] = trades_by_strategy.get(trade.strategy_id, 0) + 1

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for strategy_id in sorted(by_strategy):
            records = by_strategy[strategy_id]
            if not records:
                continue
            first = records[0]
            last = records[-1]
            total_contrib = last.cumulative_contributions
            invested = first.total_equity + total_contrib
            net_profit = last.total_equity - invested
            returns = [r.daily_return for r in records]
            vol = _annualized_volatility(returns)
            cagr = _cagr(
                start_date=first.date,
                end_date=last.date,
                start_value=first.total_equity,
                end_value=last.total_equity,
            )
            sharpe_proxy = 0.0 if vol == 0 else cagr / vol
            avg_turnover = sum(r.turnover_day for r in records) / len(records)
            writer.writerow(
                {
                    "strategy_id": strategy_id,
                    "final_equity": f"{last.total_equity:.10f}",
                    "total_contributions": f"{total_contrib:.10f}",
                    "net_profit": f"{net_profit:.10f}",
                    "cagr": f"{cagr:.10f}",
                    "max_drawdown": f"{_max_drawdown(records):.10f}",
                    "annualized_volatility": f"{vol:.10f}",
                    "sharpe_proxy": f"{sharpe_proxy:.10f}",
                    "total_trades": trades_by_strategy.get(strategy_id, 0),
                    "avg_turnover": f"{avg_turnover:.10f}",
                }
            )


def _period_return(start_value: float, end_value: float) -> float:
    if start_value == 0:
        return 0.0
    return (end_value / start_value) - 1.0


def _max_drawdown(records: list[DailyRecord]) -> float:
    peak = -math.inf
    max_dd = 0.0
    for row in records:
        peak = max(peak, row.total_equity)
        if peak <= 0:
            continue
        drawdown = (row.total_equity / peak) - 1.0
        max_dd = min(max_dd, drawdown)
    return max_dd


def _annualized_volatility(daily_returns: list[float]) -> float:
    if len(daily_returns) <= 1:
        return 0.0
    return pstdev(daily_returns) * math.sqrt(252.0)


def _cagr(
    *,
    start_date: date,
    end_date: date,
    start_value: float,
    end_value: float,
) -> float:
    if start_value <= 0:
        return 0.0
    days = (end_date - start_date).days
    if days <= 0:
        return 0.0
    years = days / 365.25
    if years <= 0:
        return 0.0
    return (end_value / start_value) ** (1.0 / years) - 1.0

