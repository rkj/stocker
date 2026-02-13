# ADR 003: Data Ingestion and Normalization Model

- Status: Accepted
- Date: 2026-02-12
- Decision Makers: Stocker project maintainers

## Context
Input data is a large CSV (~34.6M rows) with columns:
- `Date,Ticker,Open,High,Low,Close,Volume,Dividends,Stock Splits`

Requirements:
- Efficiently process long windows.
- Ensure deterministic, explainable normalization.
- Support strategy ranking metrics that rely on rolling volume/value statistics.

## Decision
Use a two-stage data model:
1. Ingestion stage: schema-validated read into a normalized internal table.
2. Simulation access stage: date-partitioned market snapshots and derived features.

Key choices:
- Parse dates as `date` type and sort by (`date`, `ticker`).
- Use `Close` as default execution/valuation price in v1.
- Treat rows with missing/non-positive close as non-tradable for that date.
- Compute derived features (for example rolling dollar volume) during preprocessing pass.

## Corporate Actions Handling
- Dividends:
- v1 assumes price series already reflects vendor adjustments where applicable.
- Optional cash dividend accrual can be added in a future enhancement; not required for v1 parity checks.

- Stock splits:
- v1 assumes split-adjusted pricing where provided by source.
- `Stock Splits` column is retained for diagnostics but not used to retro-adjust historical holdings in v1.

These assumptions must be disclosed in output manifest and realism caveats.

## Universe and Tradability Rules
On each date, a symbol is tradable if:
- A row exists for that date and symbol.
- `Close > 0`
- Optional liquidity filter passes (if configured).

Symbols absent on a date are skipped for order generation and valuation falls back to latest known tradable close only if stale-pricing mode is enabled (v1 default: disabled).

## Performance Approach
- Prefer Polars lazy scanning where possible.
- Materialize only required window (`start_date` to `end_date`) and required columns.
- Precompute date index and per-date symbol slices.
- Avoid per-strategy full table scans by sharing market snapshots across all strategies.

## Rationale
- Separates cleanly validated source handling from strategy logic.
- Keeps performance tractable on very large CSV input.
- Makes assumptions explicit and testable.

## Consequences
Positive:
- Deterministic and auditable data path.
- Reduced repeated I/O work for multi-strategy runs.

Negative:
- Additional preprocessing complexity for derived features.
- Accuracy depends on source-provider adjustment conventions.

## Alternatives Considered
Raw row-by-row simulation without preprocessing:
- Rejected due to repeated metric recomputation and slower multi-strategy execution.

Aggressive full-memory materialization of all dates/symbols:
- Rejected due to avoidable memory pressure and slower startup for short-window runs.

## Follow-up
- Add fixture extractor to generate representative test subsets.
- Add ingestion validation report (row counts, date range, tradable symbol counts).
