from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_station_settlement_backfill import main as run_station_settlement_backfill_once
from weather_rules_research.settings import (
    STATION_SETTLEMENT_MAX_CYCLES,
    STATION_SETTLEMENT_RECORDS_JSON,
    STATION_SETTLEMENT_REFRESH_INTERVAL_SECONDS,
    STATION_SETTLEMENT_SUMMARY_JSON,
)


def _load_summary() -> dict | None:
    if not STATION_SETTLEMENT_SUMMARY_JSON.exists():
        return None
    return json.loads(STATION_SETTLEMENT_SUMMARY_JSON.read_text(encoding="utf-8"))


def _load_records() -> list[dict]:
    if not STATION_SETTLEMENT_RECORDS_JSON.exists():
        return []
    payload = json.loads(STATION_SETTLEMENT_RECORDS_JSON.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


async def main() -> None:
    print("=" * 80)
    print("STARTING STATION SETTLEMENT BACKFILL REALTIME WORKER")
    print(f"Refresh interval : {STATION_SETTLEMENT_REFRESH_INTERVAL_SECONDS}s")
    print(f"Max cycles       : {STATION_SETTLEMENT_MAX_CYCLES or 'infinite'}")
    print(f"Records output   : {STATION_SETTLEMENT_RECORDS_JSON}")
    print(f"Summary output   : {STATION_SETTLEMENT_SUMMARY_JSON}")
    print("=" * 80)

    cycle = 0
    while True:
        await run_station_settlement_backfill_once()
        cycle += 1

        summary = _load_summary() or {}
        records = _load_records()
        print(
            json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "cycle": cycle,
                    "record_count": len(records),
                    "fetch_enabled": summary.get("fetch_enabled"),
                    "source_counts": summary.get("source_counts"),
                },
                ensure_ascii=False,
            )
        )

        if STATION_SETTLEMENT_MAX_CYCLES and cycle >= STATION_SETTLEMENT_MAX_CYCLES:
            break

        await asyncio.sleep(STATION_SETTLEMENT_REFRESH_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
