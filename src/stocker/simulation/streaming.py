"""Low-memory streaming simulation runner."""

from __future__ import annotations

import csv
import random
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterator

from stocker.engine.portfolio import Portfolio, RebalanceCosts, TradeFill
from stocker.simulation.config_parser import StrategySpec
from stocker.simulation.runner import (
    ContributionFrequency,
    DailyRecord,
    DatedTrade,
    RunSettings,
    SimulationResult,
)
from stocker.strategies.baseline import RebalanceFrequency, should_rebalance


def run_simulation_streaming(
    *,
    data_path: Path,
    start_date: date,
    end_date: date,
    strategy_specs: list[StrategySpec | dict[str, Any]],
    settings: RunSettings,
    progress_years: bool = False,
    min_price: float = 0.01,
    max_price: float = 100_000.0,
    min_volume: float = 0.0,
) -> SimulationResult:
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    states = [_build_state(spec=spec, settings=settings) for spec in strategy_specs]
    daily_by_strategy: dict[str, list[DailyRecord]] = {state.strategy_id: [] for state in states}
    dated_trades: list[DatedTrade] = []
    costs = RebalanceCosts(
        fee_bps=settings.fee_bps,
        fee_fixed=settings.fee_fixed,
        slippage_bps=settings.slippage_bps,
    )

    rolling_windows = sorted(
        {
            state.rolling_window
            for state in states
            if state.rolling_window is not None and state.rolling_window > 0
        }
    )
    rolling_store = _RollingMetricStore(rolling_windows)

    last_reported_year: int | None = None
    for trading_day, day in _iter_trading_days(
        data_path=data_path,
        start_date=start_date,
        end_date=end_date,
        min_price=min_price,
        max_price=max_price,
        min_volume=min_volume,
    ):
        if progress_years and trading_day.year != last_reported_year:
            print(f"[stream] year={trading_day.year}", flush=True)
            last_reported_year = trading_day.year

        day_prices = day.closes
        day_dividends = day.dividends
        day_dollar_volume = {
            symbol: day.closes[symbol] * max(day.volumes.get(symbol, 0.0), 0.0)
            for symbol in day.closes
        }
        for symbol in day_prices:
            rolling_store.update(symbol=symbol, value=day_dollar_volume[symbol])

        for state in states:
            _write_off_unpriced_holdings(state.portfolio, day_prices)
            state.portfolio.apply_dividends(day_dividends)
            if _should_contribute(
                last_contribution_date=state.last_contribution_date,
                current_date=trading_day,
                frequency=settings.contribution_frequency,
            ) and settings.contribution_amount > 0:
                state.portfolio.contribute(settings.contribution_amount)
                state.last_contribution_date = trading_day

            fills: list[TradeFill] = []
            if should_rebalance(
                state.last_rebalance_date,
                trading_day,
                state.rebalance_frequency,
            ):
                target_weights = _target_weights_for_strategy(
                    state=state,
                    trading_day=trading_day,
                    day=day,
                    rolling_store=rolling_store,
                    seed=settings.seed,
                )
                fills = state.portfolio.rebalance_to_weights(
                    target_weights=target_weights,
                    prices=day_prices,
                    costs=costs,
                )
                state.last_rebalance_date = trading_day
                dated_trades.extend(
                    DatedTrade(date=trading_day, strategy_id=state.strategy_id, fill=fill)
                    for fill in fills
                )

            market_value = state.portfolio.total_market_value(day_prices)
            equity = state.portfolio.cash + market_value
            previous_equity = state.previous_equity
            daily_return = (
                0.0
                if previous_equity is None or previous_equity == 0
                else (equity / previous_equity) - 1.0
            )
            turnover = (
                0.0
                if previous_equity is None or previous_equity == 0
                else sum(fill.gross_value for fill in fills) / previous_equity
            )
            state.previous_equity = equity
            daily_by_strategy[state.strategy_id].append(
                DailyRecord(
                    date=trading_day,
                    strategy_id=state.strategy_id,
                    cash=state.portfolio.cash,
                    positions_market_value=market_value,
                    total_equity=equity,
                    daily_return=daily_return,
                    cumulative_contributions=state.portfolio.cumulative_contributions,
                    cumulative_dividends=state.portfolio.cumulative_dividends,
                    trade_count_day=len(fills),
                    turnover_day=turnover,
                )
            )

    return SimulationResult(daily_records_by_strategy=daily_by_strategy, trades=dated_trades)


