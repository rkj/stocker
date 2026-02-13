"""Portfolio accounting primitives used by the simulation engine."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RebalanceCosts:
    fee_bps: float = 0.0
    fee_fixed: float = 0.0
    slippage_bps: float = 0.0


@dataclass(frozen=True, slots=True)
class TradeFill:
    symbol: str
    side: str
    shares: float
    price: float
    gross_value: float
    slippage_cost: float
    fee_cost: float
    total_cost: float
    net_cash_impact: float


@dataclass(slots=True)
class Portfolio:
    initial_cash: float
    cash: float = field(init=False)
    holdings: dict[str, float] = field(default_factory=dict)
    cumulative_contributions: float = 0.0
    cumulative_costs: float = 0.0
    cumulative_dividends: float = 0.0

    def __post_init__(self) -> None:
        if self.initial_cash < 0:
            raise ValueError("initial_cash must be non-negative")
        self.cash = self.initial_cash

    def contribute(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("contribution amount must be non-negative")
        self.cash += amount
        self.cumulative_contributions += amount

    def total_market_value(self, prices: dict[str, float]) -> float:
        total = 0.0
        for symbol, shares in self.holdings.items():
            price = prices.get(symbol)
            if price is None:
                continue
            total += shares * price
        return total

    def total_equity(self, prices: dict[str, float]) -> float:
        return self.cash + self.total_market_value(prices)

    def apply_dividends(self, dividends_per_share: dict[str, float]) -> float:
        """Credit dividend cash for currently held shares."""
        total = 0.0
        for symbol, shares in self.holdings.items():
            div = dividends_per_share.get(symbol, 0.0)
            if shares > 0 and div > 0:
                total += shares * div
        if total > 0:
            self.cash += total
            self.cumulative_dividends += total
        return total

    def rebalance_to_weights(
        self,
        *,
        target_weights: dict[str, float],
        prices: dict[str, float],
        costs: RebalanceCosts,
    ) -> list[TradeFill]:
        normalized = _normalize_weights(target_weights)
        equity = self.total_equity(prices)

        symbols = set(self.holdings) | set(normalized)
        fills: list[TradeFill] = []
        for symbol in sorted(symbols):
            price = prices.get(symbol)
            if price is None or price <= 0:
                continue

            current_shares = self.holdings.get(symbol, 0.0)
            current_value = current_shares * price
            target_value = normalized.get(symbol, 0.0) * equity
            delta_value = target_value - current_value
            shares_delta = delta_value / price
            if abs(shares_delta) < 1e-12:
                continue

            fill = _build_fill(
                symbol=symbol,
                price=price,
                shares_delta=shares_delta,
                costs=costs,
            )
            self.cash += fill.net_cash_impact
            self.cumulative_costs += fill.total_cost

            new_shares = current_shares + shares_delta
            if abs(new_shares) < 1e-12:
                self.holdings.pop(symbol, None)
            else:
                self.holdings[symbol] = new_shares
            fills.append(fill)

        return fills


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    positive = {k: v for k, v in weights.items() if v > 0}
    total = sum(positive.values())
    if total <= 0:
        return {}
    return {k: v / total for k, v in positive.items()}


def _build_fill(
    *,
    symbol: str,
    price: float,
    shares_delta: float,
    costs: RebalanceCosts,
) -> TradeFill:
    gross = abs(shares_delta) * price
    slippage_cost = gross * (costs.slippage_bps / 10_000.0)
    fee_cost = gross * (costs.fee_bps / 10_000.0) + costs.fee_fixed
    total_cost = slippage_cost + fee_cost

    is_buy = shares_delta > 0
    side = "buy" if is_buy else "sell"
    if is_buy:
        net_cash_impact = -(gross + total_cost)
    else:
        net_cash_impact = gross - total_cost

    return TradeFill(
        symbol=symbol,
        side=side,
        shares=abs(shares_delta),
        price=price,
        gross_value=gross,
        slippage_cost=slippage_cost,
        fee_cost=fee_cost,
        total_cost=total_cost,
        net_cash_impact=net_cash_impact,
    )
