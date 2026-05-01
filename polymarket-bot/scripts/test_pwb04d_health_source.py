from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.connectors.polymarket_config import PolymarketConnectorConfig
from backend.connectors.polymarket_connector_health import PolymarketConnectorHealthChecker
from backend.connectors.polymarket_read_only_market_source import PolymarketReadOnlyMarketSource
from backend.models.polymarket import MarketSourceMode


def print_result(title, value):
    print("\n---")
    print(title)
    print(value)


default_config = PolymarketConnectorConfig()
health = PolymarketConnectorHealthChecker(default_config).check()
print_result("Default health", health.model_dump())
assert health.gamma_reachable is False
assert health.clob_reachable is False
assert any("network access disabled" in warning for warning in health.warnings)

mock_config = PolymarketConnectorConfig(
    market_source_mode=MarketSourceMode.MOCK_ONLY,
    allow_polymarket_network=False,
)
mock_source = PolymarketReadOnlyMarketSource(mock_config)
mock_markets = mock_source.fetch_markets()
print_result("MOCK_ONLY markets", [market.model_dump() for market in mock_markets])
print_result("MOCK_ONLY warnings", mock_source.last_warnings)
assert len(mock_markets) > 0
assert all(market.source == "mock" for market in mock_markets)

hybrid_config = PolymarketConnectorConfig(
    market_source_mode=MarketSourceMode.HYBRID,
    allow_polymarket_network=False,
)
hybrid_source = PolymarketReadOnlyMarketSource(hybrid_config)
hybrid_markets = hybrid_source.fetch_markets()
print_result("HYBRID markets", [market.model_dump() for market in hybrid_markets])
print_result("HYBRID warnings", hybrid_source.last_warnings)
assert len(hybrid_markets) > 0
assert all(market.source == "mock" for market in hybrid_markets)
assert any("HYBRID fallback" in warning for warning in hybrid_source.last_warnings)

pm_only_config = PolymarketConnectorConfig(
    market_source_mode=MarketSourceMode.POLYMARKET_ONLY,
    allow_polymarket_network=False,
)
pm_only_source = PolymarketReadOnlyMarketSource(pm_only_config)
pm_only_markets = pm_only_source.fetch_markets()
print_result("POLYMARKET_ONLY markets", [market.model_dump() for market in pm_only_markets])
print_result("POLYMARKET_ONLY warnings", pm_only_source.last_warnings)
assert pm_only_markets == []
assert any("network access disabled" in warning for warning in pm_only_source.last_warnings)

print("\nPWB-04D Phase D health/source smoke test passed.")
