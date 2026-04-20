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

from weather_rules_research.official_obs.daily_fetcher import DailySettlementFetcher
from weather_rules_research.official_obs.station_settlement_backfill import (
    StationSettlementBackfiller,
    build_station_backfill_summary,
)
from weather_rules_research.rules.live_market_resolver import load_rulebook
from weather_rules_research.settings import (
    OFFICIAL_STATION_FETCH_ENABLED,
    RULEBOOK_JSON,
    STATION_OFFICIAL_SCENARIOS_JSON,
    STATION_SETTLEMENT_RECORDS_JSON,
    STATION_SETTLEMENT_SUMMARY_JSON,
)


def write_json(path: Path, payload: dict | list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


async def main() -> None:
    if not RULEBOOK_JSON.exists():
        raise FileNotFoundError(f"Missing rulebook: {RULEBOOK_JSON}")

    if not STATION_OFFICIAL_SCENARIOS_JSON.exists():
        raise FileNotFoundError(
            f"Missing station official scenarios: {STATION_OFFICIAL_SCENARIOS_JSON}"
        )

    scenarios = json.loads(STATION_OFFICIAL_SCENARIOS_JSON.read_text(encoding="utf-8"))
    rules = load_rulebook(RULEBOOK_JSON)

    records = await StationSettlementBackfiller(
        DailySettlementFetcher(token=os.getenv("CDO_TOKEN"))
    ).backfill_records(
        rules=rules,
        scenarios=scenarios,
        enable_fetch=OFFICIAL_STATION_FETCH_ENABLED,
    )

    summary = build_station_backfill_summary(
        records,
        fetch_enabled=OFFICIAL_STATION_FETCH_ENABLED,
    )

    records_path = write_json(STATION_SETTLEMENT_RECORDS_JSON, records)
    summary_path = write_json(STATION_SETTLEMENT_SUMMARY_JSON, summary)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Station settlement records written to {records_path}")
    print(f"Station settlement summary written to {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
