"""Build a period-return cube from simulation daily equity output."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class DailyPoint:
    trading_day: date
    strategy_id: str
    daily_return: float
    equity: float
    contribution_cumulative: float


def build_period_cube(
    *,
    daily_equity_path: Path,
    output_path: Path,
    date_grid: str = "monthly",
) -> int:
    by_strategy = _load_daily_points(daily_equity_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "strategy_id",
                "start_date",
                "end_date",
                "calendar_days",
                "trading_days",
                "start_equity",
                "end_equity",
                "period_contributions",
                "period_return",
                "period_annualized_return",
            ],
        )
        writer.writeheader()
        for strategy_id in sorted(by_strategy):
            points = by_strategy[strategy_id]
            grid_indices = _grid_indices(points=points, grid=date_grid)
            growth_index = _growth_index(points)
            for start_pos, start_idx in enumerate(grid_indices):
                for end_idx in grid_indices[start_pos + 1 :]:
                    start_point = points[start_idx]
                    end_point = points[end_idx]
                    period_return = _period_return(
                        growth_index=growth_index,
                        start_idx=start_idx,
                        end_idx=end_idx,
                    )
                    calendar_days = (end_point.trading_day - start_point.trading_day).days
                    writer.writerow(
                        {
                            "strategy_id": strategy_id,
                            "start_date": start_point.trading_day.isoformat(),
                            "end_date": end_point.trading_day.isoformat(),
                            "calendar_days": calendar_days,
                            "trading_days": end_idx - start_idx,
                            "start_equity": f"{start_point.equity:.10f}",
                            "end_equity": f"{end_point.equity:.10f}",
                            "period_contributions": (
                                f"{(end_point.contribution_cumulative - start_point.contribution_cumulative):.10f}"
                            ),
                            "period_return": f"{period_return:.10f}",
                            "period_annualized_return": (
                                f"{_annualized_return(period_return=period_return, calendar_days=calendar_days):.10f}"
                            ),
                        }
                    )
                    row_count += 1
    return row_count


def _load_daily_points(path: Path) -> dict[str, list[DailyPoint]]:
    by_strategy: dict[str, list[DailyPoint]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            strategy_id = str(row["strategy_id"])
            point = DailyPoint(
                trading_day=date.fromisoformat(row["date"]),
                strategy_id=strategy_id,
                daily_return=float(row["daily_return"]),
                equity=float(row["total_equity"]),
                contribution_cumulative=float(row["contribution_cumulative"]),
            )
            by_strategy.setdefault(strategy_id, []).append(point)
    for strategy_id, points in by_strategy.items():
        points.sort(key=lambda point: point.trading_day)
        by_strategy[strategy_id] = points
    return by_strategy


def _growth_index(points: list[DailyPoint]) -> list[float]:
    if not points:
        return []
    growth = [1.0]
    for idx in range(1, len(points)):
        step = 1.0 + points[idx].daily_return
        if step <= 0:
            growth.append(0.0)
        else:
            growth.append(growth[-1] * step)
    return growth


def _period_return(*, growth_index: list[float], start_idx: int, end_idx: int) -> float:
    start_growth = growth_index[start_idx]
    end_growth = growth_index[end_idx]
    if start_growth <= 0:
        return 0.0
    return (end_growth / start_growth) - 1.0


def _annualized_return(*, period_return: float, calendar_days: int) -> float:
    if calendar_days <= 0:
        return 0.0
    if period_return <= -1.0:
        return -1.0
    years = calendar_days / 365.25
    if years <= 0:
        return 0.0
    return (1.0 + period_return) ** (1.0 / years) - 1.0


def _grid_indices(*, points: list[DailyPoint], grid: str) -> list[int]:
    if grid == "daily":
        return list(range(len(points)))
    if grid == "monthly":
        return _first_index_per_bucket(
            points=points,
            bucket_keys=((point.trading_day.year, point.trading_day.month) for point in points),
        )
    if grid == "yearly":
        return _first_index_per_bucket(
            points=points,
            bucket_keys=((point.trading_day.year,) for point in points),
        )
    raise ValueError(f"unsupported date grid: {grid}")


def _first_index_per_bucket(
    *,
    points: list[DailyPoint],
    bucket_keys: Iterable[tuple[int, ...]],
) -> list[int]:
    selected: list[int] = []
    last_key: tuple[int, ...] | None = None
    for idx, key in enumerate(bucket_keys):
        if key != last_key:
            selected.append(idx)
            last_key = key
    return selected


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stocker-period-cube",
        description="Build a (strategy, start_date, end_date) return cube from daily_equity.csv",
    )
    parser.add_argument("--daily-equity-path", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--date-grid", choices=["daily", "monthly", "yearly"], default="monthly")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    rows = build_period_cube(
        daily_equity_path=Path(args.daily_equity_path),
        output_path=Path(args.output_path),
        date_grid=str(args.date_grid),
    )
    print(
        f"wrote period cube rows={rows} grid={args.date_grid} output={args.output_path}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
