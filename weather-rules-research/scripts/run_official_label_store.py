from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from weather_rules_research.climate_index import GlobalTemperatureIndexLoader
from weather_rules_research.official_obs.daily_fetcher import DailySettlementFetcher
from weather_rules_research.official_obs.station_settlement_backfill import StationSettlementBackfiller
from weather_rules_research.outputs import OfficialLabelStoreBuilder
from weather_rules_research.rules.live_market_resolver import load_rulebook
from weather_rules_research.sea_ice import SeaIceExtentLoader
from weather_rules_research.settings import (
    GLOBAL_TEMPERATURE_INDEX_JSON,
    OFFICIAL_HISTORY_JSONL,
    OFFICIAL_LABEL_SUMMARY_JSON,
    OFFICIAL_RECORDS_DIR,
    OFFICIAL_STATION_FETCH_ENABLED,
    RESOLVER_REPORT_JSON,
    SEA_ICE_EXTENT_JSON,
    RULEBOOK_JSON,
    STATION_OFFICIAL_SCENARIOS_JSON,
    STATION_SETTLEMENT_RECORDS_JSON,
)


async def main() -> None:
    if not RESOLVER_REPORT_JSON.exists():
        raise FileNotFoundError(f"Missing resolver report: {RESOLVER_REPORT_JSON}")

    resolver_report = json.loads(RESOLVER_REPORT_JSON.read_text(encoding="utf-8"))
    global_snapshot = None
    if GLOBAL_TEMPERATURE_INDEX_JSON.exists():
        global_snapshot = GlobalTemperatureIndexLoader().load(GLOBAL_TEMPERATURE_INDEX_JSON)

    sea_ice_snapshot = None
    if SEA_ICE_EXTENT_JSON.exists():
        sea_ice_snapshot = SeaIceExtentLoader().load(SEA_ICE_EXTENT_JSON)

    station_records: list[dict] = []
    if STATION_SETTLEMENT_RECORDS_JSON.exists():
        station_records = json.loads(STATION_SETTLEMENT_RECORDS_JSON.read_text(encoding="utf-8"))
    elif STATION_OFFICIAL_SCENARIOS_JSON.exists() and RULEBOOK_JSON.exists():
        scenarios = json.loads(STATION_OFFICIAL_SCENARIOS_JSON.read_text(encoding="utf-8"))
        station_records = await StationSettlementBackfiller(
            DailySettlementFetcher(token=os.getenv("CDO_TOKEN"))
        ).backfill_records(
            rules=load_rulebook(RULEBOOK_JSON),
            scenarios=scenarios,
            enable_fetch=OFFICIAL_STATION_FETCH_ENABLED,
        )

    builder = OfficialLabelStoreBuilder()
    records = builder.build_records(
        resolver_report=resolver_report,
        global_temperature_index_snapshot=global_snapshot,
        sea_ice_extent_snapshot=sea_ice_snapshot,
        station_records=station_records,
    )
    summary = builder.build_summary(records)

    written = builder.write_records(records, OFFICIAL_RECORDS_DIR)
    history_path, appended = builder.append_history_jsonl(records, OFFICIAL_HISTORY_JSONL)
    summary_path = builder.write_summary(summary, OFFICIAL_LABEL_SUMMARY_JSON)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Official records written: {len(written)} -> {OFFICIAL_RECORDS_DIR}")
    print(f"Official history updated at {history_path} (appended={appended})")
    print(f"Official label summary written to {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
