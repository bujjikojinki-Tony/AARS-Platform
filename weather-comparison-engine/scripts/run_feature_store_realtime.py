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

from run_feature_store import main as run_feature_store_once
from weather_comparison_engine.settings import (
    FEATURE_STORE_MAX_CYCLES,
    FEATURE_STORE_REFRESH_INTERVAL_SECONDS,
    FEATURE_STORE_SUMMARY_JSON,
)


def _load_summary() -> dict | None:
    if not FEATURE_STORE_SUMMARY_JSON.exists():
        return None
    return json.loads(FEATURE_STORE_SUMMARY_JSON.read_text(encoding="utf-8"))


async def main() -> None:
    print("=" * 80)
    print("STARTING FEATURE STORE REALTIME WORKER")
    print(f"Refresh interval : {FEATURE_STORE_REFRESH_INTERVAL_SECONDS}s")
    print(f"Max cycles       : {FEATURE_STORE_MAX_CYCLES or 'infinite'}")
    print(f"Summary output   : {FEATURE_STORE_SUMMARY_JSON}")
    print("=" * 80)

    cycle = 0
    while True:
        run_feature_store_once()
        cycle += 1

        summary = _load_summary() or {}
        print(
            json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "cycle": cycle,
                    "tracked_rows": summary.get("tracked_rows"),
                    "labeled_rows": summary.get("labeled_rows"),
                    "label_counts": summary.get("label_counts"),
                },
                ensure_ascii=False,
            )
        )

        if FEATURE_STORE_MAX_CYCLES and cycle >= FEATURE_STORE_MAX_CYCLES:
            break

        await asyncio.sleep(FEATURE_STORE_REFRESH_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
