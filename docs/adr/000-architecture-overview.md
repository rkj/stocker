# ADR 000: Architecture Overview

- Status: Accepted
- Date: 2026-02-12
- Decision Makers: Stocker project maintainers

## Goal
Establish a high-level architecture for a deterministic, extensible stock strategy simulator over large historical datasets.

## System Overview
Stocker is composed of five major parts:
1. Data ingestion and feature preparation.
2. Simulation engine and portfolio accounting.
3. Strategy plugins and configuration.
4. Reporting/export layer.
5. Validation/testing layer.

## Data Flow
1. Load and validate market CSV input for requested date window.
2. Build date-indexed market snapshots and derived ranking features.
3. For each strategy, run deterministic daily event loop.
4. Persist daily metrics, trades, and summary outputs.
5. Run consistency and realism checks.

## Core Architectural Principles
- Deterministic by default.
- Shared engine for fair strategy comparisons.
- Strict separation between strategy intent and execution/accounting.
- Explicit assumptions documented in manifests and ADRs.
- TDD-first development with deterministic fixtures.

## ADR Map
- ADR 001: Language/tooling stack (Python + Polars + Typer + Pytest/Ruff/mypy).
- ADR 002: Layered simulation engine with explicit event order.
- ADR 003: Data ingestion/normalization model for large CSV.
- ADR 004: Strategy plugin API + declarative config schema.
- ADR 005: Testing strategy and sample-data policy.
- ADR 006: CLI-first output surface for v1.

## Scope Boundary
Included in v1:
- Historical backtesting with configurable strategy variants.
- Cost/contribution modeling.
- Daily and annual reporting outputs.

Excluded in v1:
- Live trading.
- Intraday execution.
- Tax-aware accounting.
- Interactive frontend.

## Evolution Plan
- Stabilize engine and output contracts first.
- Add strategy families through plugin extension.
- Add optional dashboard layers on top of stable exports.
- Revisit language/runtime optimization only after profiling real bottlenecks.
