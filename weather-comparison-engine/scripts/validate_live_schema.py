from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from weather_comparison_engine.adapters.live_schema_validator import LiveSchemaValidator
from weather_comparison_engine.settings import (
    COMPARISON_HISTORY_JSON,
    REALTIME_FORECAST_JSON,
    REALTIME_MARKET_JSON,
    SCHEMA_VALIDATION_REPORT_JSON,
)


def main() -> None:
    validator = LiveSchemaValidator()
    report = validator.validate(
        market_path=REALTIME_MARKET_JSON,
        forecast_path=REALTIME_FORECAST_JSON,
        comparison_history_path=COMPARISON_HISTORY_JSON,
    )
    validator.write_report(report, SCHEMA_VALIDATION_REPORT_JSON)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Schema validation report written to {SCHEMA_VALIDATION_REPORT_JSON}")

    if report["status"] != "valid":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

