from __future__ import annotations

from datetime import date
from pathlib import Path

from weather_rules_research.backtest import evaluate_bias, join_forecasts_to_settlements, summarize_bias_metrics
from weather_rules_research.models import BiasSummary, MarketRule, StationMapEntry
from weather_rules_research.official_obs import OfficialObservationFetcher
from weather_rules_research.open_meteo import OpenMeteoForecastClient
from weather_rules_research.outputs import (
    export_bias_report,
    export_bias_summary,
    export_rulebook,
    export_station_map,
)
from weather_rules_research.rules import normalize_market_rule
from weather_rules_research.stations import StationMapper

MANUAL_STATION_MAP_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "processed" / "station_maps" / "manual_station_map.json"
)


def build_sample_rules() -> list[MarketRule]:
    return [
        normalize_market_rule(
            market_id="poly-daily-high-central-park-001",
            question="Highest temperature in Central Park on 2026-06-01?",
            rules_text="Resolves using official station data from Central Park in New York time for the daily high.",
            timezone="America/New_York",
        ),
        normalize_market_rule(
            market_id="poly-daily-low-changi-001",
            question="Lowest temperature in Singapore Changi Airport on 2026-01-15?",
            rules_text="Resolves using official station data from Changi Airport in Singapore time for the daily low.",
            timezone="Asia/Singapore",
        ),
        normalize_market_rule(
            market_id="poly-daily-high-shanghai-001",
            question="Highest temperature in Shanghai on 2026-04-14?",
            rules_text="Resolves using official station data from Shanghai Pudong International Airport in Shanghai time for the daily high.",
            timezone="Asia/Shanghai",
        ),
    ]


def _load_station_mapper() -> StationMapper:
    return StationMapper(str(MANUAL_STATION_MAP_PATH))


def build_sample_stations(rules: list[MarketRule]) -> list[StationMapEntry]:
    mapper = _load_station_mapper()
    mappings: list[StationMapEntry] = []
    for rule in rules:
        station = mapper.map_rule_to_station(rule)
        if station is None:
            continue
        mappings.append(StationMapEntry(market_id=rule.market_id, station=station))
    return mappings


def export_rulebook_bundle(output_dir: Path) -> Path:
    return export_rulebook(output_dir, build_sample_rules())


def export_station_map_bundle(output_dir: Path) -> Path:
    return export_station_map(output_dir, build_sample_stations(build_sample_rules()))


def run_bias_report_bundle(output_dir: Path) -> dict[str, Path | BiasSummary]:
    sample_rules = build_sample_rules()
    station_entries = build_sample_stations(sample_rules)
    station_by_market_id = {entry.market_id: entry.station for entry in station_entries}
    forecast_client = OpenMeteoForecastClient()
    official_obs_client = OfficialObservationFetcher()

    forecasts = []
    settlements = []
    scenario_by_market_id = {
        "poly-daily-high-central-park-001": {
            "settlement_date": date(2026, 6, 1),
            "forecast_value": 30.4,
            "settlement_value": 29.6,
            "issued_at": "2026-05-31T18:00:00Z",
        },
        "poly-daily-low-changi-001": {
            "settlement_date": date(2026, 1, 15),
            "forecast_value": 24.8,
            "settlement_value": 25.7,
            "issued_at": "2026-01-14T18:00:00Z",
        },
        "poly-daily-high-shanghai-001": {
            "settlement_date": date(2026, 4, 14),
            "forecast_value": 27.4,
            "settlement_value": 26.9,
            "issued_at": "2026-04-13T18:00:00Z",
        },
    }

    for rule in sample_rules:
        station = station_by_market_id[rule.market_id]
        scenario = scenario_by_market_id[rule.market_id]
        forecasts.append(
            forecast_client.fetch_forecast_stub(
                rule=rule,
                station=station,
                settlement_date=scenario["settlement_date"],
                predicted_temperature_c=scenario["forecast_value"],
                issued_at=scenario["issued_at"],
            )
        )
        settlements.append(
            official_obs_client.fetch_settlement_stub(
                rule=rule,
                station=station,
                settlement_date=scenario["settlement_date"],
                settled_temperature_c=scenario["settlement_value"],
            )
        )

    joined_records = join_forecasts_to_settlements(forecasts=forecasts, settlements=settlements)
    bias_rows = evaluate_bias(joined_records)
    bias_summary = summarize_bias_metrics(bias_rows)

    return {
        "report_path": export_bias_report(output_dir, bias_rows),
        "summary_path": export_bias_summary(output_dir, bias_summary),
        "summary": bias_summary,
    }


__all__ = [
    "build_sample_rules",
    "build_sample_stations",
    "export_rulebook_bundle",
    "export_station_map_bundle",
    "run_bias_report_bundle",
]
