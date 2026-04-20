from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from weather_rules_research.climate_index import GlobalTemperatureIndexLoader
from weather_rules_research.official_obs import WundergroundHistoryHelper
from weather_rules_research.open_meteo.extractors import OpenMeteoExtractor
from weather_rules_research.open_meteo.forecast_client import OpenMeteoForecastClient
from weather_rules_research.rules.live_market_resolver import (
    load_rulebook,
    resolve_market_resolution,
)
from weather_rules_research.sea_ice import (
    SeaIceExtentLoader,
    classify_sea_ice_band,
    extract_sea_ice_extent_value,
)
from weather_rules_research.stations.mapper import StationMapper


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "data" / "outputs"
OUTPUT_PATH = OUTPUT_DIR / "forecast_realtime_snapshot.json"
SNAPSHOTS_DIR = OUTPUT_DIR / "forecast_realtime_snapshots"
LIVE_MARKET_JSON = Path(
    os.getenv(
        "LIVE_MARKET_JSON",
        str(
            BASE_DIR.parent
            / "polymarket-weather-ingest"
            / "data"
            / "outputs"
            / "market_realtime_simple.json"
        ),
    )
)
RULEBOOK_JSON = Path(
    os.getenv(
        "RULEBOOK_JSON",
        str(OUTPUT_DIR / "sample_rulebook.json"),
    )
)
STATION_MAP_JSON = Path(
    os.getenv(
        "STATION_MAP_JSON",
        str(OUTPUT_DIR / "sample_station_map.json"),
    )
)
GLOBAL_TEMPERATURE_INDEX_JSON = Path(
    os.getenv(
        "GLOBAL_TEMPERATURE_INDEX_JSON",
        str(OUTPUT_DIR / "global_temperature_index_snapshot.json"),
    )
)
SEA_ICE_EXTENT_JSON = Path(
    os.getenv(
        "SEA_ICE_EXTENT_JSON",
        str(OUTPUT_DIR / "sea_ice_extent_snapshot.json"),
    )
)

VARIABLE_NAME = "daily_max_temperature"
FORECAST_REFRESH_INTERVAL_SECONDS = int(os.getenv("FORECAST_REFRESH_INTERVAL_SECONDS", "300"))
MARKET_CHECK_INTERVAL_SECONDS = int(os.getenv("MARKET_CHECK_INTERVAL_SECONDS", "15"))


def classify_temperature_band(value: float) -> str:
    rounded = round(value)
    if rounded <= 26:
        return "26_or_below"
    if rounded == 27:
        return "27"
    if rounded == 28:
        return "28"
    return "29_plus"


def confidence_from_source_mode(source_mode: str, value: float | None) -> float:
    if value is None:
        return 0.0

    if source_mode.startswith("daily."):
        return 0.90
    if source_mode.startswith("hourly."):
        return 0.75
    return 0.50


def request_params_for_variable(variable_name: str) -> dict[str, str | None]:
    if variable_name in {"daily_max_temperature", "daily_min_temperature"}:
        return {
            "hourly": "temperature_2m",
            "daily": "temperature_2m_max,temperature_2m_min",
        }
    if variable_name == "daily_precipitation_sum":
        return {
            "hourly": "precipitation",
            "daily": "precipitation_sum",
        }
    if variable_name == "daily_snowfall_sum":
        return {
            "hourly": "snowfall",
            "daily": "snowfall_sum",
        }
    if variable_name == "daily_max_wind_speed":
        return {
            "hourly": "wind_speed_10m",
            "daily": "wind_speed_10m_max",
        }
    return {
        "hourly": "temperature_2m",
        "daily": "temperature_2m_max,temperature_2m_min",
    }


def classify_model_band(
    *,
    variable_name: str,
    value: float | None,
    resolution_snapshot: dict | None,
) -> str | None:
    if value is None:
        return None
    if variable_name in {"daily_max_temperature", "daily_min_temperature"}:
        return classify_temperature_band(value)
    if variable_name in {
        "daily_precipitation_sum",
        "daily_snowfall_sum",
        "daily_max_wind_speed",
    }:
        lower = _to_float((resolution_snapshot or {}).get("threshold_lower"))
        upper = _to_float((resolution_snapshot or {}).get("threshold_upper"))
        return classify_range_band(value, lower=lower, upper=upper)
    return None


def classify_range_band(
    value: float,
    *,
    lower: float | None,
    upper: float | None,
) -> str | None:
    if lower is not None and value < lower:
        return "below_range"
    if upper is not None and value > upper:
        return "above_range"
    if lower is not None or upper is not None:
        return "in_range"
    return None


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_live_market_snapshot() -> dict:
    return json.loads(LIVE_MARKET_JSON.read_text(encoding="utf-8"))


def load_global_temperature_index_snapshot() -> dict | None:
    if not GLOBAL_TEMPERATURE_INDEX_JSON.exists():
        return None
    loader = GlobalTemperatureIndexLoader()
    return loader.load(GLOBAL_TEMPERATURE_INDEX_JSON)


def load_sea_ice_extent_snapshot() -> dict | None:
    if not SEA_ICE_EXTENT_JSON.exists():
        return None
    loader = SeaIceExtentLoader()
    return loader.load(SEA_ICE_EXTENT_JSON)


