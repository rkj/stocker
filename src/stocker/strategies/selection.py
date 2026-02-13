"""N-stock and symbol-selection strategy implementations."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from stocker.data.market_data import MarketData
from stocker.strategies.baseline import equal_weights, proportional_top_n_weights


RankMetric = Literal["close_price", "dollar_volume_1d", "rolling_dollar_volume_252d"]


@dataclass(slots=True)
class ExplicitSymbolsEqualStrategy:
    symbols: list[str]

    def target_weights(self, *, market: MarketData, trading_day: date) -> dict[str, float]:
        tradable = set(market.bars_on(trading_day))
        selected = sorted({symbol.upper() for symbol in self.symbols} & tradable)
        return equal_weights(selected)


@dataclass(slots=True)
class RandomNEqualStrategy:
    n: int
    seed: int = 42

    def target_weights(self, *, market: MarketData, trading_day: date) -> dict[str, float]:
        if self.n <= 0:
            raise ValueError("n must be positive")
        candidates = sorted(market.bars_on(trading_day))
        if not candidates:
            return {}
        sample_size = min(self.n, len(candidates))
        rng = random.Random(self.seed + trading_day.toordinal())
        selected = sorted(rng.sample(candidates, sample_size))
        return equal_weights(selected)


@dataclass(slots=True)
class TopNRankedStrategy:
    n: int
    metric: RankMetric
    proportional: bool = False
    _rolling_cache: dict[date, dict[str, float]] | None = field(default=None, init=False)

    def target_weights(self, *, market: MarketData, trading_day: date) -> dict[str, float]:
        metrics = _metric_values(
            market=market,
            trading_day=trading_day,
            metric=self.metric,
            rolling_cache=self._rolling_cache,
        )
        if self.metric == "rolling_dollar_volume_252d" and self._rolling_cache is None:
            self._rolling_cache = market.rolling_dollar_volume(window=252)
            metrics = self._rolling_cache.get(trading_day, {})

        if self.proportional:
            return proportional_top_n_weights(metrics=metrics, top_n=self.n)
        ranked = sorted(metrics, key=metrics.get, reverse=True)[: self.n]
        return equal_weights(ranked)


@dataclass(slots=True)
class BottomNRankedStrategy:
    n: int
    metric: RankMetric
    _rolling_cache: dict[date, dict[str, float]] | None = field(default=None, init=False)

    def target_weights(self, *, market: MarketData, trading_day: date) -> dict[str, float]:
        metrics = _metric_values(
            market=market,
            trading_day=trading_day,
            metric=self.metric,
            rolling_cache=self._rolling_cache,
        )
        if self.metric == "rolling_dollar_volume_252d" and self._rolling_cache is None:
            self._rolling_cache = market.rolling_dollar_volume(window=252)
            metrics = self._rolling_cache.get(trading_day, {})

        ranked = sorted(metrics, key=metrics.get)[: self.n]
        return equal_weights(ranked)


def _metric_values(
    *,
    market: MarketData,
    trading_day: date,
    metric: RankMetric,
    rolling_cache: dict[date, dict[str, float]] | None,
) -> dict[str, float]:
    bars = market.bars_on(trading_day)
    if metric == "close_price":
        return {symbol: bar.close for symbol, bar in bars.items() if bar.close > 0}
    if metric == "dollar_volume_1d":
        return {
            symbol: bar.close * bar.volume
            for symbol, bar in bars.items()
            if bar.close > 0 and bar.volume > 0
        }
    if metric == "rolling_dollar_volume_252d":
        if rolling_cache is None:
            return market.rolling_dollar_volume(window=252).get(trading_day, {})
        return rolling_cache.get(trading_day, {})
    raise ValueError(f"unsupported metric: {metric}")

