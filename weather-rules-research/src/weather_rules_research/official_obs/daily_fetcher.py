from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from weather_rules_research.settings import RAW_DIR


class DailySettlementFetcher:
    """
    Fetch daily settlement-grade values for a station and date.

    MVP strategy:
    - implement a structured interface for NCEI/CDO-style daily retrieval
    - return normalized payloads that can be reconciled into SettlementRecord
    """

    def __init__(
        self,
        cdo_base_url: str = "https://www.ncei.noaa.gov/cdo-web/api/v2",
        raw_dir: Path | None = None,
        token: str | None = None,
        user_agent: str = "weather-rules-research/0.1",
    ) -> None:
        self.cdo_base_url = cdo_base_url.rstrip("/")
        self.raw_dir = raw_dir or (RAW_DIR / "official_station_obs")
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.token = token
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/json",
        }
        if token:
            self.headers["token"] = token

    async def fetch_daily_value(
        self,
        station_id: str,
        target_date: str,
        variable_name: str,
    ) -> dict[str, Any]:
        """
        Generic daily settlement-grade fetch for supported station variables.
        """
        variable_spec = self._variable_spec(variable_name)
        datatype = variable_spec["datatype"]

        url = f"{self.cdo_base_url}/data"
        params = {
            "datasetid": "GHCND",
            "stationid": self._normalize_station_id_for_cdo(station_id),
            "startdate": target_date,
            "enddate": target_date,
            "datatypeid": datatype,
            "limit": 1000,
            "units": "metric",
        }

        async with httpx.AsyncClient(timeout=30, headers=self.headers) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            payload = resp.json()

        raw_ref = self._write_raw_payload(
            filename=f"daily_{station_id}_{target_date}_{datatype}.json",
            payload=payload,
        )

        result_value = self._extract_cdo_value(payload)

        return {
            "station_id": station_id,
            "target_date": target_date,
            "variable_name": variable_name,
            "official_value": result_value,
            "unit": variable_spec["unit"],
            "source": "ncei_cdo_daily",
            "source_url": str(resp.url),
            "raw_payload_ref": str(raw_ref),
            "quality_flag": None,
            "notes": (
                "Daily settlement-grade candidate from NCEI/CDO-style GHCND query. "
                "Review station-id normalization and rule-specific source match."
            ),
        }

    async def fetch_daily_temperature(
        self,
        station_id: str,
        target_date: str,
        variable_name: str,
    ) -> dict[str, Any]:
        return await self.fetch_daily_value(
            station_id=station_id,
            target_date=target_date,
            variable_name=variable_name,
        )

    @staticmethod
    def _map_variable_to_datatype(variable_name: str) -> str:
        return DailySettlementFetcher._variable_spec(variable_name)["datatype"]

    @staticmethod
    def _variable_spec(variable_name: str) -> dict[str, str]:
        mapping = {
            "daily_max_temperature": {"datatype": "TMAX", "unit": "celsius"},
            "daily_min_temperature": {"datatype": "TMIN", "unit": "celsius"},
            "daily_precipitation_sum": {"datatype": "PRCP", "unit": "mm"},
        }
        if variable_name not in mapping:
            raise ValueError(f"Unsupported variable_name: {variable_name}")
        return mapping[variable_name]

    @staticmethod
    def _normalize_station_id_for_cdo(station_id: str) -> str:
        """
        Many CDO station IDs are prefixed, e.g. GHCND:USW00094728.
        For MVP, allow pre-prefixed IDs to pass through and otherwise
        use the provided station_id directly.
        """
        if ":" in station_id:
            return station_id
        return station_id

    @staticmethod
    def _extract_cdo_value(payload: dict[str, Any]) -> float | None:
        """
        CDO responses often return a list of result items with `value`.
        """
        results = payload.get("results", [])
        if not results:
            return None

        first = results[0]
        value = first.get("value")
        if value is None:
            return None

        return float(value)

    def _write_raw_payload(self, filename: str, payload: dict[str, Any]) -> Path:
        path = self.raw_dir / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
