# AGENTS.md

## Project Goal
Build a high-quality stock trading simulator that runs multiple strategies over historical data and compares performance with realistic assumptions (rebalancing, trading costs, contributions, and configurable universes).

Default dataset path for local runs:
- `/mnt/nfs-lithium-public/rkj/all_stock_data.csv`

## Mandatory Workflow
1. Run `bd prime` at session start.
2. Use beads for all planning and execution tracking.
3. Before coding:
- Create or refine issues.
- Move exactly one issue to `in_progress`.
- Confirm acceptance criteria in the issue description/notes.
4. Execute in a loop:
- Implement one issue.
- Run relevant tests/checks.
- Commit with a clear message.
- Close the issue.
- Move to the next ready issue.

## Beads Commands
```bash
bd ready
bd show <issue-id>
bd update <issue-id> --status in_progress
bd close <issue-id>
bd dep add <issue-id> <depends-on-id>
bd sync --flush-only
```

## Engineering Standards
- Strict TDD:
- Write/adjust tests first for each behavioral change.
- Keep fast unit tests for strategy/accounting logic.
- Add integration tests for end-to-end simulation scenarios.
- SOLID/DRY:
- Keep strategy logic isolated behind interfaces.
- Keep accounting rules centralized and deterministic.
- Avoid duplicated data-transformation pipelines.
- Determinism:
- Seed all random-based strategies.
- Make outputs reproducible from config + dataset + seed.
- Performance:
- Design for large CSV input (tens of millions of rows).
- Prefer streaming/iterative processing and avoid unnecessary full-memory materialization.

## Documentation Requirements
- Product requirements go in `docs/spec/`.
- Engineering decisions go in `docs/adr/` (one decision per ADR).
- Implementation starts only after core spec + ADR set is drafted.

## Simulation Requirements (Minimum)
- Strategies must include:
- S&P 500-style index proxy with daily rebalancing.
- Equal-weight universe with configurable rebalance cadence (daily/yearly/never).
- Contribution variants (daily/monthly/yearly new cash deployment).
- N-stock selection variants (explicit list, random, top/bottom by configured ranking metric).
- Inputs must include:
- Start date, end date, initial capital, contribution amount/frequency, transaction cost model, rebalance frequency, and universe filter.
- Outputs must include:
- Daily portfolio values per strategy (for charting).
- Annual summary table with return metrics.
- Comparison report across strategies.

## Session Close Checklist
1. Run all relevant tests.
2. Update/close beads issues completed in session.
3. Export issue state: `bd sync --flush-only`.
4. Ensure git is clean or only contains intentional changes.
5. Provide handoff notes with current status, risks, and next ready issue IDs.
