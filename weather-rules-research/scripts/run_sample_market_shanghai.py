from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from weather_rules_research.backtest.band_eval import BandEvaluator, TemperatureBand
from weather_rules_research.backtest.joiner import ForecastSettlementJoiner
from weather_rules_research.models.forecast_snapshot import ForecastSnapshot
from weather_rules_research.official_obs.noaa_fetcher import NOAAFetcher
from weather_rules_research.official_obs.reconciler import OfficialObservationReconciler
from weather_rules_research.official_obs.wunderground import WundergroundHistoryHelper
from weather_rules_research.open_meteo.extractors import OpenMeteoExtractor
from weather_rules_research.open_meteo.forecast_client import OpenMeteoForecastClient
from weather_rules_research.outputs.export_bias_report import BiasReportExporter
from weather_rules_research.outputs.export_rulebook import export_rulebook
from weather_rules_research.outputs.export_station_map import export_station_map
from weather_rules_research.rules.assembler import RuleAssembler
from weather_rules_research.rules.question_parser import QuestionParser
from weather_rules_research.rules.rules_text_parser import RulesTextParser
from weather_rules_research.stations.mapper import StationMapper

RAW_DIR = BASE_DIR / "data" / "raw" / "market_rules"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "data" / "outputs"

MARKET_JSON = RAW_DIR / "sample_market_shanghai_001.json"
RULES_TXT = RAW_DIR / "sample_market_shanghai_001_rules.txt"
STATION_MAP_PATH = PROCESSED_DIR / "station_maps" / "manual_station_map.json"


def load_sample_inputs() -> tuple[dict, str]:
    market_payload = json.loads(MARKET_JSON.read_text(encoding="utf-8"))
    rules_text = RULES_TXT.read_text(encoding="utf-8")
    return market_payload, rules_text


def attach_station_ids_to_rule(rule, station):
    rule.station_name = station.station_name
    rule.nws_station_id = station.nws_station_id
    rule.cdo_station_id = station.cdo_station_id
    return rule


def build_offline_forecast_snapshot(rule, value: float = 29.0) -> ForecastSnapshot:
    return ForecastSnapshot(
        location_name=rule.location_name,
        forecast_issued_at=datetime.now(timezone.utc),
        target_date=rule.target_date or "UNKNOWN_DATE",
        variable_name=rule.variable_name,
        value=value,
        source="offline_stub:open_meteo",
    )


def build_offline_settlement_record(rule, station, official_value: float = 30.0):
    reconciler = OfficialObservationReconciler()
    wunderground_url = WundergroundHistoryHelper.build_history_url_for_station(station)
    payload = {
        "station_id": station.nws_station_id or station.cdo_station_id or "offline_station",
        "target_date": rule.target_date or "UNKNOWN_DATE",
        "variable_name": rule.variable_name,
        "official_value": official_value,
        "unit": "C",
        "source": "wunderground_history",
        "source_url": wunderground_url or "offline_stub",
        "raw_payload_ref": None,
        "quality_flag": None,
        "notes": "offline stub settlement payload aligned to Shanghai Pudong Wunderground history page",
    }
    return reconciler.to_settlement_record(payload), reconciler


