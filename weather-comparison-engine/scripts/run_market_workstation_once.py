from __future__ import annotations

import argparse
import json
from pathlib import Path

from weather_comparison_engine.market_workstation import (
    build_market_workstation_from_files,
    write_market_workstation_artifacts,
)
from weather_comparison_engine.settings import (
    COMPARISON_HISTORY_JSON,
    GATE_STACK_API_JSON,
    GATE_STACK_OPS_ALERTS_JSONL,
    LABEL_COVERAGE_REPORT_JSON,
    LATEST_DASHBOARD_ROWS_JSON,
    MARKET_ALERT_EVENTS_DIR,
    MARKET_ANOMALY_EVENTS_DIR,
    MARKET_WORKSTATION_OUTPUT_DIR,
    MODEL_VALIDATION_REPORT_JSON,
    OPPORTUNITY_BOARD_VIEW_JSON,
    REALTIME_FORECAST_JSON,
    REALTIME_FORECAST_SNAPSHOTS_GLOB,
    VALIDATION_FRESHNESS_STATUS_JSON,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build market_workstation_view.v1 once.")
    parser.add_argument("market_id", help="Selected market id.")
    parser.add_argument("--output-dir", default=str(MARKET_WORKSTATION_OUTPUT_DIR))
    args = parser.parse_args()

    view = build_market_workstation_from_files(
        market_id=args.market_id,
        latest_dashboard_rows_path=LATEST_DASHBOARD_ROWS_JSON,
        comparison_history_path=COMPARISON_HISTORY_JSON,
        forecast_snapshot_path=REALTIME_FORECAST_JSON,
        forecast_snapshots_glob=REALTIME_FORECAST_SNAPSHOTS_GLOB,
        gate_stack_api_path=GATE_STACK_API_JSON,
        opportunity_board_path=OPPORTUNITY_BOARD_VIEW_JSON,
        model_validation_report_path=MODEL_VALIDATION_REPORT_JSON,
        validation_freshness_status_path=VALIDATION_FRESHNESS_STATUS_JSON,
        label_coverage_report_path=LABEL_COVERAGE_REPORT_JSON,
        market_alert_events_dir=MARKET_ALERT_EVENTS_DIR,
        market_anomaly_events_dir=MARKET_ANOMALY_EVENTS_DIR,
        ops_alerts_jsonl_path=GATE_STACK_OPS_ALERTS_JSONL,
    )
    artifacts = write_market_workstation_artifacts(
        output_dir=Path(args.output_dir),
        market_id=args.market_id,
        view=view,
    )
    print(json.dumps({key: str(value) for key, value in artifacts.items()}, indent=2))


if __name__ == "__main__":
    main()
