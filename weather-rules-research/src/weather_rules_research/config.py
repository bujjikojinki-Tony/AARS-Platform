from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    open_meteo_base_url: str = "https://api.open-meteo.com"
    noaa_base_url: str = "https://www.ncei.noaa.gov"
    nws_base_url: str = "https://api.weather.gov"


def get_settings() -> Settings:
    return Settings(
        open_meteo_base_url=os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com"),
        noaa_base_url=os.getenv("NOAA_BASE_URL", "https://www.ncei.noaa.gov"),
        nws_base_url=os.getenv("NWS_BASE_URL", "https://api.weather.gov"),
    )
