"""Live RiskBoard app: serves the board dashboard and a JSON register API.

    pip install flask
    python app.py          # -> http://127.0.0.1:5000
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from flask import Flask, jsonify, send_file  # noqa: E402

from riskboard.sample import build_sample    # noqa: E402

BOARD = Path(__file__).resolve().parent / "board" / "index.html"


def create_app() -> Flask:
    app = Flask(__name__)
    reg = build_sample()

    @app.get("/")
    def board():
        if not BOARD.exists():
            from board.generate import main as regen  # type: ignore
            regen()
        return send_file(BOARD)

    @app.get("/api/risks")
    def risks():
        return jsonify([
            {
                "id": r.id,
                "name": r.name,
                "inherent_ale": round(reg.analytic_inherent_ale(r)),
                "residual_ale": round(reg.analytic_residual_ale(r)),
                "controls": [
                    {"ref": reg._controls[c].framework_ref,
                     "framework": reg._controls[c].framework,
                     "name": reg._controls[c].name}
                    for c in r.control_ids
                ],
            }
            for r in reg.top_risks_by_ale(residual=True)
        ])

    @app.get("/api/summary")
    def summary():
        inh = sum(reg.analytic_inherent_ale(r) for r in reg.risks)
        res = sum(reg.analytic_residual_ale(r) for r in reg.risks)
        return jsonify({
            "inherent_ale": round(inh),
            "residual_ale": round(res),
            "reduction_pct": round((1 - res / inh) * 100, 1) if inh else 0,
            "coverage_pct": round(reg.coverage() * 100, 1),
            "risks": len(reg.risks),
            "controls": len(reg.controls),
        })

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
