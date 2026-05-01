from __future__ import annotations

import inspect

import pytest
from fastapi.testclient import TestClient

from backend.app_factory import create_app
from backend.connectors.polymarket_clob_read_client import PolymarketClobReadClient
from backend.connectors.polymarket_config import PolymarketConnectorConfig
from backend.connectors.polymarket_connector_health import PolymarketConnectorHealthChecker
from backend.connectors.polymarket_errors import ReadOnlyConnectorNetworkDisabled
from backend.connectors.polymarket_gamma_client import PolymarketGammaClient
from backend.connectors.polymarket_market_normalizer import PolymarketMarketNormalizer
from backend.connectors.polymarket_read_only_market_source import PolymarketReadOnlyMarketSource
from backend.connectors.polymarket_weather_filter import PolymarketWeatherMarketFilter
from backend.models.polymarket import MarketSourceMode
from backend.storage.db import init_db
from backend.storage.repositories import Repository

FORBIDDEN_METHODS = [
    "post_order",
    "create_order",
    "submit_order",
    "place_order",
    "send_order",
    "cancel_order",
    "cancel_orders",
    "cancel_all",
    "replace_order",
    "amend_order",
    "market_order",
    "limit_order",
    "sign",
    "authenticate",
    "get_positions",
    "get_user_orders",
    "execute_trade",
    "live_execute",
    "auto_trade",
]

FORBIDDEN_CONFIG_FIELDS = [
    "private_key",
    "wallet",
    "signature",
    "api_key",
    "api_secret",
    "passphrase",
    "funder",
    "allowance",
    "creds",
    "signer",
]


@pytest.fixture
def raw_weather_market():
    return {
        "id": "pm_weather_1",
        "conditionId": "cond_weather_1",
        "question": "Will Tokyo high temperature exceed 30C on June 1?",
        "slug": "tokyo-high-temperature-june-1",
        "category": "weather",
        "active": True,
        "closed": False,
        "archived": False,
        "outcomes": '["Yes", "No"]',
        "outcomePrices": '["0.52", "0.49"]',
        "clobTokenIds": '["token_yes", "token_no"]',
        "liquidity": "1000",
        "volume": "5000",
    }


@pytest.fixture
def raw_non_weather_market():
    return {
        "id": "pm_election_1",
        "conditionId": "cond_election_1",
        "question": "Will candidate X win the election?",
        "slug": "candidate-x-election",
        "category": "politics",
        "active": True,
        "closed": False,
        "archived": False,
        "outcomes": ["Yes", "No"],
        "outcomePrices": [0.55, 0.46],
        "liquidity": 2000,
    }


def make_client(tmp_path, mode="MOCK_ONLY", allow_polymarket_network=False):
    app = create_app(
        db_path=str(tmp_path / f"pwb04d_{mode}.sqlite"),
        allow_network=False,
        allow_polymarket_network=allow_polymarket_network,
        market_source_mode=mode,
    )
    return TestClient(app)


def test_connector_default_network_disabled():
    config = PolymarketConnectorConfig()

    assert config.market_source_mode == MarketSourceMode.MOCK_ONLY
    assert config.allow_polymarket_network is False
    assert config.request_timeout_seconds <= 10

    dumped = config.model_dump_safe()
    annotations = set(PolymarketConnectorConfig.__annotations__.keys())
    for field in FORBIDDEN_CONFIG_FIELDS:
        assert field not in dumped
        assert field not in annotations


def test_gamma_client_refuses_network_when_disabled():
    config = PolymarketConnectorConfig()
    client = PolymarketGammaClient(config)

    with pytest.raises(ReadOnlyConnectorNetworkDisabled):
        client.fetch_markets()


def test_clob_client_refuses_network_when_disabled():
    config = PolymarketConnectorConfig()
    client = PolymarketClobReadClient(config)

    with pytest.raises(ReadOnlyConnectorNetworkDisabled):
        client.get_midpoint("fake_token_id")


def test_gamma_client_exposes_only_read_methods():
    client = PolymarketGammaClient(PolymarketConnectorConfig())
    allowed = {
        "fetch_markets",
        "fetch_events",
        "public_search",
        "fetch_tags",
    }

    for method in allowed:
        assert hasattr(client, method)
    for method in FORBIDDEN_METHODS:
        assert not hasattr(client, method)


