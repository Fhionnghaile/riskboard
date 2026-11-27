# Board Risk Committee: information-security risk and one funding decision

**Paper type:** decision · **Register:** the RiskBoard sample register (6 risks, 8 controls; illustrative organisation)
**Figures:** modelled estimates (FAIR-style Monte-Carlo, 50,000 simulated years), not accounting values.
Reproduce: `python -m riskboard.cli` and `python report/portfolio_tail.py`.

## 1. Decision requested
Fund **third-party risk management** (SOC 2 CC9.2), the one control in the register not yet operated,
**if its full annual cost is below about $120k**, the expected annual loss it removes.

## 2. Where we stand
| Annual loss | No controls | Today | With third-party risk mgmt |
|---|--:|--:|--:|
| Expected (mean) | $7.55M | **$1.98M** | $1.86M |
| Typical year (median) | $7.25M | $1.91M | $1.79M |
| Bad year (1 in 10, P90) | $10.80M | **$2.81M** | $2.64M |
| Severe year (1 in 100, P99) | $14.24M | $3.68M | $3.47M |

The controls we already operate remove **74%** of expected loss. The bad-year figure matters as much as
the average: in one year in ten we should expect losses of $2.8M or more.

## 3. What is left, and why third-party risk is the next step
| Risk | Expected loss today | Note |
|---|--:|---|
| Customer PII breach | $625k | Largest remaining; already covered by access review, DLP and logging |
| Third-party SaaS supply-chain compromise | $481k | Only 36% bought down: **the weakest-covered risk**; this decision targets it |
| Cloud misconfiguration | $448k | |
| Business email compromise | $236k | |
| Insider exfiltration | $140k | |
| Ransomware | $50k | Lowest, because offline backups are assumed to work (see 5) |

Funding the control cuts expected loss by **$120k a year** and the bad-year loss by about **$170k**.

## 4. Options
1. **Fund it** (recommended if the cost is under ~$120k a year): pays for itself on expected loss alone.
2. **Fund it even at up to ~$170k**: justified only if the committee weighs the bad year above the average.
3. **Do not fund**: accept $481k expected annual loss from third-party compromise, the least-controlled risk.

## 5. What the committee should know about these numbers
- **They are estimates.** Every input is a three-point (minimum, most likely, maximum) range from the risk owners.
- **Risks are modelled as independent.** If several struck in the same year (one breach leading to another), the bad-year figures would be higher.
- **Control effectiveness is asserted, not yet measured.** The ransomware figure assumes backups cut the loss by 60%; no restore test is attached to this register. Until one is, treat the $50k ransomware figure as optimistic. (The companion phoenix project shows the evidence this needs: a timed restore drill with every file verified.)

## 6. Next report
Control effectiveness backed by evidence (drill results, detection-test results) in place of assumed percentages.
