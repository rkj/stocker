# Stocker

Stocker is a historical stock strategy simulator.

## Quick Start

Run tests:

```bash
pytest
```

Run a simulation with example strategies:

```bash
PYTHONPATH=src python3 -m stocker.cli \
  --data-path /mnt/nfs-lithium-public/rkj/all_stock_data.csv \
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

Generated outputs:
- `daily_equity.csv`
- `trades.csv`
- `annual_summary.csv`
- `terminal_summary.csv`
- `run_manifest.json`

## Example Strategy File

See: `docs/examples/strategies.example.json`

Supported strategy types in this version:
- `equal_weight`
- `sp500_proxy`
- `explicit_symbols`
- `random_n`
- `top_n_ranked`
- `bottom_n_ranked`

## Validation

Benchmark validation artifacts:
- `docs/validation/benchmark-realism.md`
- `docs/validation/sp500_etf_proxy_result.json`
- `docs/validation/sp500_proxy_streaming_result.json`

## Docs

- Product spec: `docs/spec/`
- ADRs: `docs/adr/`
