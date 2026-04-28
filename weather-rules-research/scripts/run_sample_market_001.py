from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

from weather_rules_research.backtest.band_eval import BandEvaluator, TemperatureBand
from weather_rules_research.backtest.drift_eval import ForecastDriftRow
from weather_rules_research.backtest.joiner import ForecastSettlementJoiner
from weather_rules_research.backtest.stability_eval import StabilityRow
from weather_rules_research.models.forecast_snapshot import ForecastSnapshot
from weather_rules_research.official_obs.noaa_fetcher import NOAAFetcher
from weather_rules_research.official_obs.reconciler import OfficialObservationReconciler
from weather_rules_research.open_meteo.extractors import OpenMeteoExtractor
from weather_rules_research.open_meteo.forecast_client import OpenMeteoForecastClient
from weather_rules_research.outputs.export_bias_report import BiasReportExporter
from weather_rules_research.outputs.export_rulebook import export_rulebook
from weather_rules_research.outputs.export_station_map import export_station_map
from weather_rules_research.rules.assembler import RuleAssembler
from weather_rules_research.rules.question_parser import QuestionParser
from weather_rules_research.rules.rules_text_parser import RulesTextParser
from weather_rules_research.stations.mapper import StationMapper

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw" / "market_rules"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "data" / "outputs"

MARKET_JSON = RAW_DIR / "sample_market_001.json"
RULES_TXT = RAW_DIR / "sample_market_001_rules.txt"
STATION_MAP_PATH = PROCESSED_DIR / "station_maps" / "manual_station_map.json"


def load_sample_inputs() -> tuple[dict, str]:
    market_payload = json.loads(MARKET_JSON.read_text(encoding="utf-8"))
    rules_text = RULES_TXT.read_text(encoding="utf-8")
    return market_payload, rules_text


def build_band_evaluator() -> BandEvaluator:
    bands = [
        TemperatureBand(label="26_or_below", upper=26.0),
        TemperatureBand(label="27", lower=26.0, upper=27.0, lower_inclusive=False),
        TemperatureBand(label="28", lower=27.0, upper=28.0, lower_inclusive=False),
        TemperatureBand(label="29_plus", lower=28.0, lower_inclusive=False, upper=None),
    ]
    return BandEvaluator(bands)


def attach_station_ids_to_rule(rule, station):
    """
    Write mapped station IDs back into the rule object so the rulebook export
    reflects the real station mapping result.
    """
    rule.station_name = station.station_name
    rule.nws_station_id = station.nws_station_id
    rule.cdo_station_id = station.cdo_station_id
    return rule


def build_offline_forecast_snapshot(rule, value: float = 28.1) -> ForecastSnapshot:
    return ForecastSnapshot(
        location_name=rule.location_name,
        forecast_issued_at=datetime.utcnow(),
        target_date=rule.target_date or "UNKNOWN_DATE",
        variable_name=rule.variable_name,
        value=value,
        source="offline_stub:open_meteo",
    )


