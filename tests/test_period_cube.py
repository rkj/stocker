from __future__ import annotations

import csv
from pathlib import Path

from stocker.tools.period_cube import build_period_cube


def _write_daily_equity(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "date",
                "strategy_id",
                "cash",
                "positions_market_value",
                "total_equity",
                "daily_return",
                "cumulative_return",
                "contribution_cumulative",
                "dividend_cumulative",
                "trade_count_day",
                "turnover_day",
            ],
        )
        writer.writeheader()
        # Strategy A:
        # day1 equity 1000
        # day2 contribution 100 and +10% market => equity 1200, daily_return must stay +10% (flow-adjusted)
        # day3 no contribution, +5% market => equity 1260
        writer.writerow(
            {
                "date": "2020-01-02",
                "strategy_id": "A",
                "cash": "0",
                "positions_market_value": "1000",
                "total_equity": "1000",
                "daily_return": "0",
                "cumulative_return": "0",
                "contribution_cumulative": "0",
                "dividend_cumulative": "0",
                "trade_count_day": "0",
                "turnover_day": "0",
            }
        )
        writer.writerow(
            {
                "date": "2020-01-03",
                "strategy_id": "A",
                "cash": "0",
                "positions_market_value": "1200",
                "total_equity": "1200",
                "daily_return": "0.10",
                "cumulative_return": "0.10",
                "contribution_cumulative": "100",
                "dividend_cumulative": "0",
                "trade_count_day": "0",
                "turnover_day": "0",
            }
        )
        writer.writerow(
            {
                "date": "2020-01-06",
                "strategy_id": "A",
                "cash": "0",
                "positions_market_value": "1260",
                "total_equity": "1260",
                "daily_return": "0.05",
                "cumulative_return": "0.155",
                "contribution_cumulative": "100",
                "dividend_cumulative": "0",
                "trade_count_day": "0",
                "turnover_day": "0",
            }
        )

        # Strategy B (flat)
        writer.writerow(
            {
                "date": "2020-01-02",
                "strategy_id": "B",
                "cash": "0",
                "positions_market_value": "500",
                "total_equity": "500",
                "daily_return": "0",
                "cumulative_return": "0",
                "contribution_cumulative": "0",
                "dividend_cumulative": "0",
                "trade_count_day": "0",
                "turnover_day": "0",
            }
        )
        writer.writerow(
            {
                "date": "2020-01-03",
                "strategy_id": "B",
                "cash": "0",
                "positions_market_value": "500",
                "total_equity": "500",
                "daily_return": "0",
                "cumulative_return": "0",
                "contribution_cumulative": "0",
                "dividend_cumulative": "0",
                "trade_count_day": "0",
                "turnover_day": "0",
            }
        )
        writer.writerow(
            {
                "date": "2020-01-06",
                "strategy_id": "B",
                "cash": "0",
                "positions_market_value": "500",
                "total_equity": "500",
                "daily_return": "0",
                "cumulative_return": "0",
                "contribution_cumulative": "0",
                "dividend_cumulative": "0",
                "trade_count_day": "0",
                "turnover_day": "0",
            }
        )


def test_build_period_cube_daily_grid(tmp_path: Path) -> None:
    daily_path = tmp_path / "daily.csv"
    cube_path = tmp_path / "cube.csv"
    _write_daily_equity(daily_path)

    rows = build_period_cube(
        daily_equity_path=daily_path,
        output_path=cube_path,
        date_grid="daily",
    )

    assert rows == 6  # 3 choose 2 periods * 2 strategies
    payload = list(csv.DictReader(cube_path.open(newline="", encoding="utf-8")))
    # A: 2020-01-02 -> 2020-01-06 should be (1.10 * 1.05 - 1) = 0.155
    target = next(
        row
        for row in payload
        if row["strategy_id"] == "A"
        and row["start_date"] == "2020-01-02"
        and row["end_date"] == "2020-01-06"
    )
    assert round(float(target["period_return"]), 10) == 0.155
    assert round(float(target["period_contributions"]), 10) == 100.0


def test_build_period_cube_monthly_grid_selects_first_trading_day(tmp_path: Path) -> None:
    daily_path = tmp_path / "daily.csv"
    cube_path = tmp_path / "cube.csv"
    _write_daily_equity(daily_path)

    # With only January dates in fixture, monthly grid picks one anchor per strategy => 0 rows.
    rows = build_period_cube(
        daily_equity_path=daily_path,
        output_path=cube_path,
        date_grid="monthly",
    )
    assert rows == 0
