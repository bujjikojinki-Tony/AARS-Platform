from __future__ import annotations

import argparse
import json
from pathlib import Path

from weather_comparison_engine.settings import (
    FEATURE_STORE_SUMMARY_JSON,
    LABEL_COVERAGE_REPORT_JSON,
    MODEL_VALIDATION_REPORT_JSON,
    VALIDATION_FRESHNESS_STATUS_JSON,
    VALIDATION_OUTPUT_DIR,
)
from weather_comparison_engine.validation_assimilation import build_validation_assimilation_artifacts_from_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Build validation_summary.v1 once.")
    parser.add_argument("--scope-type", default="family")
    parser.add_argument("--scope-id", default="all")
    parser.add_argument("--output-dir", type=Path, default=VALIDATION_OUTPUT_DIR)
    args = parser.parse_args()

    artifacts = build_validation_assimilation_artifacts_from_files(
        scope_type=args.scope_type,
        scope_id=args.scope_id,
        validation_report_path=MODEL_VALIDATION_REPORT_JSON if MODEL_VALIDATION_REPORT_JSON.exists() else None,
        validation_freshness_path=VALIDATION_FRESHNESS_STATUS_JSON if VALIDATION_FRESHNESS_STATUS_JSON.exists() else None,
        label_coverage_path=LABEL_COVERAGE_REPORT_JSON if LABEL_COVERAGE_REPORT_JSON.exists() else None,
        feature_store_summary_path=FEATURE_STORE_SUMMARY_JSON if FEATURE_STORE_SUMMARY_JSON.exists() else None,
        output_dir=args.output_dir,
    )
    print(json.dumps(artifacts, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
