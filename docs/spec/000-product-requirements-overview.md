# Stocker Product Requirements Overview

## 1. Purpose
Stocker is a historical trading simulator for comparing transparent, rule-based portfolio strategies over long time periods.

The simulator must answer:
- What would a strategy's portfolio value path have been over a historical window?
- How sensitive are outcomes to rebalance cadence, trading costs, and contribution schedules?
- How do multiple strategies compare under identical market windows and cashflow assumptions?

## 2. Primary Users
- Research user: runs many strategy variants and compares annual and terminal outcomes.
- Product/engineering user: extends strategy catalog and validates behavior using deterministic tests.

## 3. Problem Statement
Many backtests are not reproducible, hide assumptions, or are hard to compare fairly. This project requires:
- A single simulation engine.
- Explicit assumptions (costs, rebalance frequency, contributions, universe selection).
- Deterministic runs with auditable daily outputs.

## 4. In-Scope (v1)
- CLI-driven multi-strategy simulation over historical OHLCV + dividends/splits CSV data.
- Strategy classes with configurable rebalance cadence: daily, monthly, yearly, never.
- Contribution schedules: none, daily, monthly, yearly.
- Transaction cost model integrated into fills.
- Daily portfolio value capture for each strategy.
- Annual summary table and cross-strategy comparison report.

## 5. Out of Scope (v1)
- Live trading or brokerage integration.
- Intraday simulation.
- Tax-lot/tax optimization.
- Margin/leverage/derivatives.
- Corporate-action-perfect index reconstruction beyond available dataset fields.

## 6. Data Inputs
Required runtime arguments:
- `--data-path`: CSV path (default example: `/mnt/nfs-lithium-public/rkj/all_stock_data.csv`).
- `--start-date`: simulation start date.
- `--end-date`: simulation end date.
- `--initial-capital`: starting cash.
- `--strategy-config`: one or more strategy definitions (CLI args or config file).
- `--contribution-amount` and `--contribution-frequency`.
- `--cost-model` (for example: bps + fixed per trade).
- `--seed` for deterministic random strategies.

Dataset fields currently available:
- `Date,Ticker,Open,High,Low,Close,Volume,Dividends,Stock Splits`

## 7. Key Constraints and Assumptions
- Dataset is large (~34.6M rows); engine design must avoid avoidable full-memory operations.
- No direct market-cap/share-outstanding field is present.
- Therefore, any "S&P 500 index" strategy in v1 is implemented as an explicit cap-proxy strategy documented in assumptions.
- All randomness must be seed-controlled.

## 8. Functional Requirements
1. User can run multiple strategies in one simulation command.
2. All strategies run on the same dates and market data slice.
3. Engine applies contributions before strategy allocation on contribution dates.
4. Rebalancing executes only at configured cadence.
5. Trading costs reduce available cash at fill time.
6. Simulator stores daily state per strategy: date, cash, market value, total equity.
7. Simulator emits machine-readable outputs for charting and analysis.

## 9. Non-Functional Requirements
- Deterministic: identical inputs produce identical outputs.
- Testable: core accounting and allocation logic has unit tests.
- Explainable: every strategy has documented decision rules.
- Performant: practical runtime on multi-decade windows from large CSV.

## 10. Acceptance Criteria
- At least five strategy families run in one invocation (including required user-specified variants).
- Daily equity curve output is produced for each strategy.
- Annual summary comparison table is produced.
- Transaction cost and contribution parameters visibly change outcomes.
- Documentation explains assumptions and known caveats.

## 11. Delivery Phases
1. Documentation phase: PRD + ADR set.
2. Core implementation phase: data loader, accounting engine, strategies, runner.
3. Validation phase: compare broad-market proxy results to published long-run return ranges.
4. UX/reporting phase: polished CLI outputs + exported CSVs for charting.
