import json

from weather_comparison_engine.ingest.realtime_market_loader import RealtimeMarketLoader


def test_realtime_market_loader(tmp_path):
    path = tmp_path / "market_realtime_snapshot.json"
    path.write_text(
        json.dumps(
            {
                "market_id": "sample_market_001",
                "updated_at": "2026-04-11T12:00:00+00:00",
                "market_band": "27",
                "market_probability": 0.63,
            }
        ),
        encoding="utf-8",
    )

    loader = RealtimeMarketLoader()
    payload = loader.load(path)

    assert payload["market_id"] == "sample_market_001"
    assert payload["market_band"] == "27"