def build_offline_settlement_record(rule, station, official_value: float = 27.0):
    reconciler = OfficialObservationReconciler()
    payload = {
        "station_id": station.nws_station_id or station.cdo_station_id or "offline_station",
        "target_date": rule.target_date or "UNKNOWN_DATE",
        "variable_name": rule.variable_name,
        "official_value": official_value,
        "unit": "C",
        "source": "ncei_cdo_daily",
        "source_url": "offline_stub",
        "raw_payload_ref": None,
        "quality_flag": None,
        "notes": "offline stub settlement payload",
    }
    return reconciler.to_settlement_record(payload), reconciler


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load raw sample
    market_payload, raw_rules_text = load_sample_inputs()
    market_id = market_payload["market_id"]
    question = market_payload["question"]

    print("=" * 80)
    print("1) RAW INPUT")
    print("Market ID:", market_id)
    print("Question :", question)
    print("Rules    :", raw_rules_text.strip())
    print("=" * 80)

    # 2. Parse question + rules
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

    print("2) PARSED RULE (PRE-MAPPING)")
    print(rule.model_dump())
    print("=" * 80)

    # 3. Map rule to station
    mapper = StationMapper(str(STATION_MAP_PATH))
    station = mapper.map_rule_to_station(rule)

    if station is None:
        raise RuntimeError("Station mapping failed")

    rule = attach_station_ids_to_rule(rule, station)

    print("3) STATION MAPPING")
    print(station.model_dump())
    print("=" * 80)

    print("4) RULE (POST-MAPPING)")
    print(rule.model_dump())
    print("=" * 80)

    # 4. Export rulebook / station map snapshot
    export_rulebook(OUTPUT_DIR / "sample_rulebook.json", [rule])
    export_station_map(OUTPUT_DIR / "sample_station_map.json", [station])

    # 5. Fetch Open-Meteo forecast, with offline fallback.
    forecast_client = OpenMeteoForecastClient()
    try:
        forecast_payload = await forecast_client.fetch(
            latitude=station.latitude,
            longitude=station.longitude,
            hourly="temperature_2m",
        )
        print("5) OPEN-METEO FORECAST FETCHED")
        print("Keys:", list(forecast_payload.keys()))
        print("=" * 80)

        # 6. Extract target-date forecast value
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
            forecast_issued_at=datetime.utcnow(),
            target_date=extracted.target_date,
            variable_name=extracted.variable_name,
            value=extracted.value,
            source=f"open-meteo:{extracted.source_path or extracted.source_mode}",
        )
    except Exception as exc:
        print("5) OPEN-METEO FORECAST FETCH FAILED, USING OFFLINE STUB")
        print(f"Reason: {exc}")
        print("=" * 80)
        forecast_snapshot = build_offline_forecast_snapshot(rule)

    print("6) FORECAST SNAPSHOT")
    print(forecast_snapshot.model_dump())
    print("=" * 80)

    # 7. Fetch official daily settlement value (preferred)
    noaa_fetcher = NOAAFetcher()
    reconciler = OfficialObservationReconciler()

    if not station.cdo_station_id:
        raise RuntimeError("Missing cdo_station_id for settlement-grade fetch")

    try:
        daily_payload = await noaa_fetcher.fetch_daily_settlement_value(
            station_id=station.cdo_station_id,
            target_date=forecast_snapshot.target_date,
            variable_name=forecast_snapshot.variable_name,
        )
        daily_record = reconciler.to_settlement_record(daily_payload)
    except Exception as exc:
        print("7) DAILY SETTLEMENT FETCH FAILED, USING OFFLINE STUB")
        print(f"Reason: {exc}")
        print("=" * 80)
        daily_record, reconciler = build_offline_settlement_record(rule, station)

    print("7) DAILY SETTLEMENT RECORD")
    print(daily_record.model_dump())
    print("Settlement grade:", reconciler.is_settlement_grade(daily_record))
    print("Validation issues:", reconciler.validate_for_backtest(daily_record))
    print("=" * 80)

    # 8. Fetch recent observation (secondary context only)
    latest_record = None
    if station.nws_station_id:
        try:
            latest_payload = await noaa_fetcher.fetch_recent_observation_nws(station.nws_station_id)
            latest_record = reconciler.to_settlement_record(latest_payload)

            print("8) LATEST OBSERVATION RECORD")
            print(latest_record.model_dump())
            print("Settlement grade:", reconciler.is_settlement_grade(latest_record))
            print("Validation issues:", reconciler.validate_for_backtest(latest_record))
            print("=" * 80)
        except Exception as exc:
            print("8) LATEST OBSERVATION FETCH FAILED, SKIPPING")
            print(f"Reason: {exc}")
            print("=" * 80)

    # 9. Join forecast vs daily settlement
    if daily_record.official_value is None:
        print("Daily settlement value missing; skipping join/export of joined bias rows.")
        return

    joiner = ForecastSettlementJoiner()
    joined = joiner.join(forecast_snapshot, daily_record)

    print("9) JOINED ROW")
    print(joined)
    print("=" * 80)

    # 10. Build drift/stability sample rows
    drift_rows = [
        ForecastDriftRow(
            forecast_issued_date="2026-04-07",
            target_date=joined.target_date,
            lead_days=5,
            forecast_value=joined.forecast_value + 0.5,
            official_value=joined.official_value,
        ),
        ForecastDriftRow(
            forecast_issued_date="2026-04-09",
            target_date=joined.target_date,
            lead_days=3,
            forecast_value=joined.forecast_value + 0.2,
            official_value=joined.official_value,
        ),
        ForecastDriftRow(
            forecast_issued_date="2026-04-11",
            target_date=joined.target_date,
            lead_days=1,
            forecast_value=joined.forecast_value,
            official_value=joined.official_value,
        ),
    ]

    stability_rows = [
        StabilityRow(
            group_key=f"{rule.location_name}-sample",
            forecast_value=joined.forecast_value,
            official_value=joined.official_value,
        ),
        StabilityRow(
            group_key=f"{rule.location_name}-sample",
            forecast_value=joined.forecast_value + 0.2,
            official_value=joined.official_value,
        ),
        StabilityRow(
            group_key=f"{rule.location_name}-sample",
            forecast_value=joined.forecast_value - 0.3,
            official_value=joined.official_value,
        ),
    ]

    # 11. Export reports
    exporter = BiasReportExporter(
        band_evaluator=build_band_evaluator(),
    )

    exporter.export_summary_report(
        path=OUTPUT_DIR / "sample_forecast_bias_summary.csv",
        joined_rows=[joined],
        drift_rows=drift_rows,
        stability_rows=stability_rows,
    )

    exporter.export_drift_detail_report(
        path=OUTPUT_DIR / "sample_forecast_drift_detail.csv",
        drift_rows=drift_rows,
    )

    exporter.export_stability_detail_report(
        path=OUTPUT_DIR / "sample_forecast_stability_detail.csv",
        stability_rows=stability_rows,
    )

    print("10) OUTPUT FILES")
    print(OUTPUT_DIR / "sample_rulebook.json")
    print(OUTPUT_DIR / "sample_station_map.json")
    print(OUTPUT_DIR / "sample_forecast_bias_summary.csv")
    print(OUTPUT_DIR / "sample_forecast_drift_detail.csv")
    print(OUTPUT_DIR / "sample_forecast_stability_detail.csv")
    print("=" * 80)
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())
