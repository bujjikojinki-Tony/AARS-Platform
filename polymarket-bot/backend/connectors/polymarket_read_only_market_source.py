from __future__ import annotations

from backend.connectors.polymarket_clob_read_client import PolymarketClobReadClient
from backend.connectors.polymarket_config import PolymarketConnectorConfig
from backend.connectors.polymarket_connector_health import PolymarketConnectorHealthChecker
from backend.connectors.polymarket_errors import ReadOnlyConnectorNetworkDisabled
from backend.connectors.polymarket_errors import ReadOnlyConnectorRequestError
from backend.connectors.polymarket_gamma_client import PolymarketGammaClient
from backend.connectors.polymarket_market_normalizer import PolymarketMarketNormalizer
from backend.connectors.polymarket_weather_filter import PolymarketWeatherMarketFilter
from backend.models.core import MarketSnapshot
from backend.models.polymarket import MarketSourceMode
from backend.models.polymarket import PolymarketMarketRecord
from backend.sources.mock_market_source import MockMarketSource


class PolymarketReadOnlyMarketSource:
    """
    PWB-04D read-only market source.
    Modes:
    - MOCK_ONLY: return MockMarketSource markets only.
    - POLYMARKET_ONLY: return Polymarket weather market snapshots; fail safely when unavailable.
    - HYBRID: try Polymarket first, fallback to mock on failure/empty result.
    Safety boundary:
    - no wallet
    - no signing
    - no order/cancel
    - no live execution
    """

    def __init__(
        self,
        config: PolymarketConnectorConfig | None = None,
        mock_source: MockMarketSource | None = None,
    ):
        self.config = config or PolymarketConnectorConfig()
        self.config.validate_safe_defaults()
        self.mock_source = mock_source or MockMarketSource()
        self.gamma_client = PolymarketGammaClient(self.config)
        self.clob_client = PolymarketClobReadClient(self.config)
        self.normalizer = PolymarketMarketNormalizer()
        self.weather_filter = PolymarketWeatherMarketFilter(self.config)
        self.last_warnings: list[str] = []

    def fetch_markets(self, limit: int = 100) -> list[MarketSnapshot]:
        self.last_warnings = []
        mode = self.config.market_source_mode or self.config.mode
        if mode == MarketSourceMode.MOCK_ONLY:
            self.last_warnings.append("MOCK_ONLY mode: using MockMarketSource.")
            return self.mock_source.fetch_markets()
        if mode == MarketSourceMode.POLYMARKET_ONLY:
            return self._fetch_polymarket_snapshots_safe(limit=limit, fallback=False)
        if mode == MarketSourceMode.HYBRID:
            return self._fetch_polymarket_snapshots_safe(limit=limit, fallback=True)
        self.last_warnings.append(
            f"Unsupported market_source_mode={mode}; fallback to mock."
        )
        return self.mock_source.fetch_markets()

    def fetch_polymarket_records(
        self, limit: int | None = None
    ) -> list[PolymarketMarketRecord]:
        raw_markets = self.gamma_client.fetch_markets(
            limit=limit or self.config.max_markets
        )
        records: list[PolymarketMarketRecord] = []
        for raw in raw_markets:
            try:
                records.append(self.normalizer.normalize_market(raw))
            except Exception as exc:
                self.last_warnings.append(f"market normalization failed: {exc}")
        return records

    def fetch_weather_records(
        self, limit: int | None = None
    ) -> list[PolymarketMarketRecord]:
        mode = self.config.market_source_mode or self.config.mode
        if mode == MarketSourceMode.MOCK_ONLY:
            return self.weather_filter.filter(self._mock_records(limit or self.config.max_markets))
        try:
            records = self.fetch_polymarket_records(limit=limit)
            filtered = self.weather_filter.filter(records)
            if filtered:
                return filtered
            if mode == MarketSourceMode.HYBRID:
                self.last_warnings.append("HYBRID fallback: using MockMarketSource.")
                return self.weather_filter.filter(self._mock_records(limit or self.config.max_markets))
            return filtered
        except (ReadOnlyConnectorNetworkDisabled, ReadOnlyConnectorRequestError) as exc:
            self.last_warnings.append(str(exc))
            if mode == MarketSourceMode.HYBRID:
                self.last_warnings.append("HYBRID fallback: using MockMarketSource.")
                return self.weather_filter.filter(self._mock_records(limit or self.config.max_markets))
            return []

    def fetch_weather_markets(self, limit: int = 100) -> list[PolymarketMarketRecord]:
        return self.fetch_weather_records(limit=limit)

    def health(self):
        return PolymarketConnectorHealthChecker(self.config).check()

    def _fetch_polymarket_snapshots_safe(
        self,
        *,
        limit: int,
        fallback: bool,
    ) -> list[MarketSnapshot]:
        mode = self.config.market_source_mode or self.config.mode
        if not self.config.allow_polymarket_network:
            self.last_warnings.append("Polymarket network access disabled by config.")
            if fallback and mode == MarketSourceMode.HYBRID:
                self.last_warnings.append("HYBRID fallback: using MockMarketSource.")
                return self.mock_source.fetch_markets()
            if mode == MarketSourceMode.POLYMARKET_ONLY:
                self.last_warnings.append("POLYMARKET_ONLY requires network access.")
                return []
            return self.mock_source.fetch_markets()
        try:
            weather_records = self.fetch_weather_records(limit=limit)
            snapshots = []
            for record in weather_records:
                try:
                    snapshots.append(record.to_market_snapshot())
                except Exception as exc:
                    self.last_warnings.append(
                        f"market snapshot conversion failed for {record.polymarket_market_id}: {exc}"
                    )
            if snapshots:
                return snapshots
            self.last_warnings.append("No Polymarket weather markets available.")
            if fallback:
                self.last_warnings.append("HYBRID fallback: using MockMarketSource.")
                return self.mock_source.fetch_markets()
            return []
        except ReadOnlyConnectorNetworkDisabled as exc:
            self.last_warnings.append(str(exc))
            if fallback:
                self.last_warnings.append("HYBRID fallback: using MockMarketSource.")
                return self.mock_source.fetch_markets()
            return []
        except ReadOnlyConnectorRequestError as exc:
            self.last_warnings.append(str(exc))
            if fallback:
                self.last_warnings.append("HYBRID fallback: using MockMarketSource.")
                return self.mock_source.fetch_markets()
            return []
        except Exception as exc:
            self.last_warnings.append(f"Polymarket read-only source failed: {exc}")
            if fallback:
                self.last_warnings.append("HYBRID fallback: using MockMarketSource.")
                return self.mock_source.fetch_markets()
            return []

    def _mock_records(self, limit: int) -> list[PolymarketMarketRecord]:
        records: list[PolymarketMarketRecord] = []
        for market in self.mock_source.fetch_markets()[:limit]:
            records.append(
                self.normalizer.normalize_market(
                    {
                        "id": market.market_id,
                        "conditionId": market.market_id,
                        "question": market.question,
                        "slug": market.market_id,
                        "category": "Weather" if "weather" in market.question.lower() else "General",
                        "active": True,
                        "closed": False,
                        "archived": False,
                        "outcomes": ["Yes", "No"],
                        "outcomePrices": [market.yes_price, market.no_price],
                        "liquidity": market.liquidity,
                        "source": "mock",
                    }
                )
            )
        return records
