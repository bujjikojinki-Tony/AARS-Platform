from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ForecastExtractionResult:
    target_date: str
    variable_name: str
    value: float | None
    source_mode: str
    notes: str | None = None


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
            return self.extract_daily_max_temperature(payload, target_date)

        if variable_name == "daily_min_temperature":
            return self.extract_daily_min_temperature(payload, target_date)

        if variable_name == "daily_precipitation_sum":
            return self.extract_daily_precipitation_sum(payload, target_date)

        if variable_name == "daily_snowfall_sum":
            return self.extract_daily_snowfall_sum(payload, target_date)

        if variable_name == "daily_max_wind_speed":
            return self.extract_daily_max_wind_speed(payload, target_date)

        return ForecastExtractionResult(
            target_date=target_date,
            variable_name=variable_name,
            value=None,
            source_mode="unsupported",
            notes=f"Unsupported variable_name: {variable_name}",
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
                        source_mode="daily.temperature_2m_max",
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
                        source_mode="hourly.temperature_2m:max",
                    )

        return ForecastExtractionResult(
            target_date=target_date,
            variable_name="daily_max_temperature",
            value=None,
            source_mode="not_found",
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
                        source_mode="daily.precipitation_sum",
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
                        source_mode="hourly.precipitation:sum",
                    )

        return ForecastExtractionResult(
            target_date=target_date,
            variable_name="daily_precipitation_sum",
            value=None,
            source_mode="not_found",
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
                        source_mode="daily.snowfall_sum",
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
                        source_mode="hourly.snowfall:sum",
                    )

        return ForecastExtractionResult(
            target_date=target_date,
            variable_name="daily_snowfall_sum",
            value=None,
            source_mode="not_found",
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
                        source_mode="daily.wind_speed_10m_max",
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
                        source_mode="hourly.wind_speed_10m:max",
                    )

        return ForecastExtractionResult(
            target_date=target_date,
            variable_name="daily_max_wind_speed",
            value=None,
            source_mode="not_found",
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
                        source_mode="daily.temperature_2m_min",
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
                        source_mode="hourly.temperature_2m:min",
                    )

        return ForecastExtractionResult(
            target_date=target_date,
            variable_name="daily_min_temperature",
            value=None,
            source_mode="not_found",
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
