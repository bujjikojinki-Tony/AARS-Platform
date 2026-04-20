from polymarket_weather_ingest.ingest.market_snapshot_builder import MarketSnapshotBuilder


def test_market_snapshot_builder() -> None:
    builder = MarketSnapshotBuilder()
    bundle = builder.build_from_event(
        {
            "id": "event_001",
            "slug": "sample",
            "title": "Weather",
            "category": "weather",
            "active": True,
            "closed": False,
            "markets": [
                {
                    "id": "m1",
                    "question": "Will temperature reach 28C?",
                    "slug": "market-sample",
                    "volume24hr": "123.4",
                    "liquidity": "456.7",
                }
            ],
        }
    )

    assert bundle.market.market_id == "m1"
    assert bundle.market.market_slug == "market-sample"
    assert bundle.market.volume_24hr == 123.4
    assert bundle.price_state.notes == "MVP builder: metadata only, no CLOB price integration yet"
