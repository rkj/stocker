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
  --output-dir outputs/example_run \
  --progress
```

Generated outputs:
- `daily_equity.csv`
- `trades.csv`
- `annual_summary.csv`
- `terminal_summary.csv`
- `run_manifest.json`

Notes:
- default engine is low-memory streaming (`--engine streaming`)
- use `--progress` to print year checkpoints during long runs
- default execution liquidity guard is `--max-trade-participation 0.01` (max 1% of that day volume per symbol trade; zero-volume symbols are not traded)
- dataset `Close` can be dividend-adjusted; `--credit-dividends` is opt-in to avoid double counting
- `--price-series-mode raw_reconstructed` (in-memory engine only) reconstructs price-only close series from adjusted close + dividends

Price-only S&P proxy benchmark (no extra cash, no fees/slippage):

```bash
PYTHONPATH=src python3 -m stocker.cli \
  --data-path /mnt/nfs-lithium-public/rkj/all_stock_data.csv \
  --start-date 1993-01-29 \
  --end-date 2024-01-02 \
  --initial-capital 10000 \
  --contribution-amount 0 \
  --contribution-frequency none \
  --fee-bps 0 \
  --slippage-bps 0 \
  --strategy-file /tmp/sp500_only_nocontrib.json \
  --output-dir /tmp/sp500_nocontrib_price_only \
  --engine in_memory \
  --price-series-mode raw_reconstructed
```

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
- `docs/validation/sp500_price_proxy_reconstructed_result.json`

## Docs

- Product spec: `docs/spec/`
- ADRs: `docs/adr/`
