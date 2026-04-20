from __future__ import annotations

from datetime import date

from weather_rules_research.config import get_settings
from weather_rules_research.models import ForecastSnapshot, MarketRule, Station


class OpenMeteoForecastClient:
    """Research-friendly client wrapper.

    Network fetching is intentionally deferred; the MVP returns deterministic
    sample records so the downstream pipeline can be exercised offline.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or get_settings().open_meteo_base_url

    def build_forecast_url(self, station: Station) -> str:
        if station.latitude is None or station.longitude is None:
            raise ValueError("Station latitude/longitude are required to build an Open-Meteo URL.")
        return (
            f"{self.base_url}/v1/forecast"
            f"?latitude={station.latitude}&longitude={station.longitude}&daily=temperature_2m_max"
        )

    def fetch_forecast_stub(
        self,
        rule: MarketRule,
        station: Station,
        settlement_date: date,
        predicted_temperature_c: float,
        issued_at: str,
    ) -> ForecastSnapshot:
        return ForecastSnapshot(
            market_id=rule.market_id,
            station_id=station.nws_station_id or station.cdo_station_id or station.station_name,
            market_type=rule.market_type,
            target_date=settlement_date,
            issued_at=issued_at,
            predicted_temperature_c=predicted_temperature_c,
            raw_payload_ref=f"open-meteo://sample/{rule.market_id}/{settlement_date.isoformat()}",
        )
