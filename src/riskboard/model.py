"""Risk register: risks, controls, and the many-to-many mapping between them.

Controls are mapped to a framework reference (ISO 27001:2022 Annex A or SOC 2
TSC) and, when enabled, reduce a risk's Loss Event Frequency and/or Loss
Magnitude. Residual risk is the inherent risk after the enabled, mapped controls
are applied -- the number a board actually governs against.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .frameworks import resolve
from .montecarlo import LossResult, Triangular, analytic_mean_ale, simulate


@dataclass(frozen=True)
class Control:
    id: str
    name: str
    framework_ref: str          # e.g. "A.8.7" or "CC6.1"
    lef_reduction: float = 0.0  # fraction [0,1] by which it cuts frequency
    lm_reduction: float = 0.0   # fraction [0,1] by which it cuts magnitude
    enabled: bool = True

    def __post_init__(self) -> None:
        resolve(self.framework_ref)  # raises if the id is not a real control
        for r in (self.lef_reduction, self.lm_reduction):
            if not 0.0 <= r <= 1.0:
                raise ValueError("reductions must lie in [0, 1]")

    @property
    def framework(self) -> str:
        return resolve(self.framework_ref)


@dataclass
class Risk:
    id: str
    name: str
    inherent_lef: Triangular
    inherent_lm: Triangular
    control_ids: list[str] = field(default_factory=list)


def _scale(t: Triangular, factor: float) -> Triangular:
    return Triangular(t.low * factor, t.mode * factor, t.high * factor)


class Register:
    """A collection of risks and controls with FAIR quantification helpers."""

    def __init__(self) -> None:
        self._risks: dict[str, Risk] = {}
        self._controls: dict[str, Control] = {}

    # -- construction -------------------------------------------------------
    def add_control(self, control: Control) -> None:
        self._controls[control.id] = control

    def add_risk(self, risk: Risk) -> None:
        for cid in risk.control_ids:
            if cid not in self._controls:
                raise KeyError(f"risk {risk.id!r} maps unknown control {cid!r}")
        self._risks[risk.id] = risk

    @property
    def risks(self) -> list[Risk]:
        return list(self._risks.values())

    @property
    def controls(self) -> list[Control]:
        return list(self._controls.values())

    def set_enabled(self, control_id: str, enabled: bool) -> None:
        c = self._controls[control_id]
        self._controls[control_id] = Control(
            c.id, c.name, c.framework_ref, c.lef_reduction, c.lm_reduction, enabled
        )

    # -- quantification -----------------------------------------------------
    def _mapped_controls(self, risk: Risk, *, enabled_only: bool) -> list[Control]:
        cs = [self._controls[cid] for cid in risk.control_ids]
        return [c for c in cs if c.enabled] if enabled_only else cs

    def residual_distributions(self, risk: Risk) -> tuple[Triangular, Triangular]:
        """Inherent LEF/LM scaled by the combined effect of enabled controls.

        Reductions combine multiplicatively: two controls each cutting LEF by
        50% leave 0.5 * 0.5 = 25% of the original frequency.
        """
        lef_factor = lm_factor = 1.0
        for c in self._mapped_controls(risk, enabled_only=True):
            lef_factor *= (1.0 - c.lef_reduction)
            lm_factor *= (1.0 - c.lm_reduction)
        return _scale(risk.inherent_lef, lef_factor), _scale(risk.inherent_lm, lm_factor)

    def inherent_ale(self, risk: Risk, *, iterations: int = 50_000, seed: int | None = None) -> LossResult:
        return simulate(risk.inherent_lef, risk.inherent_lm, iterations, seed)

    def residual_ale(self, risk: Risk, *, iterations: int = 50_000, seed: int | None = None) -> LossResult:
        lef, lm = self.residual_distributions(risk)
        return simulate(lef, lm, iterations, seed)

    def analytic_inherent_ale(self, risk: Risk) -> float:
        return analytic_mean_ale(risk.inherent_lef, risk.inherent_lm)

    def analytic_residual_ale(self, risk: Risk) -> float:
        lef, lm = self.residual_distributions(risk)
        return analytic_mean_ale(lef, lm)

    # -- board metrics ------------------------------------------------------
    def coverage(self) -> float:
        """Share of risks that have at least one enabled, mapped control."""
        if not self._risks:
            return 0.0
        covered = sum(
            1 for r in self._risks.values()
            if self._mapped_controls(r, enabled_only=True)
        )
        return covered / len(self._risks)

    def top_risks_by_ale(self, *, residual: bool = True, limit: int | None = None):
        """Risks ranked by analytic ALE (fast, deterministic ordering)."""
        fn = self.analytic_residual_ale if residual else self.analytic_inherent_ale
        ranked = sorted(self._risks.values(), key=fn, reverse=True)
        return ranked[:limit] if limit else ranked

    def control_value(self, control_id: str, *, seed: int | None = 7) -> float:
        """ALE reduction ($/yr) from enabling one currently-disabled control.

        'What closing control X buys you' -- summed across every risk it maps to.
        """
        before = sum(self.analytic_residual_ale(r) for r in self._risks.values())
        c = self._controls[control_id]
        was = c.enabled
        self.set_enabled(control_id, True)
        after = sum(self.analytic_residual_ale(r) for r in self._risks.values())
        self.set_enabled(control_id, was)
        return before - after
