"""Exact unit tests for the risk model's core, aimed at what mutation testing showed the
statistical tests miss (28 Nov 2026). Degenerate estimates (low = mode = high) make every
Monte-Carlo result exact, so arithmetic mistakes can't hide inside sampling noise."""
import random
import pytest
from riskboard.model import Control, Register, Risk
from riskboard.montecarlo import LossResult, Triangular, analytic_mean_ale, simulate

T = Triangular


# ---- Triangular ------------------------------------------------------------------------------
def test_triangular_mean_and_validation_edges():
    assert T(1, 2, 6).mean == pytest.approx(3.0)
    T(0, 0, 0); T(2, 2, 2); T(1, 1, 5); T(1, 5, 5)          # equalities are allowed
    for bad in ((2, 1, 3), (1, 3, 2), (-1, 0, 1)):
        with pytest.raises(ValueError):
            T(*bad)

def test_triangular_sample_stays_in_range_and_degenerate_is_exact():
    rng = random.Random(1)
    t = T(10, 20, 50)
    xs = [t.sample(rng) for _ in range(2000)]
    assert min(xs) >= 10 and max(xs) <= 50
    assert sum(xs) / len(xs) == pytest.approx(t.mean, rel=0.05)   # mode honoured, not swapped with high
    assert T(7, 7, 7).sample(rng) == 7


# ---- simulate: exact on degenerate inputs ----------------------------------------------------
def test_simulate_degenerate_is_exact():
    r = simulate(T(2, 2, 2), T(500, 500, 500), iterations=10, seed=0)
    assert (r.iterations, r.mean_ale, r.median_ale, r.p90, r.p99) == (10, 1000, 1000, 1000, 1000)
    assert r.losses == (1000.0,) * 10
    assert analytic_mean_ale(T(2, 2, 2), T(500, 500, 500)) == 1000

def test_simulate_rejects_non_positive_iterations():
    for n in (0, -1):
        with pytest.raises(ValueError):
            simulate(T(1, 1, 1), T(1, 1, 1), iterations=n)
    assert simulate(T(1, 1, 1), T(1, 1, 1), iterations=1).iterations == 1

def test_percentiles_median_and_sorting_on_a_known_sample():
    # LEF ~ U-shaped is hard to control, so use LM = 1 and a wide LEF: losses are LEF samples.
    r = simulate(T(0, 50, 100), T(1, 1, 1), iterations=1000, seed=3)
    assert list(r.losses) == sorted(r.losses)
    assert r.median_ale == r.losses[500]
    assert r.p90 == r.losses[900] and r.p99 == r.losses[990]
    assert r.losses[0] <= r.median_ale <= r.p90 <= r.p99 <= r.losses[-1]
    assert r.mean_ale == pytest.approx(sum(r.losses) / 1000)


# ---- exceedance curve -------------------------------------------------------------------------
def test_exceedance_curve_exact_values():
    r = LossResult(iterations=4, mean_ale=2.5, median_ale=3, p90=4, p99=4, losses=(1.0, 2.0, 3.0, 4.0))
    curve = r.exceedance_curve(points=3)        # thresholds 1, 2, 3, 4
    assert curve == [(1.0, 1.0), (2.0, 0.75), (3.0, 0.5), (4.0, 0.25)]
    assert LossResult(0, 0, 0, 0, 0, ()).exceedance_curve() == []
    assert len(r.exceedance_curve()) == 51       # default 50 intervals + the start


# ---- Control validation -----------------------------------------------------------------------
def test_control_reduction_bounds_are_inclusive():
    Control("a", "A", "A.8.7", 0.0, 1.0)
    Control("b", "B", "A.8.7", 1.0, 0.0)
    for lef, lm in ((-0.01, 0), (1.01, 0), (0, -0.01), (0, 1.01)):
        with pytest.raises(ValueError):
            Control("c", "C", "A.8.7", lef, lm)
    assert Control("d", "D", "A.8.7").framework


# ---- Register: exact residual arithmetic ------------------------------------------------------
def reg():
    r = Register()
    r.add_control(Control("F", "freq", "A.8.7", lef_reduction=0.5))
    r.add_control(Control("M", "mag", "A.8.13", lm_reduction=0.25))
    r.add_control(Control("G", "freq2", "A.8.5", lef_reduction=0.5))
    r.add_control(Control("OFF", "off", "CC9.2", lef_reduction=0.9, enabled=False))
    r.add_risk(Risk("R1", "one", T(4, 4, 4), T(100, 100, 100), ["F", "M", "G", "OFF"]))
    r.add_risk(Risk("R2", "two", T(1, 1, 1), T(10, 10, 10), []))
    return r

def test_residual_combines_reductions_multiplicatively_and_skips_disabled():
    r = reg()
    lef, lm = r.residual_distributions(r.risks[0])
    assert (lef.low, lef.mode, lef.high) == (1.0, 1.0, 1.0)     # 4 * 0.5 * 0.5; OFF ignored
    assert (lm.low, lm.mode, lm.high) == (75.0, 75.0, 75.0)     # 100 * 0.75
    assert r.analytic_inherent_ale(r.risks[0]) == 400
    assert r.analytic_residual_ale(r.risks[0]) == 75
    assert r.residual_ale(r.risks[0], iterations=5, seed=1).mean_ale == pytest.approx(75)
    assert r.inherent_ale(r.risks[0], iterations=5, seed=1).mean_ale == pytest.approx(400)

def test_control_value_exact_and_state_restored():
    r = reg()
    assert r.control_value("OFF") == pytest.approx(75 - 7.5)     # LEF 1 -> 0.1
    assert [c.enabled for c in r.controls if c.id == "OFF"] == [False]
    assert r.control_value("F") == pytest.approx(0)              # already enabled: buys nothing more

def test_set_enabled_keeps_every_other_field():
    r = reg()
    r.set_enabled("F", False)
    c = [c for c in r.controls if c.id == "F"][0]
    assert (c.name, c.framework_ref, c.lef_reduction, c.lm_reduction, c.enabled) == ("freq", "A.8.7", 0.5, 0.0, False)

def test_coverage_ranking_and_limits():
    r = reg()
    assert r.coverage() == 0.5
    assert Register().coverage() == 0.0
    assert [x.id for x in r.top_risks_by_ale()] == ["R1", "R2"]
    assert [x.id for x in r.top_risks_by_ale(limit=1)] == ["R1"]
    assert [x.id for x in r.top_risks_by_ale(residual=False)] == ["R1", "R2"]
    for cid in ("F", "M", "G"):
        r.set_enabled(cid, False)
    assert r.coverage() == 0.0

def test_add_risk_rejects_unknown_control_and_lists_are_copies():
    r = reg()
    with pytest.raises(KeyError):
        r.add_risk(Risk("R3", "three", T(1, 1, 1), T(1, 1, 1), ["NOPE"]))
    assert len(r.risks) == 2 and len(r.controls) == 4
    r.risks.clear()
    assert len(r.risks) == 2
