"""A realistic sample register for the demo, dashboard, and board report."""
from __future__ import annotations

from .model import Control, Register, Risk
from .montecarlo import Triangular as T


def build_sample() -> Register:
    reg = Register()

    controls = [
        Control("MFA",   "Phishing-resistant MFA",       "A.8.5",  lef_reduction=0.70),
        Control("EDR",   "Endpoint detection & response", "A.8.7",  lef_reduction=0.40, lm_reduction=0.30),
        Control("BKP",   "Tested offline backups",        "A.8.13", lm_reduction=0.60),
        Control("DLP",   "Data loss prevention",          "A.8.12", lef_reduction=0.35, lm_reduction=0.25),
        Control("IAM",   "Least-privilege access review",  "CC6.1", lef_reduction=0.30),
        Control("LOG",   "Centralised logging & alerting", "CC7.2", lef_reduction=0.20, lm_reduction=0.20),
        Control("VND",   "Third-party risk management",    "CC9.2", lef_reduction=0.25, enabled=False),
        Control("AWR",   "Security awareness training",    "A.6.3", lef_reduction=0.30),
    ]
    for c in controls:
        reg.add_control(c)

    risks = [
        Risk("R1", "Ransomware encrypts production",
             T(0.1, 0.4, 1.2), T(250_000, 1_200_000, 6_000_000), ["MFA", "EDR", "BKP", "AWR"]),
        Risk("R2", "Customer PII breach",
             T(0.2, 0.6, 1.5), T(400_000, 1_800_000, 9_000_000), ["IAM", "DLP", "LOG"]),
        Risk("R3", "Business email compromise / wire fraud",
             T(0.3, 1.0, 3.0), T(50_000, 300_000, 2_000_000), ["MFA", "AWR"]),
        Risk("R4", "Third-party SaaS supply-chain compromise",
             T(0.1, 0.3, 0.9), T(300_000, 900_000, 4_000_000), ["VND", "LOG"]),
        Risk("R5", "Insider data exfiltration",
             T(0.05, 0.2, 0.6), T(150_000, 700_000, 3_500_000), ["IAM", "DLP"]),
        Risk("R6", "Cloud misconfiguration exposes data store",
             T(0.2, 0.7, 2.0), T(100_000, 500_000, 2_500_000), ["LOG", "IAM"]),
    ]
    for r in risks:
        reg.add_risk(r)

    return reg
