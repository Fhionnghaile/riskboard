#!/usr/bin/env python3
"""Render the board dashboard (self-contained HTML) from the sample register.

Deterministic: analytic ALE drives the rankings and KPIs; a seeded Monte-Carlo
drives the portfolio loss-exceedance curve. No network, no external assets.
"""
from __future__ import annotations

import html
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from riskboard.model import Register, Risk           # noqa: E402
from riskboard.sample import build_sample            # noqa: E402

AS_OF = "2026-09-10"

INK = "#1c2230"
MUTED = "#5b6472"
SURFACE = "#ffffff"
PANEL = "#f6f7f9"
GRID = "#e3e6ea"
INHERENT = "#9aa7bd"     # muted: the risk before controls
RESIDUAL = "#2f6df6"     # strong: the risk the board governs
GOOD = "#1f9d6b"
WARN = "#d9870b"


def money(x: float) -> str:
    if x >= 1_000_000:
        return f"${x/1_000_000:.2f}M"
    if x >= 1_000:
        return f"${x/1_000:.0f}k"
    return f"${x:.0f}"


def portfolio_exceedance(reg: Register, iterations: int = 40_000, seed: int = 11):
    """Aggregate annual loss = sum of per-risk annual losses, independent draws."""
    rng = random.Random(seed)
    totals = []
    risks = reg.risks
    resid = {r.id: reg.residual_distributions(r) for r in risks}
    for _ in range(iterations):
        t = 0.0
        for r in risks:
            lef, lm = resid[r.id]
            t += lef.sample(rng) * lm.sample(rng)
        totals.append(t)
    totals.sort()
    n = len(totals)
    lo, hi = totals[0], totals[-1]
    from bisect import bisect_left
    pts = []
    for i in range(61):
        thr = lo + (hi - lo) * i / 60
        ge = n - bisect_left(totals, thr)
        pts.append((thr, ge / n))
    mean = sum(totals) / n
    p90 = totals[int(0.90 * n)]
    p99 = totals[int(0.99 * n)]
    return pts, mean, p90, p99


def bar_chart(reg: Register) -> str:
    risks = reg.top_risks_by_ale(residual=True)
    rows = []
    maxv = max(reg.analytic_inherent_ale(r) for r in risks)
    W, rowh, lblw = 560, 46, 230
    h = len(risks) * rowh + 20
    bars = []
    for i, r in enumerate(risks):
        y = 10 + i * rowh
        inh = reg.analytic_inherent_ale(r)
        res = reg.analytic_residual_ale(r)
        wi = (inh / maxv) * W
        wr = (res / maxv) * W
        name = html.escape(r.name if len(r.name) < 34 else r.name[:31] + "...")
        bars.append(f'''
      <text x="{lblw-10}" y="{y+16}" text-anchor="end" class="rl">{name}</text>
      <rect x="{lblw}" y="{y+4}" width="{wi:.1f}" height="12" rx="3" fill="{INHERENT}"><title>{html.escape(r.name)} inherent {money(inh)}</title></rect>
      <rect x="{lblw}" y="{y+20}" width="{wr:.1f}" height="12" rx="3" fill="{RESIDUAL}"><title>{html.escape(r.name)} residual {money(res)}</title></rect>
      <text x="{lblw+max(wi,wr)+8}" y="{y+16}" class="val">{money(inh)} &#8594; {money(res)}</text>''')
    rows.append("".join(bars))
    return f'''<svg viewBox="0 0 {lblw+W+120} {h}" role="img" aria-label="Top risks by annualised loss expectancy, inherent versus residual">
      {''.join(rows)}
    </svg>'''


