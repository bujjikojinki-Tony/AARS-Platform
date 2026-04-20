from polymarket_weather_ingest.realtime_registry import RealtimeRegistry


def test_build_asset_registry() -> None:
    registry = RealtimeRegistry().build_asset_registry(
        [
            {
                "id": "evt_1",
                "title": "Highest temperature in Central Park on Apr 12?",
                "markets": [
                    {
                        "id": "mkt_1",
                        "question": "Highest temperature in Central Park on Apr 12?",
                        "slug": "highest-temperature-in-central-park-on-apr-12",
                        "outcomeTokenIds": ["yes_1", "no_1"],
                    }
                ],
            }
        ]
    )

    assert len(registry) == 1
    assert registry[0]["market_id"] == "mkt_1"
    assert registry[0]["yes_asset_id"] == "yes_1"
    assert registry[0]["no_asset_id"] == "no_1"
