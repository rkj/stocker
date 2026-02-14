"""Configuration models for simulation runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class ContributionFrequency(str, Enum):
    """Supported contribution schedules."""

    NONE = "none"
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class PriceSeriesMode(str, Enum):
    """How to interpret input close prices."""

    AS_IS = "as_is"
    RAW_RECONSTRUCTED = "raw_reconstructed"


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Global run settings shared across all strategies."""

    data_path: str
    start_date: date
    end_date: date
    initial_capital: float
    contribution_amount: float = 0.0
    contribution_frequency: ContributionFrequency = ContributionFrequency.NONE
    fee_bps: float = 0.0
    fee_fixed: float = 0.0
    slippage_bps: float = 0.0
    seed: int = 42
    output_dir: str = "outputs"
    strategy_file: str | None = None
    progress: bool = False
    engine: str = "streaming"
    min_price: float = 0.01
    max_price: float = 100_000.0
    min_volume: float = 0.0
    max_trade_participation: float = 0.01
    credit_dividends: bool = False
    price_series_mode: PriceSeriesMode = PriceSeriesMode.AS_IS

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.initial_capital < 0:
            raise ValueError("initial_capital must be non-negative")
        if self.contribution_amount < 0:
            raise ValueError("contribution_amount must be non-negative")
        if self.fee_bps < 0 or self.fee_fixed < 0 or self.slippage_bps < 0:
            raise ValueError("fee/slippage inputs must be non-negative")
        if self.min_price <= 0:
            raise ValueError("min_price must be positive")
        if self.max_price <= self.min_price:
            raise ValueError("max_price must be greater than min_price")
        if self.min_volume < 0:
            raise ValueError("min_volume must be non-negative")
        if self.max_trade_participation <= 0 or self.max_trade_participation > 1:
            raise ValueError("max_trade_participation must be in (0, 1]")