def exceedance_chart(pts) -> str:
    W, H, padL, padB, padT = 560, 240, 70, 36, 14
    xs = [p[0] for p in pts]
    xmax = xs[-1] or 1.0
    def X(v): return padL + (v / xmax) * (W - padL - 10)
    def Y(p): return padT + (1 - p) * (H - padT - padB)
    path = " ".join(
        f"{'M' if i == 0 else 'L'}{X(v):.1f},{Y(p):.1f}" for i, (v, p) in enumerate(pts)
    )
    # gridlines on probability axis
    grid = []
    for p in (0, 0.25, 0.5, 0.75, 1.0):
        y = Y(p)
        grid.append(f'<line x1="{padL}" y1="{y:.1f}" x2="{W-10}" y2="{y:.1f}" stroke="{GRID}"/>'
                    f'<text x="{padL-8}" y="{y+4:.1f}" text-anchor="end" class="ax">{int(p*100)}%</text>')
    xticks = []
    for i in range(5):
        v = xmax * i / 4
        x = X(v)
        xticks.append(f'<text x="{x:.1f}" y="{H-padB+20}" text-anchor="middle" class="ax">{money(v)}</text>')
    area = f"M{X(0):.1f},{Y(0):.1f} " + path[1:] + f" L{X(xmax):.1f},{Y(0):.1f} Z"
    return f'''<svg viewBox="0 0 {W+10} {H+6}" role="img" aria-label="Portfolio loss-exceedance curve">
      {''.join(grid)}
      <path d="{area}" fill="{RESIDUAL}" opacity="0.08"/>
      <path d="{path}" fill="none" stroke="{RESIDUAL}" stroke-width="2.5"/>
      {''.join(xticks)}
      <text x="{(W+padL)/2}" y="{H+4}" text-anchor="middle" class="axl">Annual portfolio loss (residual)</text>
    </svg>'''


