import pandas as pd

from weather_dashboard.utils.dataframe_utils import safe_sort_dashboard_rows, available_sort_columns


def test_safe_sort_dashboard_rows():
    df = pd.DataFrame([
        {"market_id": "m1", "confidence_adjusted_gap": 0.5},
        {"market_id": "m2", "confidence_adjusted_gap": 1.2},
    ])

    sorted_df = safe_sort_dashboard_rows(df, "confidence_adjusted_gap", ascending=False)
    assert sorted_df.iloc[0]["market_id"] == "m2"


def test_available_sort_columns():
    df = pd.DataFrame([
        {"market_id": "m1", "confidence_adjusted_gap": 0.5, "confidence_score": 0.7}
    ])

    cols = available_sort_columns(df)
    assert "confidence_adjusted_gap" in cols
    assert "confidence_score" in cols

