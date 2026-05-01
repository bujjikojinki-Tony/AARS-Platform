from backend.connectors.polymarket_config import PolymarketConnectorConfig
from backend.connectors.polymarket_connector_health import PolymarketConnectorHealthChecker
from backend.connectors.polymarket_read_only_market_source import PolymarketReadOnlyMarketSource
from backend.models.polymarket import MarketSourceMode


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


def test_polymarket_only_returns_empty_when_network_disabled():
    config = PolymarketConnectorConfig(
        market_source_mode=MarketSourceMode.POLYMARKET_ONLY,
        allow_polymarket_network=False,
    )
    source = PolymarketReadOnlyMarketSource(config)

    markets = source.fetch_markets()

    assert markets == []
    assert any("network access disabled" in warning for warning in source.last_warnings)


def test_read_only_market_source_has_no_trading_methods():
    source = PolymarketReadOnlyMarketSource(PolymarketConnectorConfig())
    forbidden_methods = [
        "post_order",
        "create_order",
        "submit_order",
        "place_order",
        "cancel_order",
        "cancel_orders",
        "sign",
        "authenticate",
        "get_positions",
        "get_user_orders",
        "execute_trade",
        "live_execute",
        "auto_trade",
    ]

    for method in forbidden_methods:
        assert not hasattr(source, method)
