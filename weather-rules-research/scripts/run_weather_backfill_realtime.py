from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_weather_backfill_once import _load_market_snapshots
from run_weather_realtime import FORECAST_REFRESH_INTERVAL_SECONDS, MARKET_CHECK_INTERVAL_SECONDS, poll_once


MAX_CYCLES = int(os.getenv("WEATHER_BACKFILL_MAX_CYCLES", "0"))


def _market_fingerprint(snapshot: dict) -> tuple[str, str, str]:
    return (
        str(snapshot.get("market_id") or ""),
        str(snapshot.get("market_question") or ""),
        str(snapshot.get("market_band_scheme") or ""),
    )


async def main() -> None:
    print("=" * 80)
    print("STARTING WEATHER BACKFILL REALTIME WORKER")
    print(f"Forecast refresh : {FORECAST_REFRESH_INTERVAL_SECONDS}s")
    print(f"Market check     : {MARKET_CHECK_INTERVAL_SECONDS}s")
    print(f"Max cycles       : {MAX_CYCLES or 'infinite'}")
    print("=" * 80)

    last_fingerprint_by_market: dict[str, tuple[str, str, str]] = {}
    last_refresh_at_by_market: dict[str, datetime] = {}
    cycle = 0

    while True:
        snapshots = _load_market_snapshots()
        if not snapshots:
            raise RuntimeError("No market snapshots found for weather backfill worker")

        results = []
        now = datetime.now(timezone.utc)
        for snapshot in snapshots:
            market_id = str(snapshot.get("market_id") or "")
            fingerprint = _market_fingerprint(snapshot)
            last_fingerprint = last_fingerprint_by_market.get(market_id)
            last_refresh_at = last_refresh_at_by_market.get(market_id)
            should_refresh = (
                last_fingerprint != fingerprint
                or last_refresh_at is None
                or (now - last_refresh_at).total_seconds() >= FORECAST_REFRESH_INTERVAL_SECONDS
            )

            if should_refresh:
                result = await poll_once(live_market=snapshot)
                last_fingerprint_by_market[market_id] = fingerprint
                last_refresh_at_by_market[market_id] = now
                results.append(
                    {
                        "market_id": result.get("market_id"),
                        "market_family": result.get("market_family"),
                        "rule_status": result.get("rule_status"),
                        "model_band": result.get("model_band"),
                        "value": result.get("value"),
                        "refreshed": True,
                    }
                )
            else:
                results.append(
                    {
                        "market_id": market_id,
                        "market_family": snapshot.get("market_family"),
                        "rule_status": "unchanged",
                        "model_band": None,
                        "value": None,
                        "refreshed": False,
                    }
                )

        cycle += 1
        print(
            json.dumps(
                {
                    "timestamp": now.isoformat(),
                    "cycle": cycle,
                    "count": len(results),
                    "results": results,
                },
                ensure_ascii=False,
            )
        )

        if MAX_CYCLES and cycle >= MAX_CYCLES:
            break

        await asyncio.sleep(MARKET_CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