def test_clob_client_exposes_only_read_methods():
    client = PolymarketClobReadClient(PolymarketConnectorConfig())
    allowed = {
        "get_price",
        "get_midpoint",
        "get_spread",
        "get_book",
        "get_prices_history",
    }

    for method in allowed:
        assert hasattr(client, method)
    for method in FORBIDDEN_METHODS:
        assert not hasattr(client, method)


def test_no_trading_methods_exist_on_connector_classes():
    classes = [
        PolymarketGammaClient,
        PolymarketClobReadClient,
        PolymarketReadOnlyMarketSource,
    ]

    for cls in classes:
        members = {name for name, _ in inspect.getmembers(cls)}
        for method in FORBIDDEN_METHODS:
            assert method not in members, f"{cls.__name__} must not expose {method}"


def test_no_forbidden_config_fields_exist():
    annotations = set(PolymarketConnectorConfig.__annotations__.keys())
    for field in FORBIDDEN_CONFIG_FIELDS:
        assert field not in annotations


def test_normalizer_maps_gamma_market_to_record(raw_weather_market):
    record = PolymarketMarketNormalizer().normalize_market(raw_weather_market)

    assert record.polymarket_market_id == "pm_weather_1"
    assert record.condition_id == "cond_weather_1"
    assert record.question == raw_weather_market["question"]
    assert record.outcomes == ["Yes", "No"]
    assert record.outcome_prices == [0.52, 0.49]
    assert record.clob_token_ids == ["token_yes", "token_no"]
    assert record.liquidity == 1000
    assert record.volume == 5000
    assert record.is_binary() is True
    assert record.yes_price() == 0.52
    assert record.no_price() == 0.49


def test_normalizer_outputs_market_snapshot(raw_weather_market):
    record = PolymarketMarketNormalizer().normalize_market(raw_weather_market)
    snapshot = record.to_market_snapshot()

    assert snapshot.market_id == "cond_weather_1"
    assert snapshot.question == raw_weather_market["question"]
    assert snapshot.yes_price == 0.52
    assert snapshot.no_price == 0.49
    assert snapshot.liquidity == 1000
    assert snapshot.source == "polymarket"


def test_weather_filter_includes_weather_market(raw_weather_market):
    record = PolymarketMarketNormalizer().normalize_market(raw_weather_market)
    assert PolymarketWeatherMarketFilter().is_weather_market(record) is True


def test_weather_filter_excludes_non_weather_market(raw_non_weather_market):
    record = PolymarketMarketNormalizer().normalize_market(raw_non_weather_market)
    filter_ = PolymarketWeatherMarketFilter()

    assert filter_.is_weather_market(record) is False
    assert "not weather-like" in filter_.explain_exclusion(record)


def test_weather_filter_excludes_closed_market(raw_weather_market):
    raw = dict(raw_weather_market)
    raw["closed"] = True
    record = PolymarketMarketNormalizer().normalize_market(raw)
    filter_ = PolymarketWeatherMarketFilter()

    assert filter_.is_weather_market(record) is False
    assert "market closed" in filter_.explain_exclusion(record)


def test_weather_filter_excludes_non_binary_market(raw_weather_market):
    raw = dict(raw_weather_market)
    raw["outcomes"] = ["Below 25", "25-30", "Above 30"]
    raw["outcomePrices"] = [0.2, 0.5, 0.3]
    record = PolymarketMarketNormalizer().normalize_market(raw)
    filter_ = PolymarketWeatherMarketFilter()

    assert filter_.is_weather_market(record) is False
    assert "non-binary or missing prices" in filter_.explain_exclusion(record)


def test_connector_health_default_network_disabled():
    config = PolymarketConnectorConfig()
    health = PolymarketConnectorHealthChecker(config).check()

    assert health.connector_id == "polymarket_read_only_v0"
    assert health.gamma_reachable is False
    assert health.clob_reachable is False
    assert health.mode == MarketSourceMode.MOCK_ONLY
    assert any("network access disabled" in warning for warning in health.warnings)


