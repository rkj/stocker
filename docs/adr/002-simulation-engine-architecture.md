# ADR 002: Simulation Engine Architecture

- Status: Accepted
- Date: 2026-02-12
- Decision Makers: Stocker project maintainers

## Context
The simulator must run many strategies over shared historical dates with deterministic accounting and configurable rebalancing/contributions.

Core needs:
- Single source of truth for portfolio accounting.
- Strategy logic isolated from execution/accounting mechanics.
- Clear event order to avoid hidden assumptions.

## Decision
Adopt a layered architecture with deterministic daily event processing.

Layers:
1. Data layer: provides per-date market snapshots.
2. Domain layer: portfolio state, orders, fills, cash/position accounting.
3. Strategy layer: computes target allocations based on state + market snapshot.
4. Orchestration layer: drives daily loop and applies policies.
5. Reporting layer: records daily metrics, trades, and summaries.

Daily event order (v1):
1. Load market snapshot for date.
2. Apply scheduled contribution to cash.
3. Determine if rebalance event is due for strategy.
4. If due, strategy emits target weights.
5. Execution engine derives required trades from current vs target weights.
6. Apply slippage/fees and update holdings + cash.
7. Mark-to-market positions at close price.
8. Persist daily record.

## Domain Model
- `SimulationConfig`: global run controls.
- `StrategyConfig`: per-strategy parameters.
- `PortfolioState`: cash, positions, cumulative contributions, cumulative costs.
- `Position`: symbol, shares, cost basis proxy.
- `MarketBar`: date/symbol OHLCV/dividend/split.
- `TargetAllocation`: mapping symbol -> target weight.
- `TradeFill`: executed trade with costs.
- `DailyMetrics`: equity, returns, turnover, drawdown fields.

## Rationale
- Separation of concerns enforces SOLID and simplifies testing.
- Event ordering makes contributions/rebalances reproducible and auditable.
- Shared engine allows fair strategy comparisons.

## Consequences
Positive:
- Easier to add new strategies without touching accounting.
- Strong testability for each layer.
- Deterministic replay from config + seed.

Negative:
- Slight upfront complexity from richer domain model.
- More interfaces to maintain.

## Alternatives Considered
Monolithic strategy-specific loops:
- Rejected due to duplicated accounting logic and inconsistent behavior.

Vectorized-only pipeline without explicit domain entities:
- Rejected for limited explainability and difficulty handling mixed policies (cadence + contributions + costs) cleanly.

## Follow-up
- Define strategy plugin/config interface (ADR 004).
- Define ingestion and normalization constraints (ADR 003).
