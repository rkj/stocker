# ADR 001: Language and Tooling Stack

- Status: Accepted
- Date: 2026-02-12
- Decision Makers: Stocker project maintainers

## Context
The simulator must process a large historical CSV (~34.6M rows), support rapid strategy iteration, and maintain strict TDD quality.

Candidate languages considered:
- Python
- Go
- Rust

Evaluation criteria:
- Time to implement and evolve strategy logic.
- Numeric/data ecosystem maturity.
- Performance for batch simulation with large tabular data.
- Test tooling and developer ergonomics.

## Decision
Use Python for v1 with a typed, modular architecture.

Tooling choices:
- Runtime: Python 3.12+
- Packaging/build: `pyproject.toml` with setuptools
- CLI: Typer
- Data processing: Polars (lazy/streaming-friendly), plus standard library where sufficient
- Validation: Pydantic models for config/schema boundaries
- Testing: Pytest
- Lint/format: Ruff (lint + format)
- Type checking: mypy

## Rationale
- Python has the fastest iteration loop for strategy research and simulation rule changes.
- Polars provides efficient columnar operations and outperforms naive pandas workflows for large data.
- Strong test/lint/type toolchain keeps quality high despite dynamic language tradeoffs.
- Architecture remains portable: core interfaces are language-agnostic and could be reimplemented in Go/Rust later if needed.

## Consequences
Positive:
- Faster delivery of requested strategy variants.
- Broad contributor familiarity.
- Good balance of productivity and performance.

Negative:
- Lower raw performance ceiling than optimized Rust implementations.
- Requires discipline on typing, profiling, and memory behavior.

Mitigations:
- Keep data access and accounting loops explicit and benchmarked.
- Isolate hotspots for future optimization or native extensions.

## Alternatives Considered
Go:
- Pros: predictable performance, easy deployment.
- Cons: less ergonomic for numeric experimentation and research-style iteration.

Rust:
- Pros: best performance and memory control.
- Cons: highest development overhead for rapid prototyping and evolving strategy DSL.

## Follow-up
- Define engine/data architecture to avoid Python performance pitfalls.
- Add baseline performance benchmarks once core simulation is implemented.
