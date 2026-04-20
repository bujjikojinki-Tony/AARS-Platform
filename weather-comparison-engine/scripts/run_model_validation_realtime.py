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

from run_model_validation import main as run_model_validation_once
from weather_comparison_engine.settings import (
    MODEL_VALIDATION_MAX_CYCLES,
    MODEL_VALIDATION_REFRESH_INTERVAL_SECONDS,
    MODEL_VALIDATION_REPORT_JSON,
)


def _load_report() -> dict | None:
    if not MODEL_VALIDATION_REPORT_JSON.exists():
        return None
    return json.loads(MODEL_VALIDATION_REPORT_JSON.read_text(encoding="utf-8"))


async def main() -> None:
    print("=" * 80)
    print("STARTING MODEL VALIDATION REALTIME WORKER")
    print(f"Refresh interval : {MODEL_VALIDATION_REFRESH_INTERVAL_SECONDS}s")
    print(f"Max cycles       : {MODEL_VALIDATION_MAX_CYCLES or 'infinite'}")
    print(f"Report output    : {MODEL_VALIDATION_REPORT_JSON}")
    print("=" * 80)

    cycle = 0
    while True:
        run_model_validation_once()
        cycle += 1

        report = _load_report() or {}
        metrics = report.get("validation_metrics") or {}
        print(
            json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "cycle": cycle,
                    "sample_count": report.get("sample_count"),
                    "labeled_sample_count": report.get("labeled_sample_count"),
                    "brier_score": metrics.get("brier_score"),
                    "roi_backtest": metrics.get("roi_backtest"),
                },
                ensure_ascii=False,
            )
        )

        if MODEL_VALIDATION_MAX_CYCLES and cycle >= MODEL_VALIDATION_MAX_CYCLES:
            break

        await asyncio.sleep(MODEL_VALIDATION_REFRESH_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
