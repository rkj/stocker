"""Parse strategy configuration files for simulation runs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class StrategySpec:
    strategy_id: str
    strategy_type: str
    rebalance_frequency: str = "daily"
    params: dict[str, Any] = field(default_factory=dict)


def parse_strategy_file(path: Path) -> list[StrategySpec]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_strategies = payload.get("strategies")
    if not isinstance(raw_strategies, list) or not raw_strategies:
        raise ValueError("strategy file must contain a non-empty 'strategies' list")

    parsed: list[StrategySpec] = []
    for item in raw_strategies:
        if not isinstance(item, dict):
            raise ValueError("each strategy entry must be an object")
        strategy_id = item.get("strategy_id")
        strategy_type = item.get("type")
        if not strategy_id or not strategy_type:
            raise ValueError("strategy entries require 'strategy_id' and 'type'")
        rebalance_frequency = item.get("rebalance_frequency", "daily")
        params = item.get("params", {})
        if not isinstance(params, dict):
            raise ValueError("'params' must be an object")
        parsed.append(
            StrategySpec(
                strategy_id=str(strategy_id),
                strategy_type=str(strategy_type),
                rebalance_frequency=str(rebalance_frequency),
                params=dict(params),
            )
        )
    return parsed

