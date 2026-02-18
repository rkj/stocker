# CLI Example

Run a multi-strategy simulation and export all outputs:

```bash
PYTHONPATH=src python3 -m stocker.cli \
  --data-path data/market_data.csv \
  --start-date 1993-01-29 \
  --end-date 2024-11-04 \
  --initial-capital 10000 \
  --contribution-amount 500 \
  --contribution-frequency monthly \
  --fee-bps 2.0 \
  --slippage-bps 1.0 \
  --strategy-file docs/examples/strategies.example.json \
  --output-dir outputs/example_run
```

Generated files:
- `outputs/example_run/daily_equity.csv`
- `outputs/example_run/trades.csv`
- `outputs/example_run/annual_summary.csv`
- `outputs/example_run/terminal_summary.csv`
- `outputs/example_run/run_manifest.json`
