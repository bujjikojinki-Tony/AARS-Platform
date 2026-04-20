from __future__ import annotations

import asyncio
import glob
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_weather_realtime import poll_once
from weather_rules_research.settings import REALTIME_MARKET_JSON, REALTIME_MARKET_SNAPSHOTS_GLOB


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_market_snapshots() -> list[dict]:
    snapshots: list[dict] = []
    seen: set[str] = set()

    candidate_paths = [Path(REALTIME_MARKET_JSON)]
    candidate_paths.extend(Path(path) for path in sorted(glob.glob(REALTIME_MARKET_SNAPSHOTS_GLOB)))

    for path in candidate_paths:
        if not path.exists():
            continue
        payload = _load_json(path)
        market_id = str(payload.get("market_id") or "")
        if not market_id or market_id in seen:
            continue
        seen.add(market_id)
        snapshots.append(payload)

    active_market_id = ""
    if snapshots:
        active_market_id = str(snapshots[0].get("market_id") or "")
    if active_market_id:
        snapshots.sort(key=lambda snapshot: str(snapshot.get("market_id") or "") == active_market_id)

    return snapshots


async def main() -> None:
    snapshots = _load_market_snapshots()
    if not snapshots:
        raise RuntimeError(
            f"No market snapshots found at {REALTIME_MARKET_JSON} or {REALTIME_MARKET_SNAPSHOTS_GLOB}"
        )

    results = []
    for snapshot in snapshots:
        result = await poll_once(live_market=snapshot)
        results.append(
            {
                "market_id": result.get("market_id"),
                "market_family": result.get("market_family"),
                "rule_status": result.get("rule_status"),
                "model_band": result.get("model_band"),
                "value": result.get("value"),
            }
        )

    print(json.dumps({"count": len(results), "results": results}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
