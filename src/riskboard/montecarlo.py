"""FAIR-style Monte-Carlo loss quantification.

A risk's Annualised Loss Expectancy (ALE) is modelled as

    ALE = LEF * LM

where Loss Event Frequency (LEF, events/year) and Loss Magnitude (LM, currency
per event) are each a PERT/triangular distribution given as (min, likely, max).
We draw ``iterations`` samples, multiply per-iteration, and report the full loss
distribution plus summary statistics and a loss-exceedance curve.

Pure standard library -- ``random.triangular`` -- so results are deterministic
under a seed and the module has no third-party dependency.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Triangular:
    """A three-point estimate; ``low <= mode <= high``."""

    low: float
    mode: float
    high: float

    def __post_init__(self) -> None:
        if not (self.low <= self.mode <= self.high):
            raise ValueError(f"require low <= mode <= high, got {self}")
        if self.low < 0:
            raise ValueError("estimates must be non-negative")

    @property
    def mean(self) -> float:
        """Analytic mean of a triangular distribution: (low + mode + high) / 3."""
        return (self.low + self.mode + self.high) / 3.0

    def sample(self, rng: random.Random) -> float:
        return rng.triangular(self.low, self.high, self.mode)


@dataclass(frozen=True)
class LossResult:
    iterations: int
    mean_ale: float
    median_ale: float
    p90: float            # 90th percentile annual loss
    p99: float            # 99th percentile annual loss
    losses: tuple[float, ...]   # sorted ascending

    def exceedance_curve(self, points: int = 50) -> list[tuple[float, float]]:
        """Loss-exceedance curve: list of (loss, P(annual loss >= loss)).

        Monotonically non-increasing in probability as loss grows.
        """
        if not self.losses:
            return []
        lo, hi = self.losses[0], self.losses[-1]
        n = len(self.losses)
        out: list[tuple[float, float]] = []
        for i in range(points + 1):
            threshold = lo + (hi - lo) * i / points
            # count of samples >= threshold, via bisect on ascending list
            from bisect import bisect_left
            ge = n - bisect_left(self.losses, threshold)
            out.append((threshold, ge / n))
        return out


def simulate(
    lef: Triangular,
    lm: Triangular,
    iterations: int = 50_000,
    seed: int | None = None,
) -> LossResult:
    """Monte-Carlo the ALE distribution for a single risk."""
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    rng = random.Random(seed)
    losses = sorted(lef.sample(rng) * lm.sample(rng) for _ in range(iterations))

    def pct(p: float) -> float:
        idx = min(len(losses) - 1, int(p * len(losses)))
        return losses[idx]

    mean = sum(losses) / len(losses)
    median = losses[len(losses) // 2]
    return LossResult(
        iterations=iterations,
        mean_ale=mean,
        median_ale=median,
        p90=pct(0.90),
        p99=pct(0.99),
        losses=tuple(losses),
    )


def analytic_mean_ale(lef: Triangular, lm: Triangular) -> float:
    """Expected ALE for independent LEF and LM: E[LEF] * E[LM]."""
    return lef.mean * lm.mean
