# RiskBoard: threat model

Method: STRIDE plus model risk, written 2026-11-26 against the code as it stands. For a decision tool
the main danger is not a hacker taking it over but a board acting on wrong numbers, so model risk
gets its own section. Status: **Mitigated**, **Partial**, **Gap**, **Accepted**.

**Assets:** the integrity of the figures the board sees, and the trust leadership places in them.
**Elements:** the register (risks, controls, estimates, in `src/riskboard/sample.py`), the Monte-Carlo
engine, the generated board page and PDF, and a read-only Flask API.

## STRIDE
| # | Threat | Mitigation (evidence) | Status |
|---|---|---|---|
| T1 | Someone edits estimates to make the picture look better | The register is code under git: every change has an author, a diff and a review point | Mitigated |
| T2 | Invalid inputs produce plausible-looking nonsense | Control reductions must lie in [0, 1]; every framework ref must be a real ISO 27001:2022 or SOC 2 control; a risk cannot map an unknown control (`model.py`; framework-mapping tests) | Mitigated |
| T3 | A circulated PDF or board page is altered after generation | Outputs are unsigned | **Gap**, fix F2 |
| R1 | Nobody can say who changed which estimate, or why | git history gives who and when; the why depends on commit messages | Partial |
| I1 | The register itself is sensitive (it lists the organisation's weak points) | API binds to 127.0.0.1 only, with debug off (`app.py`) | Partial: no authentication if deployed beyond a laptop, fix F3 |
| I2 | Script injection through risk or control names in the board page | All names are HTML-escaped when rendered (`board/generate.py`) | Mitigated |
| D1 | Expensive simulation requests | The API is read-only and computes from the fixed register; nothing user-supplied reaches the simulator | Mitigated |
| E1 | Privilege escalation through the API | Only GET routes exist; there is no write path | Mitigated |

## Model risk
| # | Risk | Mitigation (evidence) | Status |
|---|---|---|---|
| M1 | The simulation is wrong | Seeded Monte-Carlo mean is within 2% of the analytic expectation (test); enabling a control never raises residual loss (test) | Mitigated |
| M2 | Estimates are guesses | Three-point estimates make the uncertainty explicit; reports state the figures are modelled, not accounting values | Accepted, stated on every report |
| M3 | Risks are treated as independent, which understates the bad-year tail if they are correlated | Stated in the board paper next to the tail figures | Accepted, stated |
| M4 | Control effectiveness is asserted, not measured | None yet | **Gap**, fix F1 |
| M5 | Controls stack multiplicatively, which may overstate the benefit of overlapping controls | None yet | **Gap**, fix F1 |

## Fixes, in priority order
- **F1 (M4, M5):** tie each control's effectiveness to evidence (test results, detection rates from mini-soc, drill results from phoenix) and add an overlap discount for controls that address the same loss path.
- **F2 (T3):** hash each generated report and append it to `crypto-audit-log`, so any copy can be checked against the original.
- **F3 (I1):** if hosted, put it behind single sign-on and restrict access to the risk committee.