def build_and_write_snapshot(snapshot: dict) -> dict:
    write_json(OUTPUT_PATH, snapshot)
    market_id = str(snapshot.get("market_id") or "")
    if market_id:
        write_json(SNAPSHOTS_DIR / f"forecast_realtime_snapshot_{market_id}.json", snapshot)
    return snapshot


async def poll_once(live_market: dict | None = None) -> dict:
    live_market = live_market or load_live_market_snapshot()
    rules = load_rulebook(RULEBOOK_JSON)
    resolution = resolve_market_resolution(live_market, rules)
    selected_rule = resolution.rule
    selection_reason = resolution.reason
    taxonomy = resolution.taxonomy
    resolution_snapshot = resolution.snapshot

    if selected_rule is None:
        if taxonomy.market_family == "global_temperature_index":
            index_snapshot = load_global_temperature_index_snapshot()
            if index_snapshot is not None:
                ordinal_rank = index_snapshot.get("ordinal_rank")
                model_band = f"top_{ordinal_rank}" if ordinal_rank is not None else None
                snapshot = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "market_id": live_market.get("market_id"),
                    "market_question": live_market.get("market_question"),
                    "location_name": live_market.get("location_name"),
                    "target_date": live_market.get("target_date"),
                    "variable_name": "global_temperature_index",
                    "value": ordinal_rank,
                    "model_band": model_band,
                    "band_scheme": taxonomy.band_scheme,
                    "confidence_score": 1.0,
                    "source_mode": "global_temperature_index.snapshot",
                    "notes": index_snapshot.get("notes") or "Loaded global temperature index snapshot",
                    "rule_status": "matched_index",
                    "rule_market_id": live_market.get("market_id"),
                    "station_name": None,
                    "station_id": None,
                    "market_family": taxonomy.market_family,
                    "resolution_scope": taxonomy.resolution_scope,
                    "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
                    "required_data_source": taxonomy.required_data_source,
                    "taxonomy_notes": taxonomy.notes,
                    "resolution_snapshot": resolution_snapshot,
                    "index_snapshot": index_snapshot,
                }
                return build_and_write_snapshot(snapshot)

        if taxonomy.market_family == "sea_ice_extent":
            sea_ice_snapshot = load_sea_ice_extent_snapshot()
            if sea_ice_snapshot is not None:
                lower = _to_float((resolution_snapshot or {}).get("threshold_lower"))
                upper = _to_float((resolution_snapshot or {}).get("threshold_upper"))
                extent_value = extract_sea_ice_extent_value(sea_ice_snapshot)
                model_band = classify_sea_ice_band(
                    extent_value,
                    lower=lower,
                    upper=upper,
                )
                snapshot = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "market_id": live_market.get("market_id"),
                    "market_question": live_market.get("market_question"),
                    "location_name": live_market.get("location_name"),
                    "target_date": live_market.get("target_date"),
                    "variable_name": "minimum_sea_ice_extent",
                    "value": extent_value,
                    "model_band": model_band,
                    "band_scheme": taxonomy.band_scheme,
                    "confidence_score": 0.95 if extent_value is not None else 0.0,
                    "source_mode": "sea_ice_extent.snapshot",
                    "notes": sea_ice_snapshot.get("notes") or "Loaded sea ice extent snapshot",
                    "rule_status": "matched_snapshot",
                    "rule_market_id": live_market.get("market_id"),
                    "station_name": None,
                    "station_id": None,
                    "market_family": taxonomy.market_family,
                    "resolution_scope": taxonomy.resolution_scope,
                    "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
                    "required_data_source": taxonomy.required_data_source,
                    "taxonomy_notes": taxonomy.notes,
                    "resolution_snapshot": resolution_snapshot,
                    "sea_ice_snapshot": sea_ice_snapshot,
                }
                return build_and_write_snapshot(snapshot)

        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_id": live_market.get("market_id"),
            "market_question": live_market.get("market_question"),
            "location_name": live_market.get("location_name"),
            "target_date": live_market.get("target_date"),
            "variable_name": live_market.get("variable_name"),
            "value": None,
            "model_band": None,
            "band_scheme": taxonomy.band_scheme,
            "confidence_score": 0.0,
            "source_mode": "no_matching_rule",
            "notes": selection_reason,
            "rule_status": "no_matching_rule",
            "rule_market_id": None,
            "station_name": None,
            "station_id": None,
            "market_family": taxonomy.market_family,
            "resolution_scope": taxonomy.resolution_scope,
            "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
            "required_data_source": taxonomy.required_data_source,
            "taxonomy_notes": taxonomy.notes,
            "resolution_snapshot": resolution_snapshot,
        }
        return build_and_write_snapshot(snapshot)

    mapper = StationMapper(str(STATION_MAP_JSON))
    station = mapper.map_rule_to_station(selected_rule)
    if station is None:
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_id": live_market.get("market_id"),
            "market_question": live_market.get("market_question"),
            "location_name": selected_rule.location_name,
            "target_date": selected_rule.target_date or live_market.get("target_date"),
            "variable_name": selected_rule.variable_name,
            "value": None,
            "model_band": None,
            "band_scheme": taxonomy.band_scheme,
            "confidence_score": 0.0,
            "source_mode": "no_station_mapping",
            "notes": "Matched a rule, but station mapping failed",
            "rule_status": "matched_rule_no_station",
            "rule_market_id": selected_rule.market_id,
            "station_name": selected_rule.station_name,
            "station_id": None,
            "market_family": taxonomy.market_family,
            "resolution_scope": taxonomy.resolution_scope,
            "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
            "required_data_source": taxonomy.required_data_source,
            "taxonomy_notes": taxonomy.notes,
            "resolution_snapshot": resolution_snapshot,
        }
        return build_and_write_snapshot(snapshot)

    client = OpenMeteoForecastClient()
    extractor = OpenMeteoExtractor()

    request_params = request_params_for_variable(selected_rule.variable_name)
    payload = await client.fetch(
        latitude=station.latitude,
        longitude=station.longitude,
        hourly=request_params.get("hourly"),
        daily=request_params.get("daily"),
    )

    extracted = extractor.extract_for_market_rule(
        payload=payload,
        target_date=selected_rule.target_date or live_market.get("target_date") or "",
        variable_name=selected_rule.variable_name,
    )

    model_value = extracted.value
    model_band = classify_model_band(
        variable_name=selected_rule.variable_name,
        value=model_value,
        resolution_snapshot=resolution_snapshot,
    )
    confidence_score = confidence_from_source_mode(extracted.source_mode, model_value)
    station_history_url = WundergroundHistoryHelper.build_history_url_for_station(station)
    notes = extracted.notes
    if station_history_url:
        suffix = f"Wunderground station history: {station_history_url}"
        notes = f"{notes} | {suffix}" if notes else suffix

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_id": live_market.get("market_id"),
        "market_question": live_market.get("market_question"),
        "location_name": selected_rule.location_name,
        "target_date": extracted.target_date,
        "variable_name": extracted.variable_name,
        "value": model_value,
        "model_band": model_band,
        "band_scheme": taxonomy.band_scheme,
        "confidence_score": confidence_score,
        "source_mode": extracted.source_mode,
        "notes": notes,
        "rule_status": "matched",
        "rule_market_id": selected_rule.market_id,
        "station_name": station.station_name,
        "station_id": station.nws_station_id or station.cdo_station_id,
        "station_source": station.source,
        "station_history_url": station_history_url,
        "market_family": taxonomy.market_family,
        "resolution_scope": taxonomy.resolution_scope,
        "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
        "required_data_source": taxonomy.required_data_source,
        "taxonomy_notes": taxonomy.notes,
        "resolution_snapshot": resolution_snapshot,
    }

    return build_and_write_snapshot(snapshot)


