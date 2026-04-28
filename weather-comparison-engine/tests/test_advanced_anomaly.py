from __future__ import annotations

from pathlib import Path

from weather_comparison_engine.advanced_anomaly import (
    build_advanced_anomaly_outputs,
    write_advanced_anomaly_artifacts,
)


def test_advanced_anomaly_artifacts_written(tmp_path: Path) -> None:
    market_rows = [
        {
            "market_id": "1001",
            "market_family": "temperature_daily_max",
            "market_probability": 0.78,
            "fair_value": 0.62,
            "spread": 0.08,
            "liquidity": 80000,
            "one_sided_pressure": 0.4,
            "favored_side_flip_frequency": 0.1,
            "edge_dislocation": 0.16,
            "evidence_mismatch": True,
            "evidence_mismatch_score": 0.3,
            "location_name": "Shanghai",
            "target_date": "2026-04-24",
            "variable_name": "temperature_daily_max",
        },
        {
            "market_id": "1002",
            "market_family": "temperature_daily_max",
            "market_probability": 0.42,
            "fair_value": 0.48,
            "spread": 0.03,
            "liquidity": 100000,
            "one_sided_pressure": 0.1,
            "favored_side_flip_frequency": 0.0,
            "edge_dislocation": 0.06,
            "evidence_mismatch": False,
            "evidence_mismatch_score": 0.08,
            "location_name": "Hangzhou",
            "target_date": "2026-04-24",
            "variable_name": "temperature_daily_max",
        },
    ]
    comparison_history = [
        {"market_id": "1001", "market_family": "temperature_daily_max", "market_probability": 0.61},
        {"market_id": "1002", "market_family": "temperature_daily_max", "market_probability": 0.4},
    ]

    outputs = build_advanced_anomaly_outputs(
        market_rows=market_rows,
        comparison_history=comparison_history,
        probability_states={},
        source_policy_status={"overall_status": "healthy"},
        policy_refs={"anomaly_policy_ref": "threshold_policy.intervention_like_score.default.v1"},
    )

    assert outputs["schema_version"] == "advanced_anomaly_outputs.v1"
    assert outputs["market_events"]
    assert outputs["family_summaries"]
    assert outputs["market_events"][0]["schema_version"] == "market_anomaly_event.v2"

    paths = write_advanced_anomaly_artifacts(
        output_dir=tmp_path / "anomaly",
        market_rows=market_rows,
        comparison_history=comparison_history,
        probability_states={},
        source_policy_status={"overall_status": "healthy"},
        policy_refs={"anomaly_policy_ref": "threshold_policy.intervention_like_score.default.v1"},
    )

    assert any(path.name.startswith("market_anomaly_") and path.name.endswith("_v2.json") for path in paths.values())
    assert any(path.name.startswith("family_anomaly_summary_") for path in paths.values())
