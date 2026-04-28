from __future__ import annotations

from datetime import date

from weather_rules_research.config import get_settings
from weather_rules_research.governance import normalize_measurement
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
        family = _family_for_variable_name(rule.variable_name)
        normalized = normalize_measurement(
            {"value": predicted_temperature_c, "unit": _raw_unit_for_variable_name(rule.variable_name)},
            family=family,
            variable_name=rule.variable_name,
            raw_unit=_raw_unit_for_variable_name(rule.variable_name),
            band_scheme=_band_scheme_for_variable_name(rule.variable_name),
        )
        return ForecastSnapshot(
            market_id=rule.market_id,
            station_id=station.nws_station_id or station.cdo_station_id or station.station_name,
            market_type=rule.market_type,
            target_date=settlement_date,
            issued_at=issued_at,
            predicted_temperature_c=predicted_temperature_c,
            raw_payload_ref=f"open-meteo://sample/{rule.market_id}/{settlement_date.isoformat()}",
            source_mode="Daily forecast matched",
            source_path="daily.temperature_2m_max",
            raw_value=normalized.get("raw_value"),
            raw_unit=normalized.get("raw_unit"),
            canonical_value=normalized.get("canonical_value"),
            canonical_unit=normalized.get("canonical_unit"),
            display_value=normalized.get("display_value"),
            display_unit=normalized.get("display_unit"),
            conversion_rule=_conversion_rule_for_family(family),
            conversion_applied=str(normalized.get("raw_unit") or "") != str(normalized.get("canonical_unit") or ""),
            precision_policy_ref=normalized.get("precision_policy_ref"),
            rounding_policy_ref=normalized.get("rounding_policy_ref"),
            band_mapping_policy_ref=normalized.get("band_mapping_policy_ref"),
            normalization_version=str(normalized.get("normalization_version") or "measurement_normalization.v1"),
        )


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
    if family in {"temperature_daily_max", "temperature_daily_min"}:
        return "identity"
    if family == "weather_metric.wind_speed":
        return "identity"
    if family in {"weather_metric.precipitation", "weather_metric.snowfall"}:
        return "identity"
    return "identity"


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
