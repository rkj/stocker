"""Core simulation loop for running multiple strategies over shared market data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Protocol

from stocker.data.market_data import MarketData
from stocker.engine.portfolio import Portfolio, RebalanceCosts, TradeFill
from stocker.simulation.config_parser import StrategySpec
from stocker.strategies.baseline import (
    EqualWeightStrategy,
    RebalanceFrequency,
    Sp500ProxyStrategy,
    should_rebalance,
)
from stocker.strategies.selection import (
    BottomNRankedStrategy,
    ExplicitSymbolsEqualStrategy,
    RandomNEqualStrategy,
    TopNRankedStrategy,
)


class ContributionFrequency(str, Enum):
    NONE = "none"
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class StrategyInstance(Protocol):
    def target_weights(self, *, market: MarketData, trading_day: date) -> dict[str, float]:
        """Return target weights for a trading day."""


@dataclass(frozen=True, slots=True)
class RunSettings:
    initial_capital: float
    contribution_amount: float
    contribution_frequency: ContributionFrequency
    fee_bps: float
    fee_fixed: float
    slippage_bps: float
    seed: int = 42


@dataclass(frozen=True, slots=True)
class DailyRecord:
    date: date
    strategy_id: str
    cash: float
    positions_market_value: float
    total_equity: float
    daily_return: float
    cumulative_contributions: float
    trade_count_day: int
    turnover_day: float


@dataclass(frozen=True, slots=True)
class DatedTrade:
    date: date
    strategy_id: str
    fill: TradeFill


@dataclass(frozen=True, slots=True)
class SimulationResult:
    daily_records_by_strategy: dict[str, list[DailyRecord]]
    trades: list[DatedTrade]


@dataclass(slots=True)
class _StrategyState:
    strategy_id: str
    strategy: StrategyInstance
    rebalance_frequency: RebalanceFrequency
    portfolio: Portfolio
    last_rebalance_date: date | None = None
    last_contribution_date: date | None = None
    previous_equity: float | None = None


def run_simulation(
    *,
    market: MarketData,
    strategy_specs: list[StrategySpec | dict[str, Any]],
    settings: RunSettings,
) -> SimulationResult:
    states = [
        _build_state(spec=spec, settings=settings) for spec in strategy_specs
    ]
    daily_by_strategy: dict[str, list[DailyRecord]] = {state.strategy_id: [] for state in states}
    dated_trades: list[DatedTrade] = []

    costs = RebalanceCosts(
        fee_bps=settings.fee_bps,
        fee_fixed=settings.fee_fixed,
        slippage_bps=settings.slippage_bps,
    )

    for trading_day in market.trading_dates:
        prices = {
            symbol: bar.close for symbol, bar in market.bars_on(trading_day).items()
        }
        for state in states:
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
                target_weights = state.strategy.target_weights(
                    market=market,
                    trading_day=trading_day,
                )
                fills = state.portfolio.rebalance_to_weights(
                    target_weights=target_weights,
                    prices=prices,
                    costs=costs,
                )
                state.last_rebalance_date = trading_day
                dated_trades.extend(
                    DatedTrade(date=trading_day, strategy_id=state.strategy_id, fill=fill)
                    for fill in fills
                )

            market_value = state.portfolio.total_market_value(prices)
            equity = state.portfolio.cash + market_value
            previous_equity = state.previous_equity
            if previous_equity is None or previous_equity == 0:
                daily_return = 0.0
            else:
                daily_return = (equity / previous_equity) - 1.0
            turnover = 0.0 if previous_equity in (None, 0) else sum(
                fill.gross_value for fill in fills
            ) / previous_equity
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
                    trade_count_day=len(fills),
                    turnover_day=turnover,
                )
            )

    return SimulationResult(daily_records_by_strategy=daily_by_strategy, trades=dated_trades)


def _to_spec(raw: StrategySpec | dict[str, Any]) -> StrategySpec:
    if isinstance(raw, StrategySpec):
        return raw
    if not isinstance(raw, dict):
        raise ValueError("strategy spec must be StrategySpec or dict")
    strategy_id = str(raw["strategy_id"])
    strategy_type = str(raw["type"])
    rebalance_frequency = str(raw.get("rebalance_frequency", "daily"))
    params = dict(raw.get("params", {}))
    return StrategySpec(
        strategy_id=strategy_id,
        strategy_type=strategy_type,
        rebalance_frequency=rebalance_frequency,
        params=params,
    )


def _build_state(*, spec: StrategySpec | dict[str, Any], settings: RunSettings) -> _StrategyState:
    resolved = _to_spec(spec)
    frequency = RebalanceFrequency(resolved.rebalance_frequency)
    strategy = _build_strategy(resolved, settings=settings)
    return _StrategyState(
        strategy_id=resolved.strategy_id,
        strategy=strategy,
        rebalance_frequency=frequency,
        portfolio=Portfolio(initial_cash=settings.initial_capital),
    )


def _build_strategy(spec: StrategySpec, *, settings: RunSettings) -> StrategyInstance:
    params = spec.params
    strategy_type = spec.strategy_type
    if strategy_type == "equal_weight":
        return EqualWeightStrategy()
    if strategy_type == "sp500_proxy":
        return Sp500ProxyStrategy(
            top_n=int(params.get("top_n", 500)),
            rolling_window=int(params.get("rolling_window", 252)),
        )
    if strategy_type == "explicit_symbols":
        return ExplicitSymbolsEqualStrategy(symbols=list(params.get("symbols", [])))
    if strategy_type == "random_n":
        seed = int(params.get("seed", settings.seed))
        return RandomNEqualStrategy(n=int(params["n"]), seed=seed)
    if strategy_type == "top_n_ranked":
        return TopNRankedStrategy(
            n=int(params["n"]),
            metric=str(params.get("metric", "close_price")),  # type: ignore[arg-type]
            proportional=bool(params.get("proportional", False)),
        )
    if strategy_type == "bottom_n_ranked":
        return BottomNRankedStrategy(
            n=int(params["n"]),
            metric=str(params.get("metric", "close_price")),  # type: ignore[arg-type]
        )
    raise ValueError(f"unknown strategy type: {strategy_type}")


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

