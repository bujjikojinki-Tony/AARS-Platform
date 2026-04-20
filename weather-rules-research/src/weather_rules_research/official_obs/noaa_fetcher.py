from __future__ import annotations

from pathlib import Path
from typing import Any

from weather_rules_research.official_obs.daily_fetcher import DailySettlementFetcher
from weather_rules_research.official_obs.client import OfficialObservationFetcher
from weather_rules_research.settings import RAW_DIR


class NOAAFetcher:
    """
    High-level facade for official observation retrieval.

    Strategy:
    1. Prefer daily settlement-grade values.
    2. Fall back to recent observation only when daily value is unavailable.
    """

    def __init__(
        self,
        nws_base_url: str = "https://api.weather.gov",
        cdo_base_url: str = "https://www.ncei.noaa.gov/cdo-web/api/v2",
        raw_dir: Path | None = None,
        cdo_token: str | None = None,
        user_agent: str = "weather-rules-research/0.1",
    ) -> None:
        self.nws_base_url = nws_base_url.rstrip("/")
        self.raw_dir = raw_dir or (RAW_DIR / "official_station_obs")
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent
        self.daily_fetcher = DailySettlementFetcher(
            cdo_base_url=cdo_base_url,
            raw_dir=self.raw_dir,
            token=cdo_token,
            user_agent=user_agent,
        )
        self.recent_fetcher = OfficialObservationFetcher(
            nws_base_url=nws_base_url,
            noaa_base_url=cdo_base_url,
        )

    async def fetch_daily_settlement_value(
        self,
        station_id: str,
        target_date: str,
        variable_name: str,
    ) -> dict[str, Any]:
        return await self.daily_fetcher.fetch_daily_temperature(
            station_id=station_id,
            target_date=target_date,
            variable_name=variable_name,
        )

    async def fetch_recent_observation_nws(self, station_id: str) -> dict[str, Any]:
        return await self.recent_fetcher.fetch_recent_observation_nws(station_id)
