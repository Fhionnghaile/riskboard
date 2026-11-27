# ADR 0002: Pure standard-library core

Status: Accepted · Recorded 2026-11-26, retrospectively, from the design as built

## Context
A risk model that a board relies on should be reproducible years later and auditable without a dependency tree.

## Decision
The core (`src/riskboard/`) uses only the Python standard library (`random.triangular`); runs are deterministic under a seed.

## Consequences
Results reproduce exactly from a seed; there is nothing third-party to drift or to patch. Charts and PDF generation sit outside the core and may use libraries.

## Alternatives considered
NumPy/SciPy in the core (rejected: heavier, version drift, no gain at this scale).
