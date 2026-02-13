from __future__ import annotations

import json
from pathlib import Path

from stocker.cli import main


def test_cli_run_writes_output_bundle(tmp_path: Path) -> None:
    strategies_path = tmp_path / "strategies.json"
    strategies_path.write_text(
        json.dumps(
            {
                "strategies": [
                    {
                        "strategy_id": "eq_daily",
                        "type": "equal_weight",
                        "rebalance_frequency": "daily",
                    },
                    {
                        "strategy_id": "spy_proxy",
                        "type": "explicit_symbols",
                        "rebalance_frequency": "daily",
                        "params": {"symbols": ["SPY"]},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    exit_code = main(
        [
            "--data-path",
            "tests/fixtures/sample_stock_data.csv",
            "--start-date",
            "1980-01-02",
            "--end-date",
            "1980-01-10",
            "--initial-capital",
            "10000",
            "--strategy-file",
            str(strategies_path),
            "--output-dir",
            str(out_dir),
        ]
    )

    assert exit_code == 0
    assert (out_dir / "daily_equity.csv").exists()
    assert (out_dir / "trades.csv").exists()
    assert (out_dir / "annual_summary.csv").exists()
    assert (out_dir / "terminal_summary.csv").exists()
    assert (out_dir / "run_manifest.json").exists()

