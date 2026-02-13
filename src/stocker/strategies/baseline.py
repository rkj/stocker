"""Baseline weighting strategies and rebalance cadence helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from stocker.data.market_data import MarketData


class RebalanceFrequency(str, Enum):
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    NEVER = "never"


def should_rebalance(
    last_rebalance_date: date | None,
    current_date: date,
    frequency: RebalanceFrequency,
) -> bool:
    if last_rebalance_date is None:
        return True
    if current_date <= last_rebalance_date:
        return False

    if frequency is RebalanceFrequency.DAILY:
        return True
    if frequency is RebalanceFrequency.MONTHLY:
        return (
            current_date.year != last_rebalance_date.year
            or current_date.month != last_rebalance_date.month
        )
    if frequency is RebalanceFrequency.YEARLY:
        return current_date.year != last_rebalance_date.year
    if frequency is RebalanceFrequency.NEVER:
        return False
    raise ValueError(f"unsupported frequency: {frequency}")


@dataclass(slots=True)
class EqualWeightStrategy:
    rebalance_frequency: RebalanceFrequency = RebalanceFrequency.DAILY

    def target_weights(self, *, market: MarketData, trading_day: date) -> dict[str, float]:
        symbols = sorted(market.bars_on(trading_day).keys())
        return equal_weights(symbols)


@dataclass(slots=True)
class Sp500ProxyStrategy:
    top_n: int = 500
    rolling_window: int = 252
    _cached_window: dict[date, dict[str, float]] | None = field(default=None, init=False)

    def target_weights(self, *, market: MarketData, trading_day: date) -> dict[str, float]:
        if self.top_n <= 0:
            raise ValueError("top_n must be positive")
        if self._cached_window is None:
            self._cached_window = market.rolling_dollar_volume(window=self.rolling_window)
        metrics = self._cached_window.get(trading_day, {})
        return proportional_top_n_weights(metrics=metrics, top_n=self.top_n)


def equal_weights(symbols: list[str]) -> dict[str, float]:
    if not symbols:
        return {}
    weight = 1.0 / len(symbols)
    return {symbol: weight for symbol in symbols}


def proportional_top_n_weights(
    *,
    metrics: dict[str, float],
    top_n: int,
) -> dict[str, float]:
    ranked = sorted(
        ((symbol, value) for symbol, value in metrics.items() if value > 0),
        key=lambda item: item[1],
        reverse=True,
    )
    selected = ranked[:top_n]
    total = sum(value for _, value in selected)
    if total <= 0:
        return {}
    return {symbol: value / total for symbol, value in selected}

