import sqlite3
from pathlib import Path


class SQLiteStore:
    def __init__(self, db_path: str = "data/outputs/weather_signal_engine.db") -> None:
        Path("data/outputs").mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.conn.cursor()

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS signal_events (
            signal_id TEXT PRIMARY KEY,
            market_id TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            location_name TEXT NOT NULL,
            target_date TEXT NOT NULL,
            variable_name TEXT NOT NULL,
            model_value REAL,
            model_band TEXT,
            market_band TEXT,
            edge_direction TEXT,
            edge_strength REAL,
            confidence_score REAL,
            confidence_level TEXT,
            action_hint TEXT,
            payload_json TEXT NOT NULL
        )
        """
        )

        self.conn.commit()
