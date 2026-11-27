"""Portfolio-level annual loss (all risks in the same simulated year), for the board paper.

Per-risk P90s cannot be added up; the bad year for the whole portfolio has to be simulated jointly.
Assumes the risks are independent (stated in the paper: correlation would fatten the tail).
Run:  PYTHONPATH=src python report/portfolio_tail.py
"""
import random
from riskboard.sample import build_sample

def portfolio(reg, residual=True, n=50_000, seed=11):
    rng = random.Random(seed)
    d = [reg.residual_distributions(r) if residual else (r.inherent_lef, r.inherent_lm) for r in reg.risks]
    L = sorted(sum(f.sample(rng) * m.sample(rng) for f, m in d) for _ in range(n))
    return {"mean": sum(L) / n, "median": L[n // 2], "p90": L[int(.9 * n)], "p99": L[int(.99 * n)]}

if __name__ == "__main__":
    reg = build_sample()
    rows = [("Inherent (no controls)", portfolio(reg, residual=False)), ("Residual (today)", portfolio(reg))]
    reg.set_enabled("VND", True)
    rows.append(("Residual + third-party risk mgmt", portfolio(reg)))
    print(f"{'':34}{'mean':>9}{'median':>9}{'P90':>9}{'P99':>9}")
    for name, r in rows:
        print(f"{name:34}" + "".join(f"{r[k]/1e6:>8.2f}M" for k in ("mean", "median", "p90", "p99")))
