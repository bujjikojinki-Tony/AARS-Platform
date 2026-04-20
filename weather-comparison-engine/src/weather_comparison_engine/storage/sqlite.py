import sqlite3
from pathlib import Path


class SQLiteStore:
    def __init__(self, db_path: str = "data/outputs/weather_comparison_engine.db") -> None:
        Path("data/outputs").mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS comparison_rows (
                market_id TEXT PRIMARY KEY,
                market_question TEXT,
                location_name TEXT NOT NULL,
                target_date TEXT NOT NULL,
                variable_name TEXT NOT NULL,
                model_band TEXT,
                market_band TEXT,
                band_distance INTEGER NOT NULL,
                confidence_score REAL NOT NULL,
                confidence_adjusted_gap REAL NOT NULL,
                comparison_status TEXT NOT NULL,
                action_hint TEXT NOT NULL
            )
            """
        )

        self.conn.commit()
