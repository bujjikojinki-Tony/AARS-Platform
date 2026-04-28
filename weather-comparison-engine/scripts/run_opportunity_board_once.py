from __future__ import annotations

import argparse
import json
from pathlib import Path

from weather_comparison_engine.opportunity_board import build_opportunity_board_view
from weather_comparison_engine.opportunity_board import load_opportunity_policy_bundle
from weather_comparison_engine.opportunity_board import write_opportunity_board_artifacts
from weather_comparison_engine.status import load_optional_json
from weather_comparison_engine.settings import (
    LATEST_DASHBOARD_ROWS_JSON,
    MODEL_VALIDATION_REPORT_JSON,
    OPPORTUNITY_BOARD_CANONICAL_EXPLANATIONS_JSON,
    OPPORTUNITY_BOARD_CANONICAL_FEATURE_ROWS_JSON,
    OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON,
    OPPORTUNITY_BOARD_CITY_DIR,
    OPPORTUNITY_BOARD_EXPLANATIONS_JSON,
    OPPORTUNITY_BOARD_FEATURE_ROWS_JSON,
    OPPORTUNITY_BOARD_SUMMARY_JSON,
    OPPORTUNITY_BOARD_VIEW_JSON,
    OPPORTUNITY_SEED_LIST_JSON,
    SOURCE_POLICY_STATUS_JSON,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build opportunity_board_view.v1 once.")
    parser.add_argument("--seed-file", type=Path, default=OPPORTUNITY_SEED_LIST_JSON)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--city", default=None)
    parser.add_argument("--family", default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    context = {
        "model_validation_report": load_optional_json(MODEL_VALIDATION_REPORT_JSON)
        if MODEL_VALIDATION_REPORT_JSON.exists()
        else {},
        "source_policy_status": load_optional_json(SOURCE_POLICY_STATUS_JSON)
        if SOURCE_POLICY_STATUS_JSON.exists()
        else {},
        "opportunity_seed_list": load_optional_json(args.seed_file) if args.seed_file.exists() else {},
        "opportunity_policy_bundle": load_opportunity_policy_bundle(),
    }
    rows = load_optional_json(LATEST_DASHBOARD_ROWS_JSON) or []
    if args.city or args.family:
        rows = [
            row for row in rows
            if _matches(row, city=args.city, family=args.family)
        ]
    payload = build_opportunity_board_view(latest_dashboard_rows=rows, context=context)
    if args.limit is not None:
        payload["rows"] = payload.get("rows", [])[: max(args.limit, 0)]
        payload["row_count"] = len(payload["rows"])
        payload["explanations"] = {
            row.get("row_id"): payload.get("explanations", {}).get(row.get("row_id"))
            for row in payload["rows"]
            if row.get("row_id")
        }
        payload["feature_rows"] = payload.get("feature_rows", [])[: max(args.limit, 0)]

    if args.output_dir is not None:
        board_path = args.output_dir / "opportunity_board_view.json"
        explanation_path = args.output_dir / "opportunity_explanations.json"
        feature_rows_path = args.output_dir / "opportunity_feature_rows.json"
        summary_path = args.output_dir / "opportunity_board_summary.json"
    else:
        board_path = OPPORTUNITY_BOARD_VIEW_JSON
        explanation_path = OPPORTUNITY_BOARD_EXPLANATIONS_JSON
        feature_rows_path = OPPORTUNITY_BOARD_FEATURE_ROWS_JSON
        summary_path = OPPORTUNITY_BOARD_SUMMARY_JSON

    artifacts = write_opportunity_board_artifacts(
        board_path=board_path,
        explanation_path=explanation_path,
        feature_rows_path=feature_rows_path,
        city_dir=OPPORTUNITY_BOARD_CITY_DIR if args.output_dir is None else args.output_dir / "cities",
        payload=payload,
        summary_path=summary_path,
        canonical_board_path=OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON if args.output_dir is None else None,
        canonical_explanation_path=OPPORTUNITY_BOARD_CANONICAL_EXPLANATIONS_JSON if args.output_dir is None else None,
        canonical_feature_rows_path=OPPORTUNITY_BOARD_CANONICAL_FEATURE_ROWS_JSON if args.output_dir is None else None,
    )
    print(json.dumps({key: str(value) for key, value in artifacts.items() if key != "city_files"}, indent=2))


def _matches(row: dict, *, city: str | None, family: str | None) -> bool:
    if city and str(row.get("city") or row.get("location_name") or "").lower() != city.lower():
        return False
    if family and str(row.get("market_family") or "").lower() != family.lower():
        return False
    return True


if __name__ == "__main__":
    main()
