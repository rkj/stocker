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

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.initial_capital < 0:
            raise ValueError("initial_capital must be non-negative")
        if self.contribution_amount < 0:
            raise ValueError("contribution_amount must be non-negative")
        if self.fee_bps < 0 or self.fee_fixed < 0 or self.slippage_bps < 0:
            raise ValueError("fee/slippage inputs must be non-negative")

