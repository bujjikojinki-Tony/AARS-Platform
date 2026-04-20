import json

from weather_dashboard.loaders.timeseries_loader import TimeSeriesLoader


def test_timeseries_loader(tmp_path):
    path = tmp_path / "timeseries.json"
    path.write_text(
        json.dumps([
            {
                "timestamp": "2026-04-11T00:00:00",
                "market_id": "sample_market_001",
                "model_value": 28.1
            }
        ]),
        encoding="utf-8",
    )

    loader = TimeSeriesLoader()
    df = loader.load_df(path)

    assert len(df) == 1
    assert df.iloc[0]["market_id"] == "sample_market_001"
