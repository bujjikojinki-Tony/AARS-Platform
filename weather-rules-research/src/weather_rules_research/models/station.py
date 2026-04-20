from __future__ import annotations

from pydantic import BaseModel


class Station(BaseModel):
    station_name: str
    nws_station_id: str | None = None
    cdo_station_id: str | None = None
    latitude: float
    longitude: float
    timezone: str | None = None
    source: str