def main() -> None:
    reg = build_sample()
    pts, port_mean, p90, p99 = portfolio_exceedance(reg)

    inh_total = sum(reg.analytic_inherent_ale(r) for r in reg.risks)
    res_total = sum(reg.analytic_residual_ale(r) for r in reg.risks)
    reduction = (1 - res_total / inh_total) * 100 if inh_total else 0.0
    coverage = reg.coverage() * 100

    # "what closing control X buys you" -- disabled controls ranked
    disabled = [c for c in reg.controls if not c.enabled]
    buys = sorted(((c, reg.control_value(c.id)) for c in disabled),
                  key=lambda t: t[1], reverse=True)

    # register table rows
    reg_rows = []
    for r in reg.top_risks_by_ale(residual=True):
        refs = ", ".join(html.escape(reg._controls[cid].framework_ref) for cid in r.control_ids)
        inh = reg.analytic_inherent_ale(r)
        res = reg.analytic_residual_ale(r)
        cut = (1 - res / inh) * 100 if inh else 0
        reg_rows.append(f'''<tr>
          <td class="rid">{html.escape(r.id)}</td>
          <td>{html.escape(r.name)}</td>
          <td class="num">{money(inh)}</td>
          <td class="num"><strong>{money(res)}</strong></td>
          <td class="num cut">-{cut:.0f}%</td>
          <td class="refs">{refs}</td>
        </tr>''')

    buys_rows = "".join(
        f'''<tr><td class="rid">{html.escape(c.framework_ref)}</td>
            <td>{html.escape(c.name)}</td>
            <td class="num buys">{money(v)}/yr</td></tr>'''
        for c, v in buys
    ) or '<tr><td colspan="3" class="muted">All controls enabled.</td></tr>'

    doc = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RiskBoard — Quantified Risk Posture</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: {PANEL}; color: {INK};
    font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  .wrap {{ max-width: 1040px; margin: 0 auto; padding: 28px 20px 60px; }}
  header {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px; }}
  h1 {{ font-size: 22px; margin: 0; letter-spacing: -0.01em; }}
  .asof {{ color: {MUTED}; font-size: 13px; }}
  .sub {{ color: {MUTED}; margin: 2px 0 22px; font-size: 14px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }}
  .kpi {{ background: {SURFACE}; border: 1px solid {GRID}; border-radius: 12px; padding: 16px 18px; }}
  .kpi .k {{ color: {MUTED}; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }}
  .kpi .v {{ font-size: 26px; font-weight: 650; margin-top: 6px; letter-spacing: -0.01em; }}
  .kpi .v.good {{ color: {GOOD}; }}
  .panel {{ background: {SURFACE}; border: 1px solid {GRID}; border-radius: 12px; padding: 18px 20px; margin-bottom: 20px; }}
  .panel h2 {{ font-size: 15px; margin: 0 0 4px; }}
  .panel p.note {{ color: {MUTED}; font-size: 13px; margin: 0 0 12px; }}
  .legend {{ display: flex; gap: 18px; font-size: 13px; color: {MUTED}; margin: 2px 0 10px; }}
  .legend span.sw {{ display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 6px; vertical-align: middle; }}
  svg text.rl {{ font-size: 12px; fill: {INK}; }}
  svg text.val {{ font-size: 11px; fill: {MUTED}; }}
  svg text.ax {{ font-size: 11px; fill: {MUTED}; }}
  svg text.axl {{ font-size: 12px; fill: {MUTED}; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
  th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid {GRID}; }}
  th {{ color: {MUTED}; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.03em; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
  td.rid {{ font-family: ui-monospace, "SF Mono", Menlo, monospace; color: {MUTED}; font-size: 12.5px; }}
  td.cut {{ color: {GOOD}; font-weight: 600; }}
  td.buys {{ color: {RESIDUAL}; font-weight: 650; }}
  td.refs {{ font-family: ui-monospace, Menlo, monospace; font-size: 12px; color: {MUTED}; }}
  .muted {{ color: {MUTED}; }}
  .two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  footer {{ color: {MUTED}; font-size: 12px; margin-top: 10px; text-align: center; }}
  @media (max-width: 720px) {{ .kpis {{ grid-template-columns: repeat(2,1fr); }} .two {{ grid-template-columns: 1fr; }} }}
</style></head>
<body><div class="wrap">
  <header>
    <h1>RiskBoard — Quantified Risk Posture</h1>
    <span class="asof">As of {AS_OF}</span>
  </header>
  <p class="sub">FAIR-style Monte-Carlo loss model · {len(reg.risks)} risks · {len(reg.controls)} controls mapped to ISO/IEC 27001:2022 &amp; SOC 2</p>

  <div class="kpis">
    <div class="kpi"><div class="k">Inherent ALE</div><div class="v">{money(inh_total)}</div></div>
    <div class="kpi"><div class="k">Residual ALE</div><div class="v">{money(res_total)}</div></div>
    <div class="kpi"><div class="k">Risk bought down</div><div class="v good">{reduction:.0f}%</div></div>
    <div class="kpi"><div class="k">Control coverage</div><div class="v">{coverage:.0f}%</div></div>
  </div>

  <div class="panel">
    <h2>Top risks — inherent vs residual ALE</h2>
    <p class="note">What each risk would cost per year before controls, and after the controls we actually run.</p>
    <div class="legend"><div><span class="sw" style="background:{INHERENT}"></span>Inherent</div><div><span class="sw" style="background:{RESIDUAL}"></span>Residual</div></div>
    {bar_chart(reg)}
  </div>

  <div class="two">
    <div class="panel">
      <h2>Portfolio loss-exceedance</h2>
      <p class="note">Probability that total annual loss meets or exceeds a given amount. P90 {money(p90)} · P99 {money(p99)}.</p>
      {exceedance_chart(pts)}
    </div>
    <div class="panel">
      <h2>What enabling a control buys you</h2>
      <p class="note">Annual residual-ALE reduction from switching on a control not yet in place.</p>
      <table><thead><tr><th>Ref</th><th>Control</th><th>Buys / yr</th></tr></thead>
      <tbody>{buys_rows}</tbody></table>
    </div>
  </div>

  <div class="panel">
    <h2>Risk register</h2>
    <table><thead><tr><th>ID</th><th>Risk</th><th>Inherent</th><th>Residual</th><th>Cut</th><th>Mapped controls</th></tr></thead>
    <tbody>{''.join(reg_rows)}</tbody></table>
  </div>

  <footer>Generated by RiskBoard · figures are modelled estimates for board discussion, not accounting values.</footer>
</div></body></html>'''

    out = Path(__file__).resolve().parent / "index.html"
    out.write_text(doc, encoding="utf-8")
    print(f"wrote {out} ({len(doc)} bytes); inherent {money(inh_total)} residual {money(res_total)} reduction {reduction:.0f}%")


if __name__ == "__main__":
    main()
