from __future__ import annotations

import json
import urllib.parse
import urllib.request
from uuid import uuid4

from backend.models.weather import FreshnessStatus
from backend.models.weather import SourceType
from backend.models.weather import TrustLevel
from backend.models.weather import WeatherMarketDescriptor
from backend.models.weather import WeatherMetric
from backend.models.weather import WeatherSourceRecord
from backend.models.weather import WeatherUnit


CITY_COORDS = {
    "Tokyo": (35.6762, 139.6503),
    "Osaka": (34.6937, 135.5023),
    "Kyoto": (35.0116, 135.7681),
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298),
    "London": (51.5072, -0.1276),
    "Paris": (48.8566, 2.3522),
    "Seoul": (37.5665, 126.9780),
    "Hong Kong": (22.3193, 114.1694),
    "Taipei": (25.0330, 121.5654),
    "Singapore": (1.3521, 103.8198),
}


class OpenMeteoSource:
    source_name = "open_meteo"
    source_type = SourceType.FORECAST

    def __init__(self, timeout_seconds: int = 8, allow_network: bool = True):
        self.timeout_seconds = timeout_seconds
        self.allow_network = allow_network

    def supports(self, descriptor: WeatherMarketDescriptor) -> bool:
        return (
            descriptor.city in CITY_COORDS
            and descriptor.target_date != "UNKNOWN"
            and descriptor.metric in {
                WeatherMetric.DAILY_HIGH,
                WeatherMetric.DAILY_LOW,
                WeatherMetric.PRECIPITATION,
            }
        )

    def fetch(self, descriptor: WeatherMarketDescriptor) -> WeatherSourceRecord:
        if not self.allow_network:
            return self._mock_record(descriptor, reason="network disabled")
        try:
            return self._fetch_real(descriptor)
        except Exception as exc:
            return self._mock_record(descriptor, reason=f"open-meteo fallback: {exc}")

    def _fetch_real(self, descriptor: WeatherMarketDescriptor) -> WeatherSourceRecord:
        lat, lon = CITY_COORDS[descriptor.city]
        daily_param = self._daily_param(descriptor.metric)
        query = urllib.parse.urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "daily": daily_param,
                "timezone": "auto",
                "start_date": descriptor.target_date,
                "end_date": descriptor.target_date,
            }
        )
        url = f"https://api.open-meteo.com/v1/forecast?{query}"
        with urllib.request.urlopen(url, timeout=self.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        value = self._extract_value(payload, daily_param)
        return WeatherSourceRecord(
            source_id=f"src_{uuid4().hex[:10]}",
            market_id=descriptor.market_id,
            source_name=self.source_name,
            source_type=self.source_type,
            city=descriptor.city,
            target_date=descriptor.target_date,
            raw_payload=payload,
            normalized_value=value,
            unit=self._unit_for_metric(descriptor.metric),
            freshness_status=FreshnessStatus.FRESH,
            trust_level=TrustLevel.PRIMARY,
        )

    def _mock_record(self, descriptor: WeatherMarketDescriptor, reason: str) -> WeatherSourceRecord:
        mock_value = self._mock_value(descriptor)
        return WeatherSourceRecord(
            source_id=f"src_{uuid4().hex[:10]}",
            market_id=descriptor.market_id,
            source_name="open_meteo_mock",
            source_type=self.source_type,
            city=descriptor.city,
            target_date=descriptor.target_date,
            raw_payload={
                "mock": True,
                "reason": reason,
                "city": descriptor.city,
                "target_date": descriptor.target_date,
                "metric": descriptor.metric.value,
                "value": mock_value,
            },
            normalized_value=mock_value,
            unit=self._unit_for_metric(descriptor.metric),
            freshness_status=FreshnessStatus.FRESH,
            trust_level=TrustLevel.PRIMARY,
        )

    def _daily_param(self, metric: WeatherMetric) -> str:
        if metric == WeatherMetric.DAILY_HIGH:
            return "temperature_2m_max"
        if metric == WeatherMetric.DAILY_LOW:
            return "temperature_2m_min"
        if metric == WeatherMetric.PRECIPITATION:
            return "precipitation_sum"
        return "temperature_2m_max"

    def _unit_for_metric(self, metric: WeatherMetric) -> WeatherUnit:
        if metric in {WeatherMetric.DAILY_HIGH, WeatherMetric.DAILY_LOW}:
            return WeatherUnit.C
        if metric == WeatherMetric.PRECIPITATION:
            return WeatherUnit.MM
        return WeatherUnit.UNKNOWN

    def _extract_value(self, payload: dict, daily_param: str) -> float:
        values = payload.get("daily", {}).get(daily_param, [])
        if not values:
            raise ValueError(f"missing daily value for {daily_param}")
        return float(values[0])

    def _mock_value(self, descriptor: WeatherMarketDescriptor) -> float:
        if descriptor.metric == WeatherMetric.DAILY_HIGH:
            return {
                "Tokyo": 31.2,
                "Osaka": 29.4,
                "Kyoto": 30.1,
                "New York": 30.8,
                "London": 22.3,
            }.get(descriptor.city, 25.0)
        if descriptor.metric == WeatherMetric.DAILY_LOW:
            return {
                "Tokyo": 21.5,
                "Osaka": 20.9,
                "New York": 18.4,
                "London": 12.8,
            }.get(descriptor.city, 15.0)
        if descriptor.metric == WeatherMetric.PRECIPITATION:
            return {
                "Tokyo": 4.2,
                "London": 6.1,
                "New York": 2.0,
            }.get(descriptor.city, 1.0)
        return 0.0
