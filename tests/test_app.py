import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app


def test_summary_endpoint():
    client = create_app().test_client()
    r = client.get("/api/summary")
    assert r.status_code == 200
    data = r.get_json()
    assert data["risks"] == 6 and data["controls"] == 8
    assert data["residual_ale"] < data["inherent_ale"]
    assert 0 < data["coverage_pct"] <= 100


def test_risks_endpoint_ranked_and_mapped():
    client = create_app().test_client()
    data = client.get("/api/risks").get_json()
    ales = [r["residual_ale"] for r in data]
    assert ales == sorted(ales, reverse=True)
    for r in data:
        for c in r["controls"]:
            assert c["framework"] in ("ISO/IEC 27001:2022", "SOC 2 (2017 TSC)")
