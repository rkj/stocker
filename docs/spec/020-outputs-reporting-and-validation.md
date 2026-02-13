# Outputs, Reporting, and Validation Requirements

## 1. Reporting Goals
The simulator must produce:
- Per-strategy daily timeseries suitable for charting.
- Cross-strategy summary tables for terminal and annual performance.
- Validation artifacts that show whether market-proxy behavior is realistic.

## 2. Required Output Artifacts

### 2.1 Daily Equity Curve Output
Format: CSV (v1 required)

Required columns:
- `date`
- `strategy_id`
- `cash`
- `positions_market_value`
- `total_equity`
- `daily_return`
- `cumulative_return`
- `contribution_cumulative`
- `trade_count_day`
- `turnover_day`

Behavior:
- One row per strategy per trading date in simulation window.
- No gaps on valid market dates for active strategies.

### 2.2 Trade Ledger Output
Format: CSV (v1 required)

Required columns:
- `date`
- `strategy_id`
- `symbol`
- `side`
- `shares`
- `price`
- `gross_value`
- `slippage_cost`
- `fee_cost`
- `net_cash_impact`

Behavior:
- Every executed rebalance/contribution trade is recorded.

### 2.3 Annual Summary Table
Format: terminal table + CSV export

Required columns:
- `strategy_id`
- `year`
- `start_equity`
- `end_equity`
- `net_contributions_year`
- `return_year`
- `max_drawdown_year`
- `volatility_year`

Behavior:
- One row per strategy per calendar year with at least one trading date in window.

### 2.4 Terminal Comparison Table
Format: terminal table + CSV export

Required columns:
- `strategy_id`
- `final_equity`
- `total_contributions`
- `net_profit`
- `cagr`
- `max_drawdown`
- `annualized_volatility`
- `sharpe_proxy` (risk-free default 0 in v1)
- `total_trades`
- `avg_turnover`

## 3. Validation Requirements

### 3.1 Determinism Validation
- Running same config + seed twice must produce identical output files.
- Validation command should checksum outputs and report exact match.

### 3.2 Internal Consistency Validation
- Daily accounting identity must hold:
- `total_equity = cash + positions_market_value`
- End-of-day equity transition reconciles prior equity, PnL, contributions, and trading costs.

### 3.3 Realism Validation (Market Proxy)
- Broad-market proxy strategy (S&P-style proxy) should produce long-run return levels within a defensible band relative to published U.S. large-cap historical return studies.
- Validation report must include:
- tested date window
- strategy definition used for proxy
- observed CAGR
- cited reference range used for comparison
- caveat note explaining non-official index reconstruction

## 4. CLI UX Requirements
Minimum output sections after run:
1. Run metadata (window, cost model, contribution policy, seed).
2. Terminal comparison table (all strategies).
3. Annual summary preview (head/tail with file path for full export).
4. Output file locations.

## 5. Export Paths (v1 Defaults)
- `outputs/<run_id>/daily_equity.csv`
- `outputs/<run_id>/trades.csv`
- `outputs/<run_id>/annual_summary.csv`
- `outputs/<run_id>/terminal_summary.csv`
- `outputs/<run_id>/run_manifest.json`

`run_manifest.json` must include config and reproducibility metadata.

## 6. Acceptance Criteria
1. A single run with multiple strategies generates all required output files.
2. Daily data can be directly plotted without further normalization.
3. Annual and terminal tables are present and numerically consistent with daily data.
4. Validation report includes a realism section and caveats.
5. Deterministic rerun check passes for non-random and seeded-random strategies.
