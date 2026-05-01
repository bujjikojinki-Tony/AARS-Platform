from fastapi.testclient import TestClient

from backend.app_factory import create_app


def make_client(tmp_path, mode="MOCK_ONLY", allow_polymarket_network=False):
    app = create_app(
        db_path=str(tmp_path / f"pwb04d_{mode}.sqlite"),
        allow_network=False,
        allow_polymarket_network=allow_polymarket_network,
        market_source_mode=mode,
    )
    return TestClient(app)


def test_polymarket_health_api_default_disabled(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/api/polymarket/health")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["health"]["gamma_reachable"] is False
    assert data["health"]["clob_reachable"] is False
    assert data["config"]["allow_polymarket_network"] is False
    assert any("network access disabled" in warning for warning in data["health"]["warnings"])


def test_polymarket_markets_api_returns_cache_list(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/api/polymarket/markets")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["mode"] == "MOCK_ONLY"
    assert isinstance(data["items"], list)


def test_polymarket_weather_markets_api_no_crash_when_network_disabled(tmp_path):
    client = make_client(tmp_path, mode="HYBRID", allow_polymarket_network=False)
    response = client.get("/api/polymarket/weather-markets")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["mode"] == "HYBRID"
    assert data["allow_polymarket_network"] is False
    assert isinstance(data["cached_items"], list)
    assert isinstance(data["preview_snapshots"], list)
    assert isinstance(data["warnings"], list)


def test_sync_weather_markets_mock_only_skips_network(tmp_path):
    client = make_client(tmp_path, mode="MOCK_ONLY", allow_polymarket_network=False)
    response = client.post("/api/polymarket/sync-weather-markets", json={"limit": 10})
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["saved_count"] == 0
    assert any("MOCK_ONLY" in warning for warning in data["warnings"])


def test_source_mode_get_and_set_runtime_only(tmp_path):
    client = make_client(tmp_path, mode="MOCK_ONLY", allow_polymarket_network=False)
    initial = client.get("/api/polymarket/source-mode").json()
    assert initial["market_source_mode"] == "MOCK_ONLY"
    assert initial["allow_polymarket_network"] is False

    response = client.post(
        "/api/polymarket/source-mode",
        json={
            "market_source_mode": "HYBRID",
            "allow_polymarket_network": False,
        },
    )
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["market_source_mode"] == "HYBRID"
    assert data["allow_polymarket_network"] is False
    assert data["live_execution"] is False

    after = client.get("/api/polymarket/source-mode").json()
    assert after["market_source_mode"] == "HYBRID"
    assert after["allow_polymarket_network"] is False


def test_source_mode_rejects_invalid_mode(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/api/polymarket/source-mode",
        json={"market_source_mode": "LIVE_TRADING"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "error"
    assert "unsupported market_source_mode" in data["message"]


def test_hybrid_source_mode_scan_falls_back_to_mock(tmp_path):
    client = make_client(tmp_path, mode="HYBRID", allow_polymarket_network=False)
    scan = client.post("/api/opportunities/scan").json()

    assert scan["status"] == "ok"
    assert scan["candidates_count"] >= 1


def test_polymarket_only_network_disabled_scan_no_crash(tmp_path):
    client = make_client(tmp_path, mode="POLYMARKET_ONLY", allow_polymarket_network=False)
    scan = client.post("/api/opportunities/scan").json()

    assert scan["status"] == "ok"
    assert scan["candidates_count"] == 0


def test_polymarket_api_does_not_enable_live_execute(tmp_path):
    client = make_client(tmp_path, mode="HYBRID", allow_polymarket_network=False)
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
