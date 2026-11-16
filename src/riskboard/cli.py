"""Text board summary -- a quick terminal view of the register."""
from __future__ import annotations

from .sample import build_sample


def money(x: float) -> str:
    if x >= 1_000_000:
        return f"${x/1_000_000:.2f}M"
    if x >= 1_000:
        return f"${x/1_000:.0f}k"
    return f"${x:.0f}"


def main() -> None:
    reg = build_sample()
    inh = sum(reg.analytic_inherent_ale(r) for r in reg.risks)
    res = sum(reg.analytic_residual_ale(r) for r in reg.risks)
    print("RiskBoard — quantified risk posture\n" + "=" * 42)
    print(f"Inherent ALE : {money(inh):>10}")
    print(f"Residual ALE : {money(res):>10}")
    print(f"Bought down  : {(1-res/inh)*100:>9.0f}%")
    print(f"Coverage     : {reg.coverage()*100:>9.0f}%\n")
    print(f"{'ID':<3} {'Risk':<40} {'Inherent':>9} {'Residual':>9}  Refs")
    print("-" * 90)
    for r in reg.top_risks_by_ale(residual=True):
        refs = ", ".join(reg._controls[c].framework_ref for c in r.control_ids)
        print(f"{r.id:<3} {r.name[:40]:<40} "
              f"{money(reg.analytic_inherent_ale(r)):>9} "
              f"{money(reg.analytic_residual_ale(r)):>9}  {refs}")
    disabled = [c for c in reg.controls if not c.enabled]
    if disabled:
        print("\nTop unfunded control investments:")
        for c in sorted(disabled, key=lambda c: reg.control_value(c.id), reverse=True):
            print(f"  {c.framework_ref:<7} {c.name:<34} buys {money(reg.control_value(c.id))}/yr")


if __name__ == "__main__":
    main()
