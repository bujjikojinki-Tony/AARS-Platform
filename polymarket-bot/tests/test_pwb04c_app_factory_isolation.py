from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app_factory import create_app
from backend.models.polymarket import MarketSourceMode


def test_create_app_isolates_sqlite_state(tmp_path):
    db_one = tmp_path / "pwb04c_one.sqlite"
    db_two = tmp_path / "pwb04c_two.sqlite"

    app_one = create_app(str(db_one), allow_network=False)
    app_two = create_app(str(db_two), allow_network=False)

    client_one = TestClient(app_one)
    client_two = TestClient(app_two)

    health_one = client_one.get("/healthz")
    health_two = client_two.get("/healthz")
    assert health_one.status_code == 200
    assert health_two.status_code == 200
    assert health_one.json()["db_path"] == str(db_one)
    assert health_two.json()["db_path"] == str(db_two)
    assert health_one.json()["allow_network"] is False
    assert health_two.json()["allow_network"] is False
    assert health_one.json()["allow_polymarket_network"] is False
    assert health_two.json()["allow_polymarket_network"] is False
    assert health_one.json()["market_source_mode"] == "MOCK_ONLY"
    assert health_two.json()["market_source_mode"] == "MOCK_ONLY"
    assert health_one.json()["live_execution"] is False
    assert health_two.json()["live_execution"] is False

    engines = client_one.get("/api/probability/engines")
    assert engines.status_code == 200
    engine_ids = {item["engine_id"] for item in engines.json()["engines"]}
    assert {"gaussian_v0", "deb_shadow_v0", "emos_shadow_v0"}.issubset(engine_ids)

    scan_one = client_one.post("/api/opportunities/scan")
    assert scan_one.status_code == 200
    scan_body = scan_one.json()
    assert scan_body["status"] == "ok"
    assert scan_body["candidates_count"] >= 1

    workstation_one = client_one.get("/api/workstation/mock_weather_strong_yes")
    assert workstation_one.status_code == 200
    work_one = workstation_one.json()
    assert work_one["status"] == "ok"
    assert work_one["candidate"] is not None

    workstation_two = client_two.get("/api/workstation/mock_weather_strong_yes")
    assert workstation_two.status_code == 200
    work_two = workstation_two.json()
    assert work_two["status"] == "error"
    assert work_two["message"] == "no workstation data found for market"


def test_live_execute_remains_rejected_in_isolated_app(tmp_path):
    app = create_app(str(tmp_path / "pwb04c_live.sqlite"), allow_network=False)
    client = TestClient(app)

    response = client.post("/api/settings/mode", json={"mode": "LIVE_EXECUTE"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert "LIVE_EXECUTE" in body["message"]
    assert client.get("/api/settings/mode").json()["mode"] != "LIVE_EXECUTE"


def test_create_app_accepts_hybrid_market_source_mode(tmp_path):
    app = create_app(
        str(tmp_path / "pwb04c_hybrid.sqlite"),
        allow_network=False,
        allow_polymarket_network=False,
        market_source_mode=MarketSourceMode.HYBRID,
    )
    client = TestClient(app)

    health = client.get("/healthz")
    assert health.status_code == 200
    body = health.json()
    assert body["market_source_mode"] == "HYBRID"
    assert body["allow_polymarket_network"] is False

    scan = client.post("/api/opportunities/scan")
    assert scan.status_code == 200
    assert scan.json()["status"] == "ok"
