from __future__ import annotations

from datetime import datetime, timezone

from weather_rules_research.open_meteo.extractors import OpenMeteoExtractor
from weather_rules_research.open_meteo.forecast_client import OpenMeteoForecastClient


class ForecastPoller:
    def __init__(self, latitude: float, longitude: float, target_date: str, variable_name: str) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.target_date = target_date
        self.variable_name = variable_name
        self.client = OpenMeteoForecastClient()
        self.extractor = OpenMeteoExtractor()
        self.latest = None

    async def poll_once(self) -> dict:
        payload = await self.client.fetch(
            latitude=self.latitude,
            longitude=self.longitude,
            hourly="temperature_2m",
        )
        extracted = self.extractor.extract_for_market_rule(
            payload=payload,
            target_date=self.target_date,
            variable_name=self.variable_name,
        )

        self.latest = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_date": self.target_date,
            "variable_name": self.variable_name,
            "value": extracted.value,
            "source_mode": extracted.source_mode,
        }
        return self.latest
