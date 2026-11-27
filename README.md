# RiskBoard — quantified risk + controls

<!-- at-a-glance -->
> **Security posture quantified in money a board can act on.**  
> **Result:** 11 tests — Monte-Carlo validated against the analytic expectation, monotonic control effect, framework-ID validation.  
> **Reproduce:** `pytest -q`  
> ![CI](https://github.com/fhionnghaile/riskboard/actions/workflows/ci.yml/badge.svg) [![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Fhionnghaile/riskboard/badge)](https://scorecard.dev/viewer/?uri=github.com/Fhionnghaile/riskboard)
>
> **What this is worth:** On the sample register, modelled exposure falls from $7.55M to $1.98M a year (74% bought down), and the one unfunded control is priced at $120k a year of risk removed: security spend and risk in the same currency.


A small, dependency-light risk register that turns security posture into **money the
board can act on**. Risks are modelled in financial terms with a **FAIR-style
Monte-Carlo** loss model, controls are mapped to **ISO/IEC 27001:2022 Annex A** and
**SOC 2 (2017 Trust Services Criteria)**, and the output is a board-ready dashboard and
a one-page PDF report.

> **What it proves:** risk quantification, control↔framework governance, and
> translating technical posture into a fundable decision — *"what does enabling this
> control buy us per year?"*

## The model

Each risk's Annualised Loss Expectancy is

```
ALE = Loss Event Frequency (events/yr)  ×  Loss Magnitude ($/event)
```

where LEF and LM are each a **triangular (min / most-likely / max)** estimate. We draw
50,000 Monte-Carlo samples, multiply per iteration, and report mean / median / P90 /
P99 plus a **loss-exceedance curve**. Controls reduce modelled frequency and/or
magnitude *multiplicatively*; **residual** risk is inherent risk after the enabled,
mapped controls are applied.

The core (`src/riskboard/`) is **pure standard library** — `random.triangular` — so the
simulation is deterministic under a seed and has zero third-party dependencies.

## Layout

```
src/riskboard/
  montecarlo.py   Triangular distribution + Monte-Carlo ALE + exceedance curve
  frameworks.py   ISO 27001:2022 Annex A & SOC 2 TSC catalogues + id resolver
  model.py        Risks ↔ Controls register, residual quantification, board metrics
  sample.py       A realistic 6-risk / 8-control register
  cli.py          Terminal board summary
board/generate.py   Renders board/index.html (self-contained HTML + SVG charts)
report/generate.py  Renders report/board-report.pdf (reportlab)
app.py              Flask app: serves the board + JSON register API
tests/              Monte-Carlo validation, control monotonicity, framework mapping
```

## Run it

```bash
# text summary — no dependencies
python -m riskboard.cli

# regenerate the board dashboard and PDF report
python board/generate.py          # -> board/index.html
python report/generate.py         # -> report/board-report.pdf

# live app (JSON API + dashboard)
pip install flask
python app.py                     # http://127.0.0.1:5000
#   GET /            board dashboard
#   GET /api/summary inherent/residual ALE, reduction %, coverage %
#   GET /api/risks   ranked risks with framework-mapped controls

# tests
pip install -e ".[dev]" && pytest -q
```

## What the tests pin down (the spec's acceptance cases)

| Test | Guarantee |
|------|-----------|
| `test_mc_mean_matches_analytic_within_tolerance` | Seeded Monte-Carlo mean is within 2% of the analytic expectation `E[LEF]·E[LM]` |
| `test_mc_is_deterministic_under_seed` | Same seed → identical results |
| `test_enabling_control_lowers_residual_ale_monotonically` | Enabling a control never *raises* residual ALE, and residual < inherent |
| `test_sample_controls_all_resolve_to_a_framework` | Every control maps to a real ISO 27001:2022 / SOC 2 id |
| `test_framework_rejects_plausible_but_fake_ids` | `A.5.99`, `A.9.1` and friends are rejected |
| `test_exceedance_curve_monotonic_non_increasing` | Exceedance probability is non-increasing in loss |
| `test_coverage_and_ranking`, `test_app_*` | Board metrics + live API ranked and mapped |

## Board outputs

- **`board/index.html`** — KPI strip (inherent/residual ALE, % bought down, coverage),
  top-risks inherent-vs-residual bars, portfolio loss-exceedance curve, a
  *"what enabling a control buys you"* table, and the full register.
- **`report/board-report.pdf`** — a one-page committee report: executive summary, top
  risks by residual ALE, and ranked control investments by annual risk bought down.

On the sample register, modelled exposure falls from an inherent **$7.55M/yr** to a
residual **$1.98M/yr** — a **74%** reduction — and the model prices the one unfunded
control (third-party risk management, SOC 2 **CC9.2**) at **$120k/yr** of risk bought
down.

## Scope / safety

This is a **defensive, governance** tool: it quantifies loss and scores controls. It
contains no exploit code, no scanning, and no live system access — the register is
hand-authored estimates, exactly as a risk workshop produces them. All figures are
**modelled estimates for board discussion, not accounting values.**

## Key decisions

- FAIR Monte-Carlo (Loss Event Frequency × Magnitude) → a loss-exceedance curve, not a single guess.
- Controls mapped to real ISO 27001:2022 Annex A / SOC 2 criteria, validated.
- Every control priced by the residual loss it buys down — investment ranked by return.

## Scope & limits

- Outputs are only as good as the input frequencies/magnitudes — calibrate to your loss data.
- Its companion `risk-optimizer` turns this into an exact spend optimum.

## Decision paper, threat model, decisions
- [`report/BOARD-PAPER.md`](report/BOARD-PAPER.md): a one-page decision paper for a risk committee, including bad-year (P90/P99) portfolio losses and what the numbers cannot tell you (`report/portfolio_tail.py` reproduces them).
- [`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md): STRIDE plus model risk, with evidence and stated gaps.
- [`docs/adr/`](docs/adr/): architecture decision records.

