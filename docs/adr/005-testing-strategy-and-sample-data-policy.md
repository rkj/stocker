# ADR 005: Testing Strategy and Sample-Data Policy

- Status: Accepted
- Date: 2026-02-12
- Decision Makers: Stocker project maintainers

## Context
The project requires strict TDD and confidence that strategy/accounting behavior is correct under many parameter combinations.

Constraints:
- Production dataset is large (~3.3GB CSV).
- Tests must stay fast and deterministic.

## Decision
Adopt a three-layer test strategy with deterministic synthetic fixtures generated at test runtime.

## Test Layers
1. Unit tests (fast, isolated)
- Portfolio accounting invariants.
- Rebalance scheduling rules.
- Weight normalization and allocation edge cases.
- Cost model calculations.

2. Integration tests (medium)
- Data ingest + strategy + execution + metrics for small fixture windows.
- Multi-strategy comparative runs on shared window.

3. Acceptance/regression tests (slower but bounded)
- End-to-end CLI runs producing output files.
- Determinism checks across repeated runs with fixed seed.

## Fixture Policy
- Generate deterministic synthetic datasets at test runtime.
- Keep integration fixtures self-contained and non-proprietary.
- Include representative cases:
- multiple symbols
- long enough window for rolling metrics
- sparse symbol coverage
- at least one dividend and split row where possible
- Fixture generation must be reproducible from explicit seed/formula.

Fixture storage:
- No external market-data slices are checked into the repository.

## TDD Workflow Rules
For each behavioral change:
1. Add/modify failing test first.
2. Implement minimal production change.
3. Refactor while tests remain green.
4. Add regression test if bug fix.

Required CI/local gates before closing an implementation issue:
- `pytest`
- `ruff check`
- `mypy` (core package)

## Determinism Rules
- Random strategies must use seeded RNG abstraction.
- Output ordering must be stable (for deterministic snapshots).
- Time-based or environment-dependent behavior is prohibited in core logic.

## Rationale
- Balances correctness and execution speed.
- Keeps heavy production data out of routine test loops.
- Supports strict TDD expectation from project requirements.

## Consequences
Positive:
- High confidence in accounting and strategy correctness.
- Faster developer iteration due to compact fixtures.
- No data-licensing risk from redistributed market data.

Negative:
- Requires maintenance of synthetic fixture generators.
- Some full-scale performance issues only surface in dedicated benchmark runs.

## Alternatives Considered
Testing only with full dataset:
- Rejected due to slow feedback loop.

Only unit tests without integration layer:
- Rejected due to risk of interface/integration regressions.

## Follow-up
- Keep fixture extraction utility for local/private workflows only.
- Add benchmark command separate from test suite.
