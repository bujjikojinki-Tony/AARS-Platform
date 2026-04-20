import sqlite3
from pathlib import Path


class SQLiteStore:
    def __init__(self, db_path: str = "data/outputs/polymarket_weather_ingest.db") -> None:
        Path("data/outputs").mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS weather_market_bundles (
                market_id TEXT PRIMARY KEY,
                event_id TEXT,
                event_title TEXT,
                market_question TEXT,
                market_slug TEXT,
                category TEXT,
                active INTEGER,
                closed INTEGER,
                volume_24hr REAL,
                liquidity REAL,
                favored_outcome TEXT,
                favored_probability REAL,
                implied_band TEXT,
                notes TEXT
            )
            """
        )

        self.conn.commit()
