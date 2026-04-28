from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from weather_rules_research.governance import normalize_measurement


@dataclass
class ForecastExtractionResult:
    target_date: str
    variable_name: str
    value: float | None
    source_mode: str
    source_path: str | None = None
    notes: str | None = None
    raw_value: float | None = None
    raw_unit: str | None = None
    canonical_value: float | None = None
    canonical_unit: str | None = None
    display_value: float | None = None
    display_unit: str | None = None
    conversion_rule: str | None = None
    conversion_applied: bool = False
    precision_policy_ref: str | None = None
    rounding_policy_ref: str | None = None
    band_mapping_policy_ref: str | None = None
    normalization_version: str = "measurement_normalization.v1"


class OpenMeteoExtractor:
    """
    Extract target-date forecast values from Open-Meteo payloads.

    Supported modes:
    - daily max/min temperature
    - hourly aggregation fallback
    """

    def extract_for_market_rule(
        self,
        payload: dict[str, Any],
        target_date: str,
        variable_name: str,
    ) -> ForecastExtractionResult:
        if variable_name == "daily_max_temperature":
            return self._with_measurement_metadata(
                self.extract_daily_max_temperature(payload, target_date)
            )

        if variable_name == "daily_min_temperature":
            return self._with_measurement_metadata(
                self.extract_daily_min_temperature(payload, target_date)
            )

        if variable_name == "daily_precipitation_sum":
            return self._with_measurement_metadata(
                self.extract_daily_precipitation_sum(payload, target_date)
            )

        if variable_name == "daily_snowfall_sum":
            return self._with_measurement_metadata(
                self.extract_daily_snowfall_sum(payload, target_date)
            )

        if variable_name == "daily_max_wind_speed":
            return self._with_measurement_metadata(
                self.extract_daily_max_wind_speed(payload, target_date)
            )

        return self._with_measurement_metadata(
            ForecastExtractionResult(
                target_date=target_date,
                variable_name=variable_name,
                value=None,
                source_mode="Unsupported variable",
                source_path="unsupported",
                notes=f"Unsupported variable_name: {variable_name}",
            )
        )

    def extract_daily_max_temperature(
        self,
        payload: dict[str, Any],
        target_date: str,
    ) -> ForecastExtractionResult:
        daily = payload.get("daily")
        if isinstance(daily, dict):
            times = daily.get("time")
            values = daily.get("temperature_2m_max")
            if self._is_valid_parallel_series(times, values):
                value = self._extract_from_parallel_series(
                    times=times,
                    values=values,
                    target_date=target_date,
                )
                if value is not None:
                    return ForecastExtractionResult(
                        target_date=target_date,
                        variable_name="daily_max_temperature",
                        value=float(value),
                        source_mode="Daily forecast matched",
                        source_path="daily.temperature_2m_max",
                    )

        hourly = payload.get("hourly")
        if isinstance(hourly, dict):
            times = hourly.get("time")
            values = hourly.get("temperature_2m")
            if self._is_valid_parallel_series(times, values):
                value = self._aggregate_hourly_for_day(
                    times=times,
                    values=values,
                    target_date=target_date,
                    agg="max",
                )
                if value is not None:
                    return ForecastExtractionResult(
                        target_date=target_date,
                        variable_name="daily_max_temperature",
                        value=float(value),
                        source_mode="Hourly fallback used",
                        source_path="hourly.temperature_2m:max",
                    )

        return ForecastExtractionResult(
            target_date=target_date,
            variable_name="daily_max_temperature",
            value=None,
            source_mode="Target-date forecast unavailable",
            source_path="not_found",
            notes="No daily or hourly temperature data available for target date",
        )

    def extract_daily_precipitation_sum(
        self,
        payload: dict[str, Any],
        target_date: str,
    ) -> ForecastExtractionResult:
        daily = payload.get("daily")
        if isinstance(daily, dict):
            times = daily.get("time")
            values = daily.get("precipitation_sum")
            if self._is_valid_parallel_series(times, values):
                value = self._extract_from_parallel_series(
                    times=times,
                    values=values,
                    target_date=target_date,
                )
                if value is not None:
                    return ForecastExtractionResult(
                        target_date=target_date,
                        variable_name="daily_precipitation_sum",
                        value=float(value),
                        source_mode="Daily forecast matched",
                        source_path="daily.precipitation_sum",
                    )

        hourly = payload.get("hourly")
        if isinstance(hourly, dict):
            times = hourly.get("time")
            values = hourly.get("precipitation")
            if self._is_valid_parallel_series(times, values):
                value = self._aggregate_hourly_for_day(
                    times=times,
                    values=values,
                    target_date=target_date,
                    agg="sum",
                )
                if value is not None:
                    return ForecastExtractionResult(
                        target_date=target_date,
                        variable_name="daily_precipitation_sum",
                        value=float(value),
                        source_mode="Hourly fallback used",
                        source_path="hourly.precipitation:sum",
                    )

        return ForecastExtractionResult(
            target_date=target_date,
            variable_name="daily_precipitation_sum",
            value=None,
            source_mode="Target-date forecast unavailable",
            source_path="not_found",
            notes="No daily or hourly precipitation data available for target date",
        )

    def extract_daily_snowfall_sum(
        self,
        payload: dict[str, Any],
        target_date: str,
    ) -> ForecastExtractionResult:
        daily = payload.get("daily")
        if isinstance(daily, dict):
            times = daily.get("time")
            values = daily.get("snowfall_sum")
            if self._is_valid_parallel_series(times, values):
                value = self._extract_from_parallel_series(
                    times=times,
                    values=values,
                    target_date=target_date,
                )
                if value is not None:
                    return ForecastExtractionResult(
                        target_date=target_date,
                        variable_name="daily_snowfall_sum",
                        value=float(value),
                        source_mode="Daily forecast matched",
                        source_path="daily.snowfall_sum",
                    )

        hourly = payload.get("hourly")
        if isinstance(hourly, dict):
            times = hourly.get("time")
            values = hourly.get("snowfall")
            if self._is_valid_parallel_series(times, values):
                value = self._aggregate_hourly_for_day(
                    times=times,
                    values=values,
                    target_date=target_date,
                    agg="sum",
                )
                if value is not None:
                    return ForecastExtractionResult(
                        target_date=target_date,
                        variable_name="daily_snowfall_sum",
                        value=float(value),
                        source_mode="Hourly fallback used",
                        source_path="hourly.snowfall:sum",
                    )

        return ForecastExtractionResult(
            target_date=target_date,
            variable_name="daily_snowfall_sum",
            value=None,
            source_mode="Target-date forecast unavailable",
            source_path="not_found",
            notes="No daily or hourly snowfall data available for target date",
        )

    def extract_daily_max_wind_speed(
        self,
        payload: dict[str, Any],
        target_date: str,
    ) -> ForecastExtractionResult:
        daily = payload.get("daily")
        if isinstance(daily, dict):
            times = daily.get("time")
            values = daily.get("wind_speed_10m_max")
            if self._is_valid_parallel_series(times, values):
                value = self._extract_from_parallel_series(
                    times=times,
                    values=values,
                    target_date=target_date,
                )
                if value is not None:
                    return ForecastExtractionResult(
                        target_date=target_date,
                        variable_name="daily_max_wind_speed",
                        value=float(value),
                        source_mode="Daily forecast matched",
                        source_path="daily.wind_speed_10m_max",
                    )

        hourly = payload.get("hourly")
        if isinstance(hourly, dict):
            times = hourly.get("time")
            values = hourly.get("wind_speed_10m")
            if self._is_valid_parallel_series(times, values):
                value = self._aggregate_hourly_for_day(
                    times=times,
                    values=values,
                    target_date=target_date,
                    agg="max",
                )
                if value is not None:
                    return ForecastExtractionResult(
                        target_date=target_date,
                        variable_name="daily_max_wind_speed",
                        value=float(value),
                        source_mode="Hourly fallback used",
                        source_path="hourly.wind_speed_10m:max",
                    )

        return ForecastExtractionResult(
            target_date=target_date,
            variable_name="daily_max_wind_speed",
            value=None,
            source_mode="Target-date forecast unavailable",
            source_path="not_found",
            notes="No daily or hourly wind-speed data available for target date",
        )

    def extract_daily_min_temperature(
        self,
        payload: dict[str, Any],
        target_date: str,
    ) -> ForecastExtractionResult:
        daily = payload.get("daily")
        if isinstance(daily, dict):
            times = daily.get("time")
            values = daily.get("temperature_2m_min")
            if self._is_valid_parallel_series(times, values):
                value = self._extract_from_parallel_series(
                    times=times,
                    values=values,
                    target_date=target_date,
                )
                if value is not None:
                    return ForecastExtractionResult(
                        target_date=target_date,
                        variable_name="daily_min_temperature",
                        value=float(value),
                        source_mode="Daily forecast matched",
                        source_path="daily.temperature_2m_min",
                    )

        hourly = payload.get("hourly")
        if isinstance(hourly, dict):
            times = hourly.get("time")
            values = hourly.get("temperature_2m")
            if self._is_valid_parallel_series(times, values):
                value = self._aggregate_hourly_for_day(
                    times=times,
                    values=values,
                    target_date=target_date,
                    agg="min",
                )
                if value is not None:
                    return ForecastExtractionResult(
                        target_date=target_date,
                        variable_name="daily_min_temperature",
                        value=float(value),
                        source_mode="Hourly fallback used",
                        source_path="hourly.temperature_2m:min",
                    )

        return ForecastExtractionResult(
            target_date=target_date,
            variable_name="daily_min_temperature",
            value=None,
            source_mode="Target-date forecast unavailable",
            source_path="not_found",
            notes="No daily or hourly temperature data available for target date",
        )

    def _extract_from_parallel_series(
        self,
        times: list[str],
        values: list[float | int | None],
        target_date: str,
    ) -> float | int | None:
        for t, v in zip(times, values):
            if t == target_date:
                return v
        return None

    def _aggregate_hourly_for_day(
        self,
        times: list[str],
        values: list[float | int | None],
        target_date: str,
        agg: str,
    ) -> float | None:
        bucket: list[float] = []

        for t, v in zip(times, values):
            if v is None:
                continue
            dt = self._safe_parse_datetime(t)
            if dt is None:
                continue
            if dt.date().isoformat() == target_date:
                bucket.append(float(v))

        if not bucket:
            return None

        if agg == "max":
            return max(bucket)
        if agg == "min":
            return min(bucket)
        if agg == "sum":
            return sum(bucket)

        raise ValueError(f"Unsupported aggregation: {agg}")

    @staticmethod
    def _safe_parse_datetime(value: str) -> datetime | None:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _is_valid_parallel_series(times: Any, values: Any) -> bool:
        return (
            isinstance(times, list)
            and isinstance(values, list)
            and len(times) == len(values)
        )

    @staticmethod
    def _with_measurement_metadata(result: ForecastExtractionResult) -> ForecastExtractionResult:
        normalized = normalize_measurement(
            {"value": result.value, "unit": _raw_unit_for_variable_name(result.variable_name)},
            family=_family_for_variable_name(result.variable_name),
            variable_name=result.variable_name,
            raw_unit=_raw_unit_for_variable_name(result.variable_name),
            band_scheme=_band_scheme_for_variable_name(result.variable_name),
        )
        result.raw_value = normalized.get("raw_value")
        result.raw_unit = normalized.get("raw_unit")
        result.canonical_value = normalized.get("canonical_value")
        result.canonical_unit = normalized.get("canonical_unit")
        result.display_value = normalized.get("display_value")
        result.display_unit = normalized.get("display_unit")
        result.conversion_rule = _conversion_rule_for_family(_family_for_variable_name(result.variable_name))
        result.conversion_applied = str(normalized.get("raw_unit") or "") != str(
            normalized.get("canonical_unit") or ""
        )
        result.precision_policy_ref = normalized.get("precision_policy_ref")
        result.rounding_policy_ref = normalized.get("rounding_policy_ref")
        result.band_mapping_policy_ref = normalized.get("band_mapping_policy_ref")
        result.normalization_version = str(
            normalized.get("normalization_version") or "measurement_normalization.v1"
        )
        return result


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
