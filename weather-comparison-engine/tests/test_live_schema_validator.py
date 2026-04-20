from __future__ import annotations

import json

from weather_comparison_engine.adapters.live_schema_validator import LiveSchemaValidator
from weather_comparison_engine.schemas import ComparisonPoint, ForecastSnapshot, MarketSnapshot


def test_market_snapshot_schema_accepts_current_simple_shape():
    snapshot = MarketSnapshot.model_validate(
        {
            "market_id": "sample_market_001",
            "market_question": "Highest temperature in Central Park on Apr 12?",
            "location_name": "Central Park",
            "updated_at": "2026-04-11T12:00:00+00:00",
            "market_band": "27",
            "market_probability": 0.63,
        }
    )

    assert snapshot.schema_version == "market_snapshot.v1"
    assert snapshot.market_id == "sample_market_001"
    assert snapshot.market_probability == 0.63


def test_forecast_snapshot_schema_accepts_current_shape():
    snapshot = ForecastSnapshot.model_validate(
        {
            "timestamp": "2026-04-11T12:00:00+00:00",
            "market_id": "sample_market_001",
            "target_date": "2026-04-12",
            "variable_name": "daily_max_temperature",
            "value": 28.1,
            "model_band": "28",
            "confidence_score": 0.91,
            "source_mode": "daily.temperature_2m_max",
        }
    )

    assert snapshot.schema_version == "forecast_snapshot.v1"
    assert snapshot.market_id == "sample_market_001"
    assert snapshot.value == 28.1


def test_comparison_point_schema_accepts_current_history_shape():
    point = ComparisonPoint.model_validate(
        {
            "timestamp": "2026-04-13T06:42:24.602412+00:00",
            "market_id": "sample_market_001",
            "model_value": 28.1,
            "model_band": "28",
            "market_band": "28",
            "confidence_score": 0.91,
            "confidence_adjusted_gap": 0.0,
            "comparison_status": "aligned",
            "action_hint": "watch",
            "market_snapshot_ref": "2026-04-11T12:00:00+00:00",
            "forecast_snapshot_ref": "2026-04-11T12:00:00+00:00",
        }
    )

    assert point.schema_version == "comparison_point.v1"
    assert point.comparison_status == "aligned"


def test_live_schema_validator_writes_valid_report(tmp_path):
    market_path = tmp_path / "market.json"
    forecast_path = tmp_path / "forecast.json"
    history_path = tmp_path / "comparison_history.json"
    report_path = tmp_path / "schema_validation_report.json"

    market_path.write_text(
        json.dumps({"market_id": "m1", "market_probability": 0.62}),
        encoding="utf-8",
    )
    forecast_path.write_text(
        json.dumps({"market_id": "m1", "value": 28.1}),
        encoding="utf-8",
    )
    history_path.write_text(
        json.dumps(
            [
                {
                    "timestamp": "2026-04-17T00:00:00+00:00",
                    "market_id": "m1",
                    "comparison_status": "aligned",
                }
            ]
        ),
        encoding="utf-8",
    )

    validator = LiveSchemaValidator()
    report = validator.validate(
        market_path=market_path,
        forecast_path=forecast_path,
        comparison_history_path=history_path,
    )
    validator.write_report(report, report_path)

    saved = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved["status"] == "valid"
    assert saved["sections"]["market_snapshot"]["market_id"] == "m1"
    assert saved["sections"]["comparison_history"]["row_count"] == 1

