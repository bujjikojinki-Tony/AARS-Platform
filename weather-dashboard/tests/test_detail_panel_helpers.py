import pandas as pd

from weather_dashboard.ui.detail_panel import build_detail_state


def test_build_detail_state():
    df = pd.DataFrame([
        {
            "market_id": "sample_market_001",
            "market_question": "Highest temperature in Central Park on Apr 12?",
            "location_name": "Central Park",
            "target_date": "2026-04-12",
            "variable_name": "daily_max_temperature",
            "model_band": "28",
            "market_band": "27",
            "confidence_score": 0.9,
            "confidence_adjusted_gap": 0.9,
            "comparison_status": "mild_divergence",
            "action_hint": "approve_small",
        }
    ])

    detail = build_detail_state(df, "sample_market_001")

    assert detail is not None
    assert detail.market_id == "sample_market_001"
    assert detail.model_band == "28"
