from __future__ import annotations

from backend.connectors.polymarket_config import PolymarketConnectorConfig
from backend.models.polymarket import PolymarketMarketRecord


class PolymarketWeatherMarketFilter:
    """
    Filters normalized Polymarket records to weather-like binary markets.
    Conservative v0 rule:
    include only weather-like question/category/slug AND binary YES/NO priced markets.
    """

    def __init__(self, config: PolymarketConnectorConfig | None = None):
        self.config = config or PolymarketConnectorConfig()

    def is_weather_market(self, record: PolymarketMarketRecord) -> bool:
        if not self._passes_status_filter(record):
            return False
        if not self._passes_binary_filter(record):
            return False
        text = " ".join(
            [
                record.question or "",
                record.slug or "",
                record.category or "",
            ]
        ).lower()
        return any(keyword.lower() in text for keyword in self.config.weather_keywords)

    def include(self, record: PolymarketMarketRecord) -> bool:
        return self.is_weather_market(record)

    def filter(self, records: list[PolymarketMarketRecord]) -> list[PolymarketMarketRecord]:
        return [record for record in records if self.is_weather_market(record)]

    def explain_exclusion(self, record: PolymarketMarketRecord) -> list[str]:
        reasons: list[str] = []
        if not record.question:
            reasons.append("missing question")
        if record.active is False:
            reasons.append("market inactive")
        if record.closed is True:
            reasons.append("market closed")
        if record.archived is True:
            reasons.append("market archived")
        if not record.is_binary():
            reasons.append("non-binary or missing prices")
        if record.yes_price() is None:
            reasons.append("missing YES price")
        if record.no_price() is None:
            reasons.append("missing NO price")
        text = " ".join(
            [
                record.question or "",
                record.slug or "",
                record.category or "",
            ]
        ).lower()
        if not any(keyword.lower() in text for keyword in self.config.weather_keywords):
            reasons.append("not weather-like")
        return reasons

    def _passes_status_filter(self, record: PolymarketMarketRecord) -> bool:
        if not record.question:
            return False
        if record.active is False:
            return False
        if record.closed is True:
            return False
        if record.archived is True:
            return False
        return True

    def _passes_binary_filter(self, record: PolymarketMarketRecord) -> bool:
        if not record.is_binary():
            return False
        if record.yes_price() is None:
            return False
        if record.no_price() is None:
            return False
        return True


PolymarketWeatherFilter = PolymarketWeatherMarketFilter