def _market_fingerprint(live_market: dict) -> tuple[str | None, str | None, str | None]:
    return (
        str(live_market.get("market_id") or ""),
        str(live_market.get("market_question") or ""),
        str(live_market.get("market_band_scheme") or ""),
    )


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("STARTING WEATHER REALTIME POLLER")
    print(f"Live market    : {LIVE_MARKET_JSON}")
    print(f"Climate index  : {GLOBAL_TEMPERATURE_INDEX_JSON}")
    print(f"Sea ice index  : {SEA_ICE_EXTENT_JSON}")
    print(f"Rulebook       : {RULEBOOK_JSON}")
    print(f"Station map    : {STATION_MAP_JSON}")
    print(f"Output         : {OUTPUT_PATH}")
    print(f"Snapshot dir   : {SNAPSHOTS_DIR}")
    print(f"Poll Interval  : {MARKET_CHECK_INTERVAL_SECONDS}s")
    print("=" * 80)

    last_fingerprint: tuple[str | None, str | None, str | None] | None = None
    last_refresh_at: datetime | None = None

    while True:
        try:
            live_market = load_live_market_snapshot()
            fingerprint = _market_fingerprint(live_market)
            now = datetime.now(timezone.utc)
            should_refresh = (
                last_fingerprint != fingerprint
                or last_refresh_at is None
                or (now - last_refresh_at).total_seconds() >= FORECAST_REFRESH_INTERVAL_SECONDS
            )

            if should_refresh:
                snapshot = await poll_once(live_market)
                last_fingerprint = fingerprint
                last_refresh_at = now
            else:
                snapshot = {
                    "timestamp": now.isoformat(),
                    "market_id": live_market.get("market_id"),
                    "value": None,
                    "model_band": None,
                    "confidence_score": 0.0,
                    "source_mode": "unchanged_market_skipped",
                    "rule_status": "unchanged",
                }
            print(
                f"[{snapshot['timestamp']}] "
                f"market_id={snapshot['market_id']} "
                f"value={snapshot['value']} "
                f"band={snapshot['model_band']} "
                f"confidence={snapshot['confidence_score']} "
                f"rule_status={snapshot.get('rule_status')} "
                f"refreshed={should_refresh}"
            )
        except Exception as e:
            print(f"[weather-realtime] error: {e}")

        await asyncio.sleep(MARKET_CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