@dataclass(slots=True)
class _StreamingStrategyState:
    strategy_id: str
    strategy_type: str
    rebalance_frequency: RebalanceFrequency
    portfolio: Portfolio
    params: dict[str, Any]
    last_rebalance_date: date | None = None
    last_contribution_date: date | None = None
    previous_equity: float | None = None
    rolling_window: int | None = None


@dataclass(frozen=True, slots=True)
class _DayData:
    closes: dict[str, float]
    volumes: dict[str, float]
    dividends: dict[str, float]


class _RollingMetricStore:
    def __init__(self, windows: list[int]) -> None:
        self._windows = [w for w in windows if w > 0]
        self._queues: dict[int, dict[str, deque[float]]] = {
            window: defaultdict(lambda w=window: deque(maxlen=w))
            for window in self._windows
        }
        self._sums: dict[int, dict[str, float]] = {
            window: defaultdict(float) for window in self._windows
        }

    def update(self, *, symbol: str, value: float) -> None:
        for window in self._windows:
            queue = self._queues[window][symbol]
            if len(queue) == queue.maxlen:
                self._sums[window][symbol] -= queue[0]
            queue.append(value)
            self._sums[window][symbol] += value

    def value(self, *, symbol: str, window: int) -> float:
        return self._sums.get(window, {}).get(symbol, 0.0)


def _iter_trading_days(
    *,
    data_path: Path,
    start_date: date,
    end_date: date,
    min_price: float,
    max_price: float,
    min_volume: float,
) -> Iterator[tuple[date, _DayData]]:
    current_day: date | None = None
    closes: dict[str, float] = {}
    volumes: dict[str, float] = {}
    dividends: dict[str, float] = {}
    with data_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_day = date.fromisoformat(row["Date"])
            if row_day < start_date or row_day > end_date:
                continue
            if current_day is None:
                current_day = row_day
            elif row_day != current_day:
                if closes:
                    yield (
                        current_day,
                        _DayData(
                            closes=closes,
                            volumes=volumes,
                            dividends=dividends,
                        ),
                    )
                current_day = row_day
                closes = {}
                volumes = {}
                dividends = {}

            symbol = row["Ticker"].upper()
            close = _parse_optional_float(row.get("Close"))
            if close is None or close <= 0:
                continue
            volume = _parse_optional_float(row.get("Volume"))
            if close < min_price or close > max_price:
                continue
            if volume is None or volume < min_volume:
                continue
            div = _parse_optional_float(row.get("Dividends"))
            closes[symbol] = close
            volumes[symbol] = volume
            dividends[symbol] = 0.0 if div is None else div

        if current_day is not None and closes:
            yield (
                current_day,
                _DayData(closes=closes, volumes=volumes, dividends=dividends),
            )


def _parse_optional_float(raw: str | None) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _build_state(
    *,
    spec: StrategySpec | dict[str, Any],
    settings: RunSettings,
) -> _StreamingStrategyState:
    resolved = _to_spec(spec)
    params = dict(resolved.params)
    strategy_type = resolved.strategy_type
    rolling_window: int | None = None
    if strategy_type == "sp500_proxy":
        rolling_window = int(params.get("rolling_window", 252))
    elif strategy_type in {"top_n_ranked", "bottom_n_ranked"} and str(
        params.get("metric", "close_price")
    ) == "rolling_dollar_volume_252d":
        rolling_window = int(params.get("rolling_window", 252))
    return _StreamingStrategyState(
        strategy_id=resolved.strategy_id,
        strategy_type=strategy_type,
        rebalance_frequency=RebalanceFrequency(resolved.rebalance_frequency),
        portfolio=Portfolio(initial_cash=settings.initial_capital),
        params=params,
        rolling_window=rolling_window,
    )


def _to_spec(raw: StrategySpec | dict[str, Any]) -> StrategySpec:
    if isinstance(raw, StrategySpec):
        return raw
    if not isinstance(raw, dict):
        raise ValueError("strategy spec must be StrategySpec or dict")
    return StrategySpec(
        strategy_id=str(raw["strategy_id"]),
        strategy_type=str(raw["type"]),
        rebalance_frequency=str(raw.get("rebalance_frequency", "daily")),
        params=dict(raw.get("params", {})),
    )


