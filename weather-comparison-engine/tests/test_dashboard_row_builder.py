from weather_comparison_engine.outputs.dashboard_row_builder import (
    build_latest_dashboard_row,
    normalize_market_target_date,
)


def test_normalize_market_target_date_from_question_text() -> None:
    assert normalize_market_target_date("Highest temperature in Shanghai on April 20?") == "Apr 20"


def test_build_latest_dashboard_row_prefers_question_date() -> None:
    row = build_latest_dashboard_row(
        market_snapshot={
            "market_id": "m-1",
            "market_question": "Highest temperature in Shanghai on April 20?",
            "location_name": "Shanghai",
        },
        forecast_snapshot={
            "market_id": "m-1",
            "target_date": "Apr 14",
            "variable_name": "daily_max_temperature",
        },
        point={
            "model_value": 17.8,
            "model_band": "18",
            "market_band": "20",
            "band_scheme": "temperature_integer",
            "market_band_scheme": "temperature_integer",
            "comparison_status": "unmatched_rule",
        },
    )

    assert row["target_date"] == "Apr 20"
    assert row["target_date_source"] == "market_question"
    assert row["question_target_date"] == "Apr 20"


def test_build_latest_dashboard_row_derives_market_probability_from_prices() -> None:
    row = build_latest_dashboard_row(
        market_snapshot={
            "market_id": "m-2",
            "market_question": "Will Shanghai exceed 35C?",
            "yes_price": 0.63,
            "no_price": 0.37,
        },
        forecast_snapshot={
            "market_id": "m-2",
            "variable_name": "daily_max_temperature",
        },
        point={},
    )

    assert row["market_probability"] == 0.63
