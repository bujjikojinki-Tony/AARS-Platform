import json

from weather_comparison_engine.ingest.realtime_forecast_loader import RealtimeForecastLoader


def test_realtime_forecast_loader_load_many(tmp_path):
    path1 = tmp_path / "forecast_realtime_snapshot_m1.json"
    path2 = tmp_path / "forecast_realtime_snapshot_m2.json"
    path1.write_text(
        json.dumps({"market_id": "m1", "timestamp": "2026-04-11T12:00:00+00:00"}),
        encoding="utf-8",
    )
    path2.write_text(
        json.dumps({"market_id": "m2", "timestamp": "2026-04-11T12:01:00+00:00"}),
        encoding="utf-8",
    )

    loader = RealtimeForecastLoader()
    payload = loader.load_many(tmp_path / "forecast_realtime_snapshot_*.json")

    assert len(payload) == 2
    assert payload[0]["market_id"] == "m2"
