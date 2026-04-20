import json

from weather_dashboard.loaders.market_realtime_snapshot_loader import (
    MarketRealtimeSnapshotLoader,
)


def test_market_realtime_snapshot_loader(tmp_path):
    path = tmp_path / "market_realtime_snapshot.json"
    path.write_text(
        json.dumps(
            {
                "updated_at": "2026-04-11T12:00:00+00:00",
                "asset_count": 1,
                "states": [
                    {
                        "asset_id": "123456",
                        "updated_at": "2026-04-11T12:00:00+00:00",
                        "event_type": "best_bid_ask",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    loader = MarketRealtimeSnapshotLoader()
    payload = loader.load(path)

    assert payload["asset_count"] == 1
    assert payload["states"][0]["asset_id"] == "123456"
