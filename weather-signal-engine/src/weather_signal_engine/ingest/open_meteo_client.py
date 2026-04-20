import httpx


class OpenMeteoClient:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    async def fetch(self, latitude: float, longitude: float, hourly: str = "temperature_2m") -> dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": hourly,
            "forecast_days": 7,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            return resp.json()
