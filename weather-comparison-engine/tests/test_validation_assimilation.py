from __future__ import annotations

import json
from pathlib import Path

from weather_comparison_engine.validation_assimilation import (
    build_validation_assimilation_artifacts_from_files,
)


def test_validation_assimilation_artifacts_written(tmp_path: Path) -> None:
    validation_report_path = tmp_path / "model_validation_report.json"
    validation_freshness_path = tmp_path / "validation_freshness_status.json"
    label_coverage_path = tmp_path / "label_coverage_report.json"
    feature_store_summary_path = tmp_path / "feature_store_summary.json"

    validation_report_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-04-23T00:00:00+00:00",
                "model_id": "heuristic_shadow_probability_v1",
                "model_type": "probability_shadow",
                "validation_metrics": {
                    "brier_score": 0.2,
                    "market_baseline_brier_score": 0.3,
                },
                "promotion_reason": "validation_strong",
                "family_rollout_summary": {"support_level": "strong"},
                "governance_summary": {
                    "canonical_ratio": 0.9,
                    "source_policy_coverage": 0.88,
                    "normalization_coverage": 0.91,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    validation_freshness_path.write_text(
        json.dumps({"status": "healthy", "freshness_seconds": 900}, indent=2),
        encoding="utf-8",
    )
    label_coverage_path.write_text(
        json.dumps({"status": "healthy", "labeled_ratio": 0.86, "official_record_coverage": 0.72}, indent=2),
        encoding="utf-8",
    )
    feature_store_summary_path.write_text(
        json.dumps(
            {
                "source_policy_coverage": 0.88,
                "forecast_coverage": 0.8,
                "observation_coverage": 0.77,
                "freshness_reliability": 0.93,
                "source_precision_reliability": 0.82,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    artifacts = build_validation_assimilation_artifacts_from_files(
        scope_type="family",
        scope_id="temperature_daily_max",
        validation_report_path=validation_report_path,
        validation_freshness_path=validation_freshness_path,
        label_coverage_path=label_coverage_path,
        feature_store_summary_path=feature_store_summary_path,
        output_dir=tmp_path / "validation",
        policy_refs={"source_policy_ref": "source_policy_registry.json"},
        upstream_refs={"feature_store_ref": "training_samples.jsonl"},
    )

    assert artifacts["validation_summary"]["schema_version"] == "validation_summary.v1"
    assert artifacts["validation_summary"]["promotion_readiness"] in {"ready", "conditional", "not_ready"}
    assert artifacts["coverage_summary"]["schema_version"] == "coverage_summary.v1"
    assert artifacts["promotion_support"]["schema_version"] == "promotion_decision_support.v1"
    assert artifacts["model_validation_compare"]["schema_version"] == "model_validation_compare.v1"
    assert (tmp_path / "validation" / "validation_summary_temperature_daily_max.json").exists()
    assert (tmp_path / "validation" / "coverage_summary_temperature_daily_max.json").exists()
    assert (tmp_path / "validation" / "promotion_support_temperature_daily_max.json").exists()
    assert (tmp_path / "validation" / "model_validation_compare_temperature_daily_max.json").exists()
