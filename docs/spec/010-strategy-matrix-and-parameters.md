# Strategy Matrix and Simulation Parameters

## 1. Strategy Framework
Each strategy is represented as:
- `universe_selector`: decides eligible symbols for the current rebalance date.
- `weight_model`: computes target weights across selected symbols.
- `rebalance_frequency`: `daily|monthly|yearly|never`.
- `contribution_policy`: how new capital is injected and invested.

Strategies are run under a shared engine and differ only by the components above.

## 2. Required Baseline Strategies

### 2.1 S&P 500 Daily Rebalance (Required)
Name: `sp500_proxy_daily`

Given missing direct market-cap fields, v1 defines a documented proxy:
- Universe: top 500 symbols by rolling 252-trading-day dollar-volume (`close * volume`) on each rebalance date.
- Weights: dollar-volume weights normalized to 100%.
- Rebalance: daily.

Configuration:
- `universe.top_n=500`
- `universe.rank_metric=rolling_dollar_volume_252d`
- `weights=model_rank_metric_proportional`
- `rebalance_frequency=daily`

Notes:
- This is a broad-market-cap-proxy strategy, not an official index reconstruction.

### 2.2 Equal-Weight All-Selected Symbols (Required)
Name: `equal_weight`

- Universe: configurable (all symbols with valid close on date, or filtered subset).
- Weights: equal across selected symbols.
- Rebalance: configurable (`daily|monthly|yearly|never`).

Configuration:
- `weights=equal`
- `rebalance_frequency=<cadence>`

### 2.3 Rebalance Cadence Variants (Required)
Each baseline strategy supports:
- `daily`
- `yearly`
- `never` (buy-and-hold after initial allocation)

Optional in v1:
- `monthly`

### 2.4 Contribution Variants (Required)
Each strategy can run with one contribution schedule:
- `none`
- `daily`
- `monthly`
- `yearly`

Contribution rules:
- Contribution amount is deposited to cash at market open event of the contribution date.
- If rebalance is due that date, contribution is included in rebalance target.
- If rebalance is not due, contribution stays in cash until next rebalance unless `auto_invest_new_cash=true`.

## 3. N-Stock Selection Strategies (Required)

### 3.1 Explicit Symbols
Name: `explicit_symbols_equal`
- Universe: provided symbol list.
- Weights: equal.
- Rebalance: configurable cadence.

### 3.2 Random N
Name: `random_n_equal`
- Universe: symbols tradable on rebalance date.
- Selector: deterministic seeded random sample of size `N`.
- Weights: equal.
- Rebalance: configurable cadence.

### 3.3 Top N by Rank Metric
Name: `top_n_ranked`
- Universe: symbols tradable on rebalance date.
- Selector: top `N` by configured metric.
- Weights: equal or metric-proportional.

### 3.4 Bottom N by Rank Metric
Name: `bottom_n_ranked`
- Universe: symbols tradable on rebalance date.
- Selector: bottom `N` by configured metric.
- Weights: equal.

Supported rank metrics in v1:
- `close_price`
- `dollar_volume_1d` (`close * volume`)
- `rolling_dollar_volume_252d`

## 4. Additional Popular Strategies (v1+ Recommended)
- `buy_and_hold_market_proxy`: one-time allocation, never rebalance.
- `min_variance_proxy` (future): requires covariance estimates and stabilization constraints.
- `momentum_top_n` (future): rank by trailing return window.
- `dividend_focus` (future): requires richer fundamental/dividend feature handling.

## 5. Strategy Configuration Schema (Conceptual)
```yaml
strategy_id: sp500_proxy_daily
universe:
  mode: rank_top_n
  n: 500
  rank_metric: rolling_dollar_volume_252d
weights:
  model: proportional_to_metric
  metric: rolling_dollar_volume_252d
rebalance:
  frequency: daily
contributions:
  amount: 0
  frequency: none
execution:
  slippage_bps: 1.0
  fee_bps: 2.0
  fee_fixed: 0.00
random_seed: 42
```

## 6. Parameter Definitions
Global simulation parameters:
- `start_date`, `end_date`
- `initial_capital`
- `contribution_amount`, `contribution_frequency`
- `fee_bps`, `fee_fixed`, `slippage_bps`
- `price_field_for_execution` (v1 default: `Close`)
- `max_positions` (optional risk control)
- `seed`

## 7. Strategy-Level Acceptance Criteria
1. Same strategy with same seed and inputs yields identical outputs.
2. Changing rebalance cadence changes trade count and PnL path.
3. Changing cost model changes net returns.
4. Contribution schedules produce expected step increases in invested capital.
5. `never` rebalance performs one initial allocation and no rebalance trades afterward.
