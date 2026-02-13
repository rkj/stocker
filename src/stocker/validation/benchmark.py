"""Streaming benchmark validation for S&P-style proxy portfolios."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    start_date: date
    end_date: date
    trading_days: int
    final_equity: float
    cagr: float
    annualized_volatility: float
    max_drawdown: float


def run_sp500_proxy_streaming(
    *,
    data_path: Path,
    start_date: date,
    end_date: date,
    initial_capital: float,
    top_n: int = 500,
    rolling_window: int = 252,
    fee_bps: float = 0.0,
    fee_fixed: float = 0.0,
    slippage_bps: float = 0.0,
) -> BenchmarkResult:
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")

    rolling_values: dict[str, deque[float]] = defaultdict(
        lambda: deque(maxlen=rolling_window)
    )
    rolling_sums: dict[str, float] = defaultdict(float)
    last_close: dict[str, float] = {}
    holdings: dict[str, float] = {}
    cash = initial_capital
    prior_equity: float | None = None

    daily_returns: list[float] = []
    max_drawdown = 0.0
    peak_equity = -math.inf
    day_count = 0
    first_day: date | None = None
    last_day: date | None = None

    current_day: date | None = None
    day_closes: dict[str, float] = {}
    day_metrics: dict[str, float] = {}
    day_dividends: dict[str, float] = {}

    with data_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_day = date.fromisoformat(row["Date"])
            if row_day < start_date or row_day > end_date:
                continue

            if current_day is None:
                current_day = row_day
            elif row_day != current_day:
                cash, holdings, prior_equity, peak_equity, max_drawdown, day_return = _finalize_day(
                    day=current_day,
                    cash=cash,
                    holdings=holdings,
                    last_close=last_close,
                    day_closes=day_closes,
                    day_metrics=day_metrics,
                    day_dividends=day_dividends,
                    prior_equity=prior_equity,
                    top_n=top_n,
                    fee_bps=fee_bps,
                    fee_fixed=fee_fixed,
                    slippage_bps=slippage_bps,
                    peak_equity=peak_equity,
                    max_drawdown=max_drawdown,
                )
                if first_day is None:
                    first_day = current_day
                last_day = current_day
                day_count += 1
                if day_return is not None:
                    daily_returns.append(day_return)
                current_day = row_day
                day_closes = {}
                day_metrics = {}
                day_dividends = {}

            symbol = row["Ticker"].upper()
            try:
                close = float(row["Close"])
            except (TypeError, ValueError):
                continue
            try:
                volume = float(row["Volume"])
            except (TypeError, ValueError):
                volume = 0.0
            try:
                dividend = float(row["Dividends"])
            except (TypeError, ValueError):
                dividend = 0.0
            if close <= 0:
                continue

            dollar_volume = close * max(volume, 0.0)
            queue = rolling_values[symbol]
            if len(queue) == rolling_window:
                rolling_sums[symbol] -= queue[0]
            queue.append(dollar_volume)
            rolling_sums[symbol] += dollar_volume

            day_closes[symbol] = close
            day_metrics[symbol] = rolling_sums[symbol]
            day_dividends[symbol] = dividend

        if current_day is not None and day_closes:
            cash, holdings, prior_equity, peak_equity, max_drawdown, day_return = _finalize_day(
                day=current_day,
                cash=cash,
                holdings=holdings,
                last_close=last_close,
                day_closes=day_closes,
                day_metrics=day_metrics,
                day_dividends=day_dividends,
                prior_equity=prior_equity,
                top_n=top_n,
                fee_bps=fee_bps,
                fee_fixed=fee_fixed,
                slippage_bps=slippage_bps,
                peak_equity=peak_equity,
                max_drawdown=max_drawdown,
            )
            if first_day is None:
                first_day = current_day
            last_day = current_day
            day_count += 1
            if day_return is not None:
                daily_returns.append(day_return)

    if first_day is None or last_day is None or prior_equity is None:
        raise ValueError("no rows matched requested date range")

    years = max((last_day - first_day).days / 365.25, 1.0 / 365.25)
    cagr = (prior_equity / initial_capital) ** (1.0 / years) - 1.0
    ann_vol = _annualized_volatility(daily_returns)
    return BenchmarkResult(
        start_date=first_day,
        end_date=last_day,
        trading_days=day_count,
        final_equity=prior_equity,
        cagr=cagr,
        annualized_volatility=ann_vol,
        max_drawdown=max_drawdown,
    )


def _finalize_day(
    *,
    day: date,
    cash: float,
    holdings: dict[str, float],
    last_close: dict[str, float],
    day_closes: dict[str, float],
    day_metrics: dict[str, float],
    day_dividends: dict[str, float],
    prior_equity: float | None,
    top_n: int,
    fee_bps: float,
    fee_fixed: float,
    slippage_bps: float,
    peak_equity: float,
    max_drawdown: float,
) -> tuple[float, dict[str, float], float, float, float, float | None]:
    # Update reference prices first.
    last_close.update(day_closes)

    # Credit dividends for currently held symbols on their ex-dividend date.
    for symbol, shares in holdings.items():
        div = day_dividends.get(symbol, 0.0)
        if shares > 0 and div > 0:
            cash += shares * div

    equity = cash + sum(shares * last_close.get(symbol, 0.0) for symbol, shares in holdings.items())
    if equity < 0:
        equity = 0.0

    ranked = sorted(
        ((symbol, metric) for symbol, metric in day_metrics.items() if metric > 0),
        key=lambda item: item[1],
        reverse=True,
    )
    selected = ranked[:top_n]
    metric_total = sum(metric for _, metric in selected)
    target_weights = (
        {symbol: metric / metric_total for symbol, metric in selected}
        if metric_total > 0
        else {}
    )

    symbols = set(holdings) | set(target_weights)
    for symbol in symbols:
        price = day_closes.get(symbol) or last_close.get(symbol)
        if price is None or price <= 0:
            continue
        current_shares = holdings.get(symbol, 0.0)
        current_value = current_shares * price
        target_value = target_weights.get(symbol, 0.0) * equity
        delta_value = target_value - current_value
        if abs(delta_value) < 1e-12:
            continue

        gross = abs(delta_value)
        trade_cost = gross * ((fee_bps + slippage_bps) / 10_000.0) + fee_fixed
        if delta_value > 0:
            cash -= gross + trade_cost
        else:
            cash += gross - trade_cost

        new_shares = current_shares + (delta_value / price)
        if abs(new_shares) < 1e-10:
            holdings.pop(symbol, None)
        else:
            holdings[symbol] = new_shares

    end_equity = cash + sum(shares * last_close.get(symbol, 0.0) for symbol, shares in holdings.items())
    day_return = None
    if prior_equity not in (None, 0):
        day_return = (end_equity / prior_equity) - 1.0
    peak_equity = max(peak_equity, end_equity)
    if peak_equity > 0:
        max_drawdown = min(max_drawdown, (end_equity / peak_equity) - 1.0)
    return cash, holdings, end_equity, peak_equity, max_drawdown, day_return


def _annualized_volatility(daily_returns: list[float]) -> float:
    if len(daily_returns) <= 1:
        return 0.0
    mean = sum(daily_returns) / len(daily_returns)
    variance = sum((value - mean) ** 2 for value in daily_returns) / len(daily_returns)
    return math.sqrt(variance) * math.sqrt(252.0)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stocker-benchmark",
        description="Run streaming S&P-style benchmark validation.",
    )
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--initial-capital", type=float, default=10_000.0)
    parser.add_argument("--top-n", type=int, default=500)
    parser.add_argument("--rolling-window", type=int, default=252)
    parser.add_argument("--fee-bps", type=float, default=0.0)
    parser.add_argument("--fee-fixed", type=float, default=0.0)
    parser.add_argument("--slippage-bps", type=float, default=0.0)
    parser.add_argument("--output-json")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = run_sp500_proxy_streaming(
        data_path=Path(args.data_path),
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        initial_capital=args.initial_capital,
        top_n=args.top_n,
        rolling_window=args.rolling_window,
        fee_bps=args.fee_bps,
        fee_fixed=args.fee_fixed,
        slippage_bps=args.slippage_bps,
    )
    payload = {
        "start_date": result.start_date.isoformat(),
        "end_date": result.end_date.isoformat(),
        "trading_days": result.trading_days,
        "final_equity": result.final_equity,
        "cagr": result.cagr,
        "annualized_volatility": result.annualized_volatility,
        "max_drawdown": result.max_drawdown,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.output_json:
        Path(args.output_json).write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