def build_band_evaluator() -> BandEvaluator:
    bands = [
        TemperatureBand(label="26_or_below", upper=26.0),
        TemperatureBand(label="27", lower=26.0, upper=27.0, lower_inclusive=False),
        TemperatureBand(label="28", lower=27.0, upper=28.0, lower_inclusive=False),
        TemperatureBand(label="29_plus", lower=28.0, lower_inclusive=False, upper=None),
    ]
    return BandEvaluator(bands)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    market_payload, raw_rules_text = load_sample_inputs()
    market_id = market_payload["market_id"]
    question = market_payload["question"]

    print("=" * 80)
    print("SHANGHAI SAMPLE INPUT")
    print("Market ID:", market_id)
    print("Question :", question)
    print("Rules    :", raw_rules_text.strip())
    print("=" * 80)

    q_parser = QuestionParser()
    r_parser = RulesTextParser()
    assembler = RuleAssembler()

    q_result = q_parser.parse(question)
    r_result = r_parser.parse(raw_rules_text)

    rule = assembler.assemble(
        market_id=market_id,
        question=question,
        raw_rules_text=raw_rules_text,
        q_result=q_result,
        r_result=r_result,
    )

    print("PARSED RULE (PRE-MAPPING)")
    print(rule.model_dump())
    print("=" * 80)

    mapper = StationMapper(str(STATION_MAP_PATH))
    station = mapper.map_rule_to_station(rule)
    if station is None:
        raise RuntimeError("Station mapping failed for Shanghai sample")

    rule = attach_station_ids_to_rule(rule, station)

    print("STATION MAPPING")
    print(station.model_dump())
    print("=" * 80)

    export_rulebook(OUTPUT_DIR / "sample_rulebook_shanghai.json", [rule])
    export_station_map(OUTPUT_DIR / "sample_station_map_shanghai.json", [station])

    forecast_client = OpenMeteoForecastClient()
    try:
        forecast_payload = await forecast_client.fetch(
            latitude=station.latitude,
            longitude=station.longitude,
            hourly="temperature_2m",
        )
        extractor = OpenMeteoExtractor()
        extracted = extractor.extract_for_market_rule(
            payload=forecast_payload,
            target_date=rule.target_date or "UNKNOWN_DATE",
            variable_name=rule.variable_name,
        )

        if extracted.value is None:
            raise RuntimeError(
                f"Could not extract forecast value for {rule.target_date=} {rule.variable_name=}"
            )

        forecast_snapshot = ForecastSnapshot(
            location_name=rule.location_name,
            forecast_issued_at=datetime.now(timezone.utc),
            target_date=extracted.target_date,
            variable_name=extracted.variable_name,
            value=extracted.value,
            source=f"open-meteo:{extracted.source_path or extracted.source_mode}",
        )
    except Exception as exc:
        print("OPEN-METEO FORECAST FETCH FAILED, USING OFFLINE STUB")
        print(f"Reason: {exc}")
        print("=" * 80)
        forecast_snapshot = build_offline_forecast_snapshot(rule)

    print("FORECAST SNAPSHOT")
    print(forecast_snapshot.model_dump())
    print("=" * 80)

    noaa_fetcher = NOAAFetcher()
    reconciler = OfficialObservationReconciler()

    if not station.cdo_station_id:
        print("NO CDO STATION ID, USING OFFLINE STUB SETTLEMENT")
        print("=" * 80)
        daily_record, reconciler = build_offline_settlement_record(rule, station)
    else:
        try:
            daily_payload = await noaa_fetcher.fetch_daily_settlement_value(
                station_id=station.cdo_station_id,
                target_date=forecast_snapshot.target_date,
                variable_name=forecast_snapshot.variable_name,
            )
            daily_record = reconciler.to_settlement_record(daily_payload)
        except Exception as exc:
            print("DAILY SETTLEMENT FETCH FAILED, USING OFFLINE STUB")
            print(f"Reason: {exc}")
            print("=" * 80)
            daily_record, reconciler = build_offline_settlement_record(rule, station)

    print("DAILY SETTLEMENT RECORD")
    print(daily_record.model_dump())
    print("Settlement grade:", reconciler.is_settlement_grade(daily_record))
    print("Validation issues:", reconciler.validate_for_backtest(daily_record))
    print("=" * 80)

    if daily_record.official_value is None:
        print("Daily settlement value missing; skipping join/export.")
        return

    joiner = ForecastSettlementJoiner()
    joined = joiner.join(forecast_snapshot, daily_record)
    print("JOINED ROW")
    print(asdict(joined))
    print("=" * 80)

    exporter = BiasReportExporter(band_evaluator=build_band_evaluator())
    exporter.export_summary_report(
        OUTPUT_DIR / "sample_bias_report_shanghai.csv",
        joined_rows=[joined],
        drift_rows=[],
        stability_rows=[],
    )

    write_json(OUTPUT_DIR / "sample_joined_shanghai.json", asdict(joined))

    print("DONE. Shanghai sample artifacts written to:")
    print(OUTPUT_DIR / "sample_rulebook_shanghai.json")
    print(OUTPUT_DIR / "sample_station_map_shanghai.json")
    print(OUTPUT_DIR / "sample_joined_shanghai.json")
    print(OUTPUT_DIR / "sample_bias_report_shanghai.csv")


if __name__ == "__main__":
    asyncio.run(main())
