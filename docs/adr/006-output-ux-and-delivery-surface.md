# ADR 006: Output UX and Delivery Surface

- Status: Accepted
- Date: 2026-02-12
- Decision Makers: Stocker project maintainers

## Context
Requested output could be delivered through:
- Simple web app + backend
- Full TUI
- CLI with export files

v1 priorities:
- Correct simulation and realistic results.
- Fast iteration on strategy/engine behavior.
- Deterministic outputs usable for charting.

## Decision
Choose CLI-first delivery for v1, with machine-readable exports and concise terminal summaries.

V1 UX components:
- CLI command to run one or many strategies.
- Terminal comparison table (final metrics).
- Terminal annual summary preview.
- Output directory containing CSV and manifest artifacts.

## Rationale
- Lowest implementation overhead while engine is evolving.
- Easiest to automate in research and CI workflows.
- Separates simulation correctness from presentation-layer complexity.

## Consequences
Positive:
- Faster path to validated backtesting behavior.
- Simple integration with notebooks/plotting tools later.
- Stable contract via exported files.

Negative:
- No interactive visuals in v1.
- Users need external tool for charts.

## Migration Path
- Keep reporter outputs as stable API contract.
- Future adapters can consume output artifacts:
- `web-dashboard` adapter (read CSV/manifest)
- `tui-dashboard` adapter (live table/charts)

## Alternatives Considered
Web-first implementation:
- Rejected for v1 because UI/backend complexity would slow core simulation validation.

TUI-first implementation:
- Rejected for v1 due to additional rendering/state complexity versus limited incremental value during early engine development.

## Follow-up
- Implement polished CLI with explicit output paths.
- Provide example plotting script/notebook as companion utility.
