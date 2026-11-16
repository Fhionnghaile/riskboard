import math

import pytest

from riskboard.frameworks import is_valid, resolve
from riskboard.model import Control, Register, Risk
from riskboard.montecarlo import Triangular, analytic_mean_ale, simulate
from riskboard.sample import build_sample


# -- Monte-Carlo validated against the analytic expectation -----------------
def test_mc_mean_matches_analytic_within_tolerance():
    lef = Triangular(0.2, 0.5, 1.0)
    lm = Triangular(100_000, 500_000, 1_000_000)
    res = simulate(lef, lm, iterations=200_000, seed=42)
    expected = analytic_mean_ale(lef, lm)   # E[LEF]*E[LM], independent factors
    # within 2% of the analytic mean
    assert math.isclose(res.mean_ale, expected, rel_tol=0.02), (res.mean_ale, expected)


def test_mc_is_deterministic_under_seed():
    lef, lm = Triangular(0.1, 0.4, 1.0), Triangular(1_000, 5_000, 20_000)
    a = simulate(lef, lm, iterations=10_000, seed=7)
    b = simulate(lef, lm, iterations=10_000, seed=7)
    assert a.mean_ale == b.mean_ale and a.p99 == b.p99


def test_triangular_rejects_bad_order():
    with pytest.raises(ValueError):
        Triangular(5, 2, 1)
    with pytest.raises(ValueError):
        Triangular(-1, 0, 1)


# -- Control effect: enabling a control lowers residual ALE monotonically ----
def test_enabling_control_lowers_residual_ale_monotonically():
    reg = build_sample()
    r = next(x for x in reg.risks if x.id == "R2")  # maps IAM, DLP, LOG

    def residual():
        return reg.analytic_residual_ale(r)

    # start with all three disabled, enable one at a time
    for cid in ("IAM", "DLP", "LOG"):
        reg.set_enabled(cid, False)

    prev = residual()
    for cid in ("IAM", "DLP", "LOG"):
        reg.set_enabled(cid, True)
        now = residual()
        assert now <= prev + 1e-9, f"enabling {cid} raised residual ALE"
        prev = now

    # residual must end strictly below inherent
    assert reg.analytic_residual_ale(r) < reg.analytic_inherent_ale(r)


def test_control_value_is_positive_for_effective_control():
    reg = build_sample()
    # VND is disabled in the sample; enabling it must buy down ALE
    assert reg.control_value("VND") > 0


# -- Framework mapping: every control resolves to a real id ------------------
def test_sample_controls_all_resolve_to_a_framework():
    reg = build_sample()
    for c in reg.controls:
        fw = resolve(c.framework_ref)
        assert fw in ("ISO/IEC 27001:2022", "SOC 2 (2017 TSC)")


def test_framework_rejects_plausible_but_fake_ids():
    assert is_valid("A.5.7") and is_valid("CC6.1")
    assert not is_valid("A.5.99")   # well-formed but not a real control
    assert not is_valid("A.9.1")    # no A.9 theme in 2022
    assert not is_valid("ZZ1.1")
    with pytest.raises(ValueError):
        Control("x", "bad", "A.9.1")


# -- Loss-exceedance curve is monotonic non-increasing -----------------------
def test_exceedance_curve_monotonic_non_increasing():
    res = simulate(Triangular(0.1, 0.5, 1.5), Triangular(10_000, 80_000, 400_000),
                   iterations=20_000, seed=3)
    curve = res.exceedance_curve(points=60)
    probs = [p for _, p in curve]
    assert probs[0] == pytest.approx(1.0, abs=1e-9)
    for a, b in zip(probs, probs[1:]):
        assert b <= a + 1e-12
    assert probs[-1] >= 0.0


# -- Board metrics -----------------------------------------------------------
def test_coverage_and_ranking():
    reg = build_sample()
    cov = reg.coverage()
    assert 0.0 < cov <= 1.0
    ranked = reg.top_risks_by_ale(residual=True, limit=3)
    vals = [reg.analytic_residual_ale(r) for r in ranked]
    assert vals == sorted(vals, reverse=True) and len(ranked) == 3
