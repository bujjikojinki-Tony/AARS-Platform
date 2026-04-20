import json

from weather_dashboard.loaders.comparison_history_loader import ComparisonHistoryLoader


def test_comparison_history_loader(tmp_path):
    path = tmp_path / "history.json"
    path.write_text(
        json.dumps(
            [
                {
                    "timestamp": "2026-04-11T00:00:00",
                    "market_id": "sample_market_001",
                    "confidence_adjusted_gap": 0.0,
                }
            ]
        ),
        encoding="utf-8",
    )

    loader = ComparisonHistoryLoader()
    df = loader.load_df(path)

    assert len(df) == 1
    assert df.iloc[0]["market_id"] == "sample_market_001"
