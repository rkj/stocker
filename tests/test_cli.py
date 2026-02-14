from datetime import date

from stocker.cli import parse_args
from stocker.config import ContributionFrequency, PriceSeriesMode


def test_parse_args_uses_expected_defaults() -> None:
    cfg = parse_args(
        [
            "--data-path",
            "/tmp/data.csv",
            "--start-date",
            "2020-01-01",
            "--end-date",
            "2020-12-31",
            "--initial-capital",
            "10000",
        ]
    )

    assert cfg.data_path == "/tmp/data.csv"
    assert cfg.start_date == date(2020, 1, 1)
    assert cfg.end_date == date(2020, 12, 31)
    assert cfg.initial_capital == 10_000.0
    assert cfg.contribution_frequency is ContributionFrequency.NONE
    assert cfg.engine == "streaming"
    assert cfg.min_price == 0.01
    assert cfg.max_price == 100_000.0
    assert cfg.min_volume == 0.0
    assert cfg.credit_dividends is False
    assert cfg.price_series_mode is PriceSeriesMode.AS_IS


def test_parse_args_accepts_contribution_and_cost_options() -> None:
    cfg = parse_args(
        [
            "--data-path",
            "/tmp/data.csv",
            "--start-date",
            "2020-01-01",
            "--end-date",
            "2020-12-31",
            "--initial-capital",
            "25000",
            "--contribution-amount",
            "500",
            "--contribution-frequency",
            "monthly",
            "--fee-bps",
            "2.5",
            "--fee-fixed",
            "1.0",
            "--slippage-bps",
            "1.5",
            "--seed",
            "7",
        ]
    )

    assert cfg.initial_capital == 25_000.0
    assert cfg.contribution_amount == 500.0
    assert cfg.contribution_frequency is ContributionFrequency.MONTHLY
    assert cfg.fee_bps == 2.5
    assert cfg.fee_fixed == 1.0
    assert cfg.slippage_bps == 1.5
    assert cfg.seed == 7


def test_parse_args_accepts_price_series_controls() -> None:
    cfg = parse_args(
        [
            "--data-path",
            "/tmp/data.csv",
            "--start-date",
            "2020-01-01",
            "--end-date",
            "2020-12-31",
            "--initial-capital",
            "10000",
            "--credit-dividends",
            "--price-series-mode",
            "raw_reconstructed",
        ]
    )
    assert cfg.credit_dividends is True
    assert cfg.price_series_mode is PriceSeriesMode.RAW_RECONSTRUCTED
