# ADR 0001: FAIR-style Monte-Carlo with three-point estimates

Status: Accepted · Recorded 2026-11-26, retrospectively, from the design as built

## Context
Boards decide in money. A single annual-loss figure hides its uncertainty, and a red/amber/green heat map cannot be compared with any other investment.

## Decision
Each risk's annual loss is Loss Event Frequency times Loss Magnitude, each a triangular (minimum, most likely, maximum) estimate; 50,000 samples give the mean, median, P90, P99 and a loss-exceedance curve.

## Consequences
Leadership sees a distribution, not a point. The model is only as good as its estimates, which is stated with the results. The simulation is checked against the analytic expectation (within 2%) by a test.

## Alternatives considered
Single-point ALE (rejected: hides uncertainty); qualitative heat map (rejected: not comparable with spend).
