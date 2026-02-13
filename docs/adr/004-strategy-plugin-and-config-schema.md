# ADR 004: Strategy Plugin and Configuration Schema

- Status: Accepted
- Date: 2026-02-12
- Decision Makers: Stocker project maintainers

## Context
We need to support multiple strategy families:
- S&P 500-style proxy with daily rebalance.
- Equal-weight with varied rebalance cadence.
- Contribution variants.
- N-stock selectors (explicit/random/top/bottom).

Extensibility and deterministic behavior are required.

## Decision
Adopt a strategy plugin interface backed by a declarative configuration schema.

## Strategy Interface (Conceptual)
Each strategy plugin implements:
- `name() -> str`
- `initialize(context) -> None`
- `on_rebalance(date, portfolio_state, market_snapshot) -> TargetAllocation`
- `validate_config(config) -> None`

Engine responsibilities:
- Schedule rebalance dates.
- Invoke plugin only on rebalance events.
- Translate target allocation into executable trades.

## Configuration Schema
Top-level run config includes:
- Global simulation settings (dates, capital, costs, contribution defaults, seed).
- List of strategy configs.

Each strategy config includes:
- `strategy_id`
- `plugin`
- `universe`
- `weights`
- `rebalance`
- `contributions` (override optional)
- `random_seed` (optional override)

Example:
```yaml
strategy_id: eq_yearly_contrib_monthly
plugin: equal_weight
universe:
  mode: all_tradable
weights:
  model: equal
rebalance:
  frequency: yearly
contributions:
  amount: 1000
  frequency: monthly
execution:
  fee_bps: 2.0
  slippage_bps: 1.0
```

## Required Plugin Set (v1)
- `sp500_proxy`
- `equal_weight`
- `explicit_symbols`
- `random_n`
- `top_n_ranked`
- `bottom_n_ranked`

## Determinism Rules
- Randomized plugins must receive an explicit seed from run or strategy config.
- Plugin output must be a pure function of config + state + market snapshot.
- No wall-clock or external I/O access from plugin logic.

## Validation Rules
At startup:
- Unknown plugin names fail fast.
- Invalid cadence/frequency values fail fast.
- Invalid symbol lists fail fast when strict validation is enabled.
- `N` must be positive and not exceed tradable universe size when strict mode is on.

## Rationale
- Plugin boundary keeps strategies independent from accounting/execution.
- Declarative configs improve reproducibility and batch experimentation.
- Central validation prevents hidden runtime assumptions.

## Consequences
Positive:
- Easy to add strategies without core engine rewrites.
- Supports matrix runs by generating config combinations.

Negative:
- Requires stable plugin API and schema versioning discipline.
- Slight complexity in config parsing/validation layer.

## Alternatives Considered
Hard-coded strategies in engine switch statements:
- Rejected due to tight coupling and poor extensibility.

Fully dynamic scripting DSL for strategies:
- Rejected for v1 due to safety and debugging complexity.

## Follow-up
- Define concrete Pydantic models for config schema.
- Add plugin registry and startup self-checks.
