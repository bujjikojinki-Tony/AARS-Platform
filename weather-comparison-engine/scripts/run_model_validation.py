from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from weather_comparison_engine.settings import (
    BACKTEST_EDGE_THRESHOLD,
    BACKTEST_REPORT_JSON,
    CALIBRATION_REPORT_JSON,
    FEATURE_STORE_TRAINING_SAMPLES_JSONL,
    MODEL_VALIDATION_BUCKET_COUNT,
    MODEL_VALIDATION_REPORT_JSON,
)
from weather_comparison_engine.validation import (
    build_model_validation_report,
    load_training_samples_jsonl,
)


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> None:
    samples = load_training_samples_jsonl(FEATURE_STORE_TRAINING_SAMPLES_JSONL)
    calibration_report, backtest_report, validation_report = build_model_validation_report(
        samples,
        calibration_bucket_count=MODEL_VALIDATION_BUCKET_COUNT,
        edge_threshold=BACKTEST_EDGE_THRESHOLD,
    )

    calibration_path = _write_json(CALIBRATION_REPORT_JSON, calibration_report)
    backtest_path = _write_json(BACKTEST_REPORT_JSON, backtest_report)
    validation_path = _write_json(MODEL_VALIDATION_REPORT_JSON, validation_report)

    print(json.dumps(validation_report, indent=2, ensure_ascii=False))
    print(f"Calibration report written to {calibration_path}")
    print(f"Backtest report written to {backtest_path}")
    print(f"Model validation report written to {validation_path}")


if __name__ == "__main__":
    main()
