from polymarket_weather_ingest.models.weather_market_bundle import WeatherMarketBundle
from polymarket_weather_ingest.storage.sqlite import SQLiteStore


class WeatherMarketBundleRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def save(self, bundle: WeatherMarketBundle) -> None:
        cur = self.store.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO weather_market_bundles (
                market_id, event_id, event_title, market_question, market_slug,
                category, active, closed, volume_24hr, liquidity,
                favored_outcome, favored_probability, implied_band, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bundle.market.market_id,
                bundle.market.event_id,
                bundle.market.event_title,
                bundle.market.market_question,
                bundle.market.market_slug,
                bundle.market.category,
                int(bundle.market.active) if bundle.market.active is not None else None,
                int(bundle.market.closed) if bundle.market.closed is not None else None,
                bundle.market.volume_24hr,
                bundle.market.liquidity,
                bundle.price_state.favored_outcome,
                bundle.price_state.favored_probability,
                bundle.price_state.implied_band,
                bundle.price_state.notes,
            ),
        )
        self.store.conn.commit()
