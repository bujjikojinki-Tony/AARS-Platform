import asyncio

from polymarket_weather_ingest.market_state_reducer import MarketStateReducer


def test_market_state_reducer_updates_snapshot() -> None:
    reducer = MarketStateReducer()

    asyncio.run(
        reducer.on_event(
            {
                "asset_id": "yes_1",
                "event_type": "book",
                "best_bid": "0.48",
                "best_ask": "0.52",
            }
        )
    )

    snapshot = reducer.snapshot()
    assert len(snapshot) == 1
    assert snapshot[0]["asset_id"] == "yes_1"
    assert snapshot[0]["best_bid"] == "0.48"
