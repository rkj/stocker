from datetime import date

import pytest

from stocker.config import ContributionFrequency, SimulationConfig


def test_simulation_config_rejects_inverted_date_range() -> None:
    with pytest.raises(ValueError):
        SimulationConfig(
            data_path="/tmp/data.csv",
            start_date=date(2021, 1, 2),
            end_date=date(2021, 1, 1),
            initial_capital=10_000.0,
        )


def test_simulation_config_applies_defaults() -> None:
    cfg = SimulationConfig(
        data_path="/tmp/data.csv",
        start_date=date(2021, 1, 1),
        end_date=date(2021, 12, 31),
        initial_capital=10_000.0,
    )

    assert cfg.contribution_amount == 0.0
    assert cfg.contribution_frequency is ContributionFrequency.NONE
    assert cfg.fee_bps == 0.0
    assert cfg.slippage_bps == 0.0
    assert cfg.max_trade_participation == 0.01


def test_simulation_config_rejects_invalid_trade_participation() -> None:
    with pytest.raises(ValueError):
        SimulationConfig(
            data_path="/tmp/data.csv",
            start_date=date(2021, 1, 1),
            end_date=date(2021, 12, 31),
            initial_capital=10_000.0,
            max_trade_participation=0.0,
        )
