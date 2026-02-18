# Stocker

Stocker is a historical stock strategy simulator.

## Data Setup

This repository does not include historical market data.

Provide your own CSV at runtime via `--data-path`:
- export from your data vendor or broker
- or prepare a normalized CSV with the required schema below

For local slicing of your own large dataset:

```bash
PYTHONPATH=src python3 -m stocker.tools.fixture_extractor \
  --input-path data/market_data_full.csv \
  --output-path data/market_data.csv \
  --symbols SPY,AAPL,MSFT \
  --start-date 2010-01-01 \
  --end-date 2024-12-31
```

## Quick Start

Run tests:

```bash
pytest
```

Run a simulation with example strategies:

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
  --data-path data/market_data.csv \
  --start-date 1993-01-29 \
  --end-date 2024-01-02 \
  --initial-capital 10000 \
  --contribution-amount 0 \
  --contribution-frequency none \
  --fee-bps 0 \
  --slippage-bps 0 \
  --strategy-file docs/examples/strategies.example.json \
  --output-dir outputs/sp500_nocontrib_price_only \
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

## Period Cube

Build a `(strategy_id, start_date, end_date)` period-return cube from a run:

```bash
PYTHONPATH=src python3 -m stocker.tools.period_cube \
  --daily-equity-path outputs/example_run/daily_equity.csv \
  --output-path outputs/example_run/period_cube_monthly.csv \
  --date-grid monthly
```

`--date-grid` controls cube density:
- `daily` (largest)
- `monthly` (default)
- `yearly`

## CSV Format

Input CSV must include these headers:
- `Date`
- `Ticker`
- `Open`
- `High`
- `Low`
- `Close`
- `Volume`
- `Dividends`
- `Stock Splits`

## Docs

- Product spec: `docs/spec/`
- ADRs: `docs/adr/`