def test_read_only_market_source_mock_only_outputs_mock():
    config = PolymarketConnectorConfig(
        market_source_mode=MarketSourceMode.MOCK_ONLY,
        allow_polymarket_network=False,
    )
    source = PolymarketReadOnlyMarketSource(config)
    markets = source.fetch_markets()

    assert len(markets) > 0
    assert all(market.source == "mock" for market in markets)
    assert any("MOCK_ONLY" in warning for warning in source.last_warnings)


def test_hybrid_mode_falls_back_to_mock_when_network_disabled():
    config = PolymarketConnectorConfig(
        market_source_mode=MarketSourceMode.HYBRID,
        allow_polymarket_network=False,
    )
    source = PolymarketReadOnlyMarketSource(config)
    markets = source.fetch_markets()

    assert len(markets) > 0
    assert all(market.source == "mock" for market in markets)
    assert any("network access disabled" in warning for warning in source.last_warnings)
    assert any("HYBRID fallback" in warning for warning in source.last_warnings)


def test_polymarket_only_network_disabled_returns_empty_without_crash():
    config = PolymarketConnectorConfig(
        market_source_mode=MarketSourceMode.POLYMARKET_ONLY,
        allow_polymarket_network=False,
    )
    source = PolymarketReadOnlyMarketSource(config)
    markets = source.fetch_markets()

    assert markets == []
    assert any("network access disabled" in warning for warning in source.last_warnings)


def test_polymarket_market_cache_repository(tmp_path, raw_weather_market):
    db_path = str(tmp_path / "pwb04d_cache.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    record = PolymarketMarketNormalizer().normalize_market(raw_weather_market)
    repo.save_polymarket_market_record(record)
    rows = repo.list_polymarket_market_cache()

    assert len(rows) == 1
    assert rows[0]["polymarket_market_id"] == "pm_weather_1"
    assert rows[0]["condition_id"] == "cond_weather_1"
    assert rows[0]["outcomes"] == ["Yes", "No"]
    assert rows[0]["outcome_prices"] == [0.52, 0.49]
    assert rows[0]["clob_token_ids"] == ["token_yes", "token_no"]


def test_polymarket_weather_market_cache_repository(
    tmp_path,
    raw_weather_market,
    raw_non_weather_market,
):
    db_path = str(tmp_path / "pwb04d_weather_cache.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    normalizer = PolymarketMarketNormalizer()
    repo.save_polymarket_market_record(normalizer.normalize_market(raw_weather_market))
    repo.save_polymarket_market_record(normalizer.normalize_market(raw_non_weather_market))
    rows = repo.list_polymarket_weather_market_cache()

    assert len(rows) == 1
    assert rows[0]["polymarket_market_id"] == "pm_weather_1"


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


def test_polymarket_weather_markets_api_no_crash(tmp_path):
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


def test_healthz_includes_polymarket_source_fields(tmp_path):
    client = make_client(tmp_path, mode="HYBRID", allow_polymarket_network=False)
    data = client.get("/healthz").json()

    assert data["status"] == "ok"
    assert data["market_source_mode"] == "HYBRID"
    assert data["allow_polymarket_network"] is False
    assert data["live_execution"] is False
    assert "PWB-04D" in data["rounds"]


def test_sync_weather_markets_does_not_create_candidates(tmp_path):
    client = make_client(tmp_path, mode="MOCK_ONLY", allow_polymarket_network=False)
    before = client.get("/api/history/candidates").json()
    sync = client.post("/api/polymarket/sync-weather-markets", json={"limit": 10}).json()
    after = client.get("/api/history/candidates").json()

    assert sync["status"] == "ok"
    assert sync["saved_count"] == 0
    assert len(before) == len(after)


def test_source_mode_does_not_change_execution_mode(tmp_path):
    client = make_client(tmp_path, mode="MOCK_ONLY", allow_polymarket_network=False)
    before = client.get("/api/settings/mode").json()
    response = client.post(
        "/api/polymarket/source-mode",
        json={
            "market_source_mode": "HYBRID",
            "allow_polymarket_network": False,
        },
    ).json()
    after = client.get("/api/settings/mode").json()

    assert response["status"] == "ok"
    assert before["mode"] == after["mode"]
    assert after["mode"] != "LIVE_EXECUTE"
