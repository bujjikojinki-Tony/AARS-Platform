from __future__ import annotations

import httpx

from weather_rules_research.open_meteo.client import OpenMeteoForecastClient

__all__ = ["OpenMeteoForecastClient"]


async def _fetch(
    self: OpenMeteoForecastClient,
    latitude: float,
    longitude: float,
    hourly: str | None = "temperature_2m",
    daily: str | None = None,
) -> dict:
    params = [
        f"latitude={latitude}",
        f"longitude={longitude}",
    ]
    if hourly:
        params.append(f"hourly={hourly}")
    if daily:
        params.append(f"daily={daily}")
    url = f"{self.base_url}/v1/forecast?{'&'.join(params)}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


OpenMeteoForecastClient.fetch = _fetch
