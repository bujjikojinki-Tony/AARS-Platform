from __future__ import annotations

from datetime import date

from weather_rules_research.config import get_settings
from weather_rules_research.models import MarketRule, SettlementRecord, Station


class OfficialObservationFetcher:
    """Observation wrapper for the research MVP."""

    def __init__(self, noaa_base_url: str | None = None, nws_base_url: str | None = None) -> None:
        settings = get_settings()
        self.noaa_base_url = noaa_base_url or settings.noaa_base_url
        self.nws_base_url = nws_base_url or settings.nws_base_url

    def build_daily_summaries_url(self, station_id: str) -> str:
        return (
            f"{self.noaa_base_url}/access/services/data/v1"
            f"?dataset=daily-summaries&stations={station_id}"
        )

    def build_station_points_url(self, latitude: float, longitude: float) -> str:
        return f"{self.nws_base_url}/points/{latitude},{longitude}"

    def fetch_settlement_stub(
        self,
        rule: MarketRule,
        station: Station,
        settlement_date: date,
        settled_temperature_c: float,
    ) -> SettlementRecord:
        return SettlementRecord(
            station_id=station.nws_station_id or station.cdo_station_id or station.station_name,
            target_date=settlement_date.isoformat(),
            variable_name=rule.variable_name,
            official_value=settled_temperature_c,
            unit="C",
            source="official_obs",
            source_url=self.build_daily_summaries_url(
                station.nws_station_id or station.cdo_station_id or station.station_name
            ),
            raw_payload_ref=(
                f"official-obs://sample/"
                f"{station.nws_station_id or station.cdo_station_id or station.station_name}/"
                f"{settlement_date.isoformat()}"
            ),
        )