def _target_weights_for_strategy(
    *,
    state: _StreamingStrategyState,
    trading_day: date,
    day: _DayData,
    rolling_store: _RollingMetricStore,
    seed: int,
) -> dict[str, float]:
    strategy_type = state.strategy_type
    if strategy_type == "equal_weight":
        return _equal_weights(sorted(day.closes))
    if strategy_type == "explicit_symbols":
        requested = {symbol.upper() for symbol in state.params.get("symbols", [])}
        selected = sorted(requested & set(day.closes))
        return _equal_weights(selected)
    if strategy_type == "random_n":
        n = int(state.params.get("n", 0))
        if n <= 0:
            return {}
        candidates = sorted(day.closes)
        if not candidates:
            return {}
        sample_size = min(n, len(candidates))
        strategy_seed = int(state.params.get("seed", seed))
        rng = random.Random(strategy_seed + trading_day.toordinal())
        return _equal_weights(sorted(rng.sample(candidates, sample_size)))
    if strategy_type == "top_n_ranked":
        n = int(state.params.get("n", 0))
        metric = str(state.params.get("metric", "close_price"))
        proportional = bool(state.params.get("proportional", False))
        metrics = _metrics_for_day(
            metric=metric,
            day=day,
            rolling_store=rolling_store,
            rolling_window=int(state.params.get("rolling_window", 252)),
        )
        return _ranked_weights(metrics=metrics, n=n, top=True, proportional=proportional)
    if strategy_type == "bottom_n_ranked":
        n = int(state.params.get("n", 0))
        metric = str(state.params.get("metric", "close_price"))
        metrics = _metrics_for_day(
            metric=metric,
            day=day,
            rolling_store=rolling_store,
            rolling_window=int(state.params.get("rolling_window", 252)),
        )
        return _ranked_weights(metrics=metrics, n=n, top=False, proportional=False)
    if strategy_type == "sp500_proxy":
        top_n = int(state.params.get("top_n", 500))
        rolling_window = int(state.params.get("rolling_window", 252))
        metrics = _metrics_for_day(
            metric="rolling_dollar_volume_252d",
            day=day,
            rolling_store=rolling_store,
            rolling_window=rolling_window,
        )
        return _ranked_weights(metrics=metrics, n=top_n, top=True, proportional=True)
    raise ValueError(f"unknown strategy type: {strategy_type}")


def _metrics_for_day(
    *,
    metric: str,
    day: _DayData,
    rolling_store: _RollingMetricStore,
    rolling_window: int,
) -> dict[str, float]:
    if metric == "close_price":
        return {s: p for s, p in day.closes.items() if p > 0}
    if metric == "dollar_volume_1d":
        return {
            s: day.closes[s] * max(day.volumes.get(s, 0.0), 0.0)
            for s in day.closes
            if day.closes[s] > 0
        }
    if metric == "rolling_dollar_volume_252d":
        out: dict[str, float] = {}
        for symbol in day.closes:
            value = rolling_store.value(symbol=symbol, window=rolling_window)
            if value > 0:
                out[symbol] = value
        return out
    raise ValueError(f"unsupported metric: {metric}")


def _equal_weights(symbols: list[str]) -> dict[str, float]:
    if not symbols:
        return {}
    w = 1.0 / len(symbols)
    return {s: w for s in symbols}


def _ranked_weights(
    *,
    metrics: dict[str, float],
    n: int,
    top: bool,
    proportional: bool,
) -> dict[str, float]:
    if n <= 0:
        return {}
    ranked = sorted(
        ((symbol, value) for symbol, value in metrics.items() if value > 0),
        key=lambda item: item[1],
        reverse=top,
    )[:n]
    if not ranked:
        return {}
    if not proportional:
        return _equal_weights([symbol for symbol, _ in ranked])
    total = sum(value for _, value in ranked)
    if total <= 0:
        return {}
    return {symbol: value / total for symbol, value in ranked}


def _should_contribute(
    *,
    last_contribution_date: date | None,
    current_date: date,
    frequency: ContributionFrequency,
) -> bool:
    if frequency is ContributionFrequency.NONE:
        return False
    if last_contribution_date is None:
        return True
    if current_date <= last_contribution_date:
        return False
    if frequency is ContributionFrequency.DAILY:
        return True
    if frequency is ContributionFrequency.MONTHLY:
        return (
            current_date.year != last_contribution_date.year
            or current_date.month != last_contribution_date.month
        )
    if frequency is ContributionFrequency.YEARLY:
        return current_date.year != last_contribution_date.year
    raise ValueError(f"unsupported contribution frequency: {frequency}")


def _write_off_unpriced_holdings(portfolio: Portfolio, prices: dict[str, float]) -> None:
    stale_symbols = [symbol for symbol in portfolio.holdings if symbol not in prices]
    for symbol in stale_symbols:
        portfolio.holdings.pop(symbol, None)
