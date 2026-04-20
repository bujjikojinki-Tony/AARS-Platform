import pandas as pd

from weather_dashboard.ui.market_snapshots_panel import filter_market_watchlist_frame


def test_filter_market_watchlist_frame_applies_resolver_edge_and_freshness_filters():
    frame = pd.DataFrame(
        [
            {
                "market_family": "temperature",
                "resolver_status": "matched",
                "edge_bucket": "positive",
                "freshness_bucket": "fresh",
                "market_question": "A",
            },
            {
                "market_family": "temperature",
                "resolver_status": "unmatched",
                "edge_bucket": "blocked",
                "freshness_bucket": "stale",
                "market_question": "B",
            },
        ]
    )

    filtered = filter_market_watchlist_frame(
        frame,
        query="",
        family="temperature",
        resolver_status="matched",
        edge_bucket="positive",
        freshness_bucket="fresh",
    )

    assert len(filtered) == 1
    assert filtered.iloc[0]["market_question"] == "A"


def test_filter_market_watchlist_frame_applies_query():
    frame = pd.DataFrame(
        [
            {
                "market_family": "temperature",
                "resolver_status": "matched",
                "edge_bucket": "positive",
                "freshness_bucket": "fresh",
                "market_question": "Shanghai temperature",
                "market_id": "m1",
            },
            {
                "market_family": "sea_ice_extent",
                "resolver_status": "matched",
                "edge_bucket": "flat",
                "freshness_bucket": "warm",
                "market_question": "Sea ice extent",
                "market_id": "m2",
            },
        ]
    )

    filtered = filter_market_watchlist_frame(
        frame,
        query="shanghai",
        family="All",
        resolver_status="All",
        edge_bucket="All",
        freshness_bucket="All",
    )

    assert len(filtered) == 1
    assert filtered.iloc[0]["market_id"] == "m1"
