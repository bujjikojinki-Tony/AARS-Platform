from __future__ import annotations

from datetime import datetime, timezone

from weather_rules_research.governance import normalize_measurement
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
        normalized = normalize_measurement(
            {"value": extracted.value, "unit": _raw_unit_for_variable_name(self.variable_name)},
            family=_family_for_variable_name(self.variable_name),
            variable_name=self.variable_name,
            raw_unit=_raw_unit_for_variable_name(self.variable_name),
            band_scheme=_band_scheme_for_variable_name(self.variable_name),
        )

        self.latest = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_date": self.target_date,
            "variable_name": self.variable_name,
            "value": extracted.value,
            "source_mode": extracted.source_mode,
            "source_path": extracted.source_path,
            "notes": extracted.notes,
            "raw_value": normalized.get("raw_value"),
            "raw_unit": normalized.get("raw_unit"),
            "canonical_value": normalized.get("canonical_value"),
            "canonical_unit": normalized.get("canonical_unit"),
            "display_value": normalized.get("display_value"),
            "display_unit": normalized.get("display_unit"),
            "conversion_rule": _conversion_rule_for_family(_family_for_variable_name(self.variable_name)),
            "conversion_applied": str(normalized.get("raw_unit") or "") != str(normalized.get("canonical_unit") or ""),
            "precision_policy_ref": normalized.get("precision_policy_ref"),
            "rounding_policy_ref": normalized.get("rounding_policy_ref"),
            "band_mapping_policy_ref": normalized.get("band_mapping_policy_ref"),
            "normalization_version": normalized.get("normalization_version"),
        }
        return self.latest


def _family_for_variable_name(variable_name: str) -> str:
    if variable_name == "daily_max_temperature":
        return "temperature_daily_max"
    if variable_name == "daily_min_temperature":
        return "temperature_daily_min"
    if variable_name == "daily_precipitation_sum":
        return "weather_metric.precipitation"
    if variable_name == "daily_snowfall_sum":
        return "weather_metric.snowfall"
    if variable_name == "daily_max_wind_speed":
        return "weather_metric.wind_speed"
    return "climate_index"


def _band_scheme_for_variable_name(variable_name: str) -> str | None:
    if variable_name in {"daily_max_temperature", "daily_min_temperature"}:
        return "temperature_4_bucket"
    if variable_name == "daily_precipitation_sum":
        return "precipitation_range_3way"
    if variable_name == "daily_snowfall_sum":
        return "snowfall_range_3way"
    if variable_name == "daily_max_wind_speed":
        return "wind_speed_range_3way"
    return None


def _conversion_rule_for_family(family: str) -> str | None:
    if family:
        return "identity"
    return None


def _raw_unit_for_variable_name(variable_name: str) -> str:
    if variable_name in {"daily_max_temperature", "daily_min_temperature"}:
        return "celsius"
    if variable_name == "daily_precipitation_sum":
        return "mm"
    if variable_name == "daily_snowfall_sum":
        return "cm"
    if variable_name == "daily_max_wind_speed":
        return "km/h"
    return "source_defined"
