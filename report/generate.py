#!/usr/bin/env python3
"""Generate the sample board report PDF from the register (reportlab, offline)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from reportlab.lib import colors                       # noqa: E402
from reportlab.lib.enums import TA_LEFT                 # noqa: E402
from reportlab.lib.pagesizes import A4                  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import cm                      # noqa: E402
from reportlab.platypus import (                        # noqa: E402
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from riskboard.sample import build_sample              # noqa: E402

INK = colors.HexColor("#1c2230")
MUTED = colors.HexColor("#5b6472")
BLUE = colors.HexColor("#2f6df6")
GRID = colors.HexColor("#e3e6ea")
GOOD = colors.HexColor("#1f9d6b")
PANEL = colors.HexColor("#f6f7f9")


def money(x: float) -> str:
    if x >= 1_000_000:
        return f"${x/1_000_000:.2f}M"
    if x >= 1_000:
        return f"${x/1_000:.0f}k"
    return f"${x:.0f}"


def build() -> Path:
    reg = build_sample()
    inh_total = sum(reg.analytic_inherent_ale(r) for r in reg.risks)
    res_total = sum(reg.analytic_residual_ale(r) for r in reg.risks)
    reduction = (1 - res_total / inh_total) * 100
    coverage = reg.coverage() * 100

    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=INK, fontSize=20,
                        spaceAfter=2, alignment=TA_LEFT)
    sub = ParagraphStyle("sub", parent=ss["Normal"], textColor=MUTED, fontSize=10, spaceAfter=10)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=INK, fontSize=13,
                        spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("body", parent=ss["Normal"], textColor=INK, fontSize=10, leading=15, spaceAfter=6)
    small = ParagraphStyle("small", parent=ss["Normal"], textColor=MUTED, fontSize=8.5, leading=12)

    out = Path(__file__).resolve().parent / "board-report.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4,
                            topMargin=1.8*cm, bottomMargin=1.6*cm,
                            leftMargin=1.9*cm, rightMargin=1.9*cm,
                            title="RiskBoard — Board Risk Report")
    el = []
    el.append(Paragraph("Quantified Risk Report", h1))
    el.append(Paragraph("Prepared for the Board Risk Committee &nbsp;·&nbsp; As of 2026-09-10", sub))
    el.append(HRFlowable(width="100%", color=GRID, spaceAfter=10))

    # KPI strip
    kpi_data = [[
        Paragraph("<b>Inherent ALE</b><br/><font size=15>%s</font>" % money(inh_total), body),
        Paragraph("<b>Residual ALE</b><br/><font size=15>%s</font>" % money(res_total), body),
        Paragraph('<b>Risk bought down</b><br/><font size=15 color="#1f9d6b">%.0f%%</font>' % reduction, body),
        Paragraph("<b>Control coverage</b><br/><font size=15>%.0f%%</font>" % coverage, body),
    ]]
    kpi = Table(kpi_data, colWidths=[4.1*cm]*4)
    kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    el.append(kpi)

    el.append(Paragraph("Executive summary", h2))
    el.append(Paragraph(
        "This report quantifies the organisation's top information-security risks in financial "
        "terms using a FAIR-style model: each risk's annual loss is simulated as Loss Event "
        "Frequency &times; Loss Magnitude, with each factor expressed as a three-point "
        "(min / most-likely / max) estimate and drawn 50,000 times by Monte-Carlo. "
        "Across the current register, modelled exposure falls from an inherent "
        f"<b>{money(inh_total)}/yr</b> to a residual <b>{money(res_total)}/yr</b> once the "
        f"controls we operate are applied &mdash; a <b>{reduction:.0f}%</b> reduction. "
        "The single largest remaining exposure is customer-PII breach; the highest-return "
        "unfunded investment is third-party risk management (CC9.2), which buys down "
        f"{money(reg.control_value('VND'))}/yr of residual loss.", body))

    el.append(Paragraph("Top risks by residual ALE", h2))
    rows = [["ID", "Risk", "Inherent", "Residual", "Cut", "Framework refs"]]
    for r in reg.top_risks_by_ale(residual=True):
        refs = ", ".join(reg._controls[cid].framework_ref for cid in r.control_ids)
        inh = reg.analytic_inherent_ale(r)
        res = reg.analytic_residual_ale(r)
        cut = (1 - res / inh) * 100
        rows.append([r.id, r.name, money(inh), money(res), f"-{cut:.0f}%", refs])
    t = Table(rows, colWidths=[1.0*cm, 5.4*cm, 2.2*cm, 2.2*cm, 1.4*cm, 4.3*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, GRID),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, GRID),
        ("ALIGN", (2, 0), (4, -1), "RIGHT"),
        ("TEXTCOLOR", (4, 1), (4, -1), GOOD),
        ("TEXTCOLOR", (5, 1), (5, -1), MUTED),
        ("FONTNAME", (5, 1), (5, -1), "Courier"),
        ("FONTSIZE", (5, 1), (5, -1), 7.5),
        ("FONTNAME", (3, 1), (3, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    el.append(t)

    el.append(Paragraph("Recommended control investments", h2))
    el.append(Paragraph(
        "Ranked by annual residual-ALE reduction per the model. Figures answer the board's "
        "question directly: what does funding this control buy us?", body))
    disabled = [c for c in reg.controls if not c.enabled]
    inv = [["Framework ref", "Control", "Annual risk bought down"]]
    for c in sorted(disabled, key=lambda c: reg.control_value(c.id), reverse=True):
        inv.append([c.framework_ref, c.name, f"{money(reg.control_value(c.id))}/yr"])
    if len(inv) == 1:
        inv.append(["—", "All catalogued controls are in place", "—"])
    it = Table(inv, colWidths=[3.0*cm, 7.5*cm, 4.0*cm], repeatRows=1)
    it.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Courier"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, GRID),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, GRID),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("TEXTCOLOR", (2, 1), (2, -1), BLUE),
        ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    el.append(it)

    el.append(Spacer(1, 10))
    el.append(HRFlowable(width="100%", color=GRID, spaceAfter=6))
    el.append(Paragraph(
        "Methodology: FAIR-style Monte-Carlo (50,000 iterations, triangular factor "
        "distributions). Controls map to ISO/IEC 27001:2022 Annex A and SOC 2 (2017 Trust "
        "Services Criteria) and reduce modelled frequency and/or magnitude multiplicatively. "
        "All figures are modelled estimates for board decision-making, not accounting values.", small))

    doc.build(el)
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return out


if __name__ == "__main__":
    build()
