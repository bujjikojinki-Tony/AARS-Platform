from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from weather_comparison_engine.features import (
    HistoricalFeatureStoreBuilder,
    load_comparison_history,
    load_optional_json_records,
)
from weather_comparison_engine.settings import (
    COMPARISON_HISTORY_JSON,
    FEATURE_STORE_SUMMARY_JSON,
    FEATURE_STORE_TRAINING_SAMPLES_JSONL,
    OFFICIAL_HISTORY_JSONL,
    OFFICIAL_RECORDS_GLOB,
    RESOLVER_REPORT_JSON,
)


def main() -> None:
    if not COMPARISON_HISTORY_JSON.exists():
        raise FileNotFoundError(f"Missing comparison history: {COMPARISON_HISTORY_JSON}")

    comparison_rows = load_comparison_history(COMPARISON_HISTORY_JSON)
    resolver_report = None
    if RESOLVER_REPORT_JSON.exists():
        resolver_report = json.loads(RESOLVER_REPORT_JSON.read_text(encoding="utf-8"))

    if OFFICIAL_HISTORY_JSONL.exists():
        official_records = load_optional_json_records(OFFICIAL_HISTORY_JSONL)
    else:
        official_records = load_optional_json_records(OFFICIAL_RECORDS_GLOB)
    builder = HistoricalFeatureStoreBuilder()
    samples = builder.build_samples(
        comparison_rows=comparison_rows,
        resolver_report=resolver_report,
        official_records=official_records,
    )
    summary = builder.build_summary(samples)

    samples_path = builder.write_samples_jsonl(samples, FEATURE_STORE_TRAINING_SAMPLES_JSONL)
    summary_path = builder.write_summary(summary, FEATURE_STORE_SUMMARY_JSON)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Training samples written to {samples_path}")
    print(f"Feature store summary written to {summary_path}")


if __name__ == "__main__":
    main()
