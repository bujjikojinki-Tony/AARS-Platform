from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.official_obs.daily_fetcher import DailySettlementFetcher
from weather_rules_research.rules.market_taxonomy import classify_market_question


class StationSettlementBackfiller:
    def __init__(self, fetcher: DailySettlementFetcher | None = None) -> None:
        self.fetcher = fetcher

    async def backfill_records(
        self,
        *,
        rules: list[MarketRule],
        scenarios: list[dict],
        enable_fetch: bool = False,
    ) -> list[dict]:
        rules_by_market = {str(rule.market_id): rule for rule in rules}
        records: list[dict] = []

        for scenario in scenarios:
            market_id = str(scenario.get("market_id") or "")
            rule = rules_by_market.get(market_id)
            if rule is None:
                continue

            if scenario.get("official_value") is not None:
                records.append(self._record_from_payload(rule=rule, payload=scenario))
                continue

            if not enable_fetch or self.fetcher is None:
                continue

            station_id = (
                scenario.get("station_id")
                or rule.nws_station_id
                or rule.cdo_station_id
            )
            target_date = str(scenario.get("target_date") or "")
            if not station_id or not target_date:
                continue

            payload = await self.fetcher.fetch_daily_value(
                station_id=str(station_id),
                target_date=target_date,
                variable_name=rule.variable_name,
            )
            merged = {
                **scenario,
                **payload,
            }
            records.append(self._record_from_payload(rule=rule, payload=merged))

        return records

    def _record_from_payload(self, *, rule: MarketRule, payload: dict) -> dict:
        taxonomy = classify_market_question(rule.market_question)
        official_value = _to_float(payload.get("official_value"))
        resolved_band = payload.get("resolved_band")
        if resolved_band is None:
            resolved_band = _classify_station_resolved_band(
                band_scheme=taxonomy.band_scheme,
                official_value=official_value,
            )

        station_id = (
            payload.get("station_id")
            or rule.nws_station_id
            or rule.cdo_station_id
            or rule.station_name
        )

        return {
            "market_id": rule.market_id,
            "market_question": rule.market_question,
            "market_family": taxonomy.market_family,
            "target_date": str(payload.get("target_date") or ""),
            "variable_name": rule.variable_name,
            "station_id": station_id,
            "official_value": official_value,
            "resolved_band": resolved_band,
            "expected_band": payload.get("expected_band"),
            "source": payload.get("source") or "station_settlement_backfill",
            "source_timestamp": payload.get("source_timestamp"),
            "source_url": payload.get("source_url"),
            "label_type": payload.get("label_type") or "settlement_grade",
            "unit": payload.get("unit") or _unit_for_variable(rule.variable_name),
            "notes": payload.get("notes"),
            "raw_payload_ref": payload.get("raw_payload_ref"),
        }


def build_station_backfill_summary(
    records: list[dict],
    *,
    fetch_enabled: bool,
) -> dict:
    family_counts = Counter(str(record.get("market_family") or "unknown") for record in records)
    source_counts = Counter(str(record.get("source") or "unknown") for record in records)
    label_counts = Counter(str(record.get("label_type") or "unknown") for record in records)

    return {
        "schema_version": "station_settlement_backfill_summary.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fetch_enabled": fetch_enabled,
        "record_count": len(records),
        "market_family_counts": dict(family_counts),
        "source_counts": dict(source_counts),
        "label_type_counts": dict(label_counts),
        "note": (
            "Station settlement backfill supports sample-mode scaffolding by default and "
            "can switch to fetch-mode when OFFICIAL_STATION_FETCH_ENABLED=1 and upstream "
            "station data credentials are available."
        ),
    }


def _classify_station_resolved_band(
    *,
    band_scheme: str | None,
    official_value: float | None,
) -> str | None:
    if official_value is None:
        return None
    if band_scheme == "temperature_4_bucket":
        return _classify_temperature_band(official_value)
    return None


def _classify_temperature_band(value: float) -> str:
    rounded = round(value)
    if rounded <= 26:
        return "26_or_below"
    if rounded == 27:
        return "27"
    if rounded == 28:
        return "28"
    return "29_plus"


def _unit_for_variable(variable_name: str | None) -> str | None:
    if variable_name in {"daily_max_temperature", "daily_min_temperature"}:
        return "celsius"
    if variable_name == "daily_precipitation_sum":
        return "mm"
    if variable_name == "daily_snowfall_sum":
        return "cm"
    if variable_name == "daily_max_wind_speed":
        return "km_h"
    return None


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
