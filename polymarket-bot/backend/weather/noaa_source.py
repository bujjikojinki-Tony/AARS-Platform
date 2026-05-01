from uuid import uuid4

from backend.models.weather import FreshnessStatus
from backend.models.weather import SourceType
from backend.models.weather import TrustLevel
from backend.models.weather import WeatherMarketDescriptor
from backend.models.weather import WeatherMetric
from backend.models.weather import WeatherSourceRecord
from backend.models.weather import WeatherUnit


class NoaaPlaceholderSource:
    source_name = "noaa_placeholder"
    source_type = SourceType.SHADOW

    def supports(self, descriptor: WeatherMarketDescriptor) -> bool:
        return (
            descriptor.country == "US"
            and descriptor.metric in {
                WeatherMetric.DAILY_HIGH,
                WeatherMetric.DAILY_LOW,
                WeatherMetric.PRECIPITATION,
            }
        )

    def fetch(self, descriptor: WeatherMarketDescriptor) -> WeatherSourceRecord:
        return WeatherSourceRecord(
            source_id=f"src_{uuid4().hex[:10]}",
            market_id=descriptor.market_id,
            source_name=self.source_name,
            source_type=self.source_type,
            city=descriptor.city,
            target_date=descriptor.target_date,
            raw_payload={
                "mock": True,
                "source": "NOAA placeholder",
                "note": "NOAA real connector deferred beyond PWB-02 Phase C",
            },
            normalized_value=self._mock_value(descriptor),
            unit=self._unit_for_metric(descriptor.metric),
            freshness_status=FreshnessStatus.FRESH,
            trust_level=TrustLevel.SHADOW,
        )

    def _mock_value(self, descriptor: WeatherMarketDescriptor) -> float:
        if descriptor.metric == WeatherMetric.DAILY_HIGH:
            return {
                "New York": 30.1,
                "Los Angeles": 27.4,
                "Chicago": 28.0,
            }.get(descriptor.city, 25.0)
        if descriptor.metric == WeatherMetric.DAILY_LOW:
            return {
                "New York": 18.0,
                "Los Angeles": 16.5,
                "Chicago": 15.2,
            }.get(descriptor.city, 15.0)
        if descriptor.metric == WeatherMetric.PRECIPITATION:
            return {
                "New York": 2.5,
                "Los Angeles": 0.2,
                "Chicago": 3.1,
            }.get(descriptor.city, 1.0)
        return 0.0

    def _unit_for_metric(self, metric: WeatherMetric) -> WeatherUnit:
        if metric in {WeatherMetric.DAILY_HIGH, WeatherMetric.DAILY_LOW}:
            return WeatherUnit.C
        if metric == WeatherMetric.PRECIPITATION:
            return WeatherUnit.MM
        return WeatherUnit.UNKNOWN
