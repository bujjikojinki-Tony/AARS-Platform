from fastapi.testclient import TestClient

from backend.app_factory import create_app


def test_create_app_default_market_source_mode_mock_only(tmp_path):
    app = create_app(
        db_path=str(tmp_path / "default.sqlite"),
        allow_network=False,
        allow_polymarket_network=False,
        market_source_mode="MOCK_ONLY",
    )
    client = TestClient(app)

    health = client.get("/healthz").json()
    assert health["status"] == "ok"
    assert health["allow_polymarket_network"] is False
    assert health["market_source_mode"] == "MOCK_ONLY"
    assert health["live_execution"] is False


def test_scan_with_mock_only_still_works(tmp_path):
    app = create_app(
        db_path=str(tmp_path / "mock_only.sqlite"),
        allow_network=False,
        allow_polymarket_network=False,
        market_source_mode="MOCK_ONLY",
    )
    client = TestClient(app)

    response = client.post("/api/opportunities/scan")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["candidates_count"] >= 1


def test_hybrid_mode_falls_back_to_mock_when_network_disabled(tmp_path):
    app = create_app(
        db_path=str(tmp_path / "hybrid.sqlite"),
        allow_network=False,
        allow_polymarket_network=False,
        market_source_mode="HYBRID",
    )
    client = TestClient(app)

    health = client.get("/healthz").json()
    assert health["market_source_mode"] == "HYBRID"
    assert health["allow_polymarket_network"] is False

    response = client.post("/api/opportunities/scan")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["candidates_count"] >= 1


def test_polymarket_only_network_disabled_returns_no_candidates_without_crash(tmp_path):
    app = create_app(
        db_path=str(tmp_path / "pm_only.sqlite"),
        allow_network=False,
        allow_polymarket_network=False,
        market_source_mode="POLYMARKET_ONLY",
    )
    client = TestClient(app)

    health = client.get("/healthz").json()
    assert health["market_source_mode"] == "POLYMARKET_ONLY"
    assert health["allow_polymarket_network"] is False

    response = client.post("/api/opportunities/scan")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["candidates_count"] == 0


def test_live_execute_still_rejected_with_polymarket_fields(tmp_path):
    app = create_app(
        db_path=str(tmp_path / "safe.sqlite"),
        allow_network=False,
        allow_polymarket_network=False,
        market_source_mode="HYBRID",
    )
    client = TestClient(app)

    response = client.post(
        "/api/settings/mode",
        json={"mode": "LIVE_EXECUTE"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "error"
    assert "LIVE_EXECUTE" in data["message"]
    mode = client.get("/api/settings/mode").json()
    assert mode["mode"] != "LIVE_EXECUTE"
