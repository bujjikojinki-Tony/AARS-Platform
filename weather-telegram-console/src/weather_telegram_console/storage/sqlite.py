from __future__ import annotations

import sqlite3
from pathlib import Path


class SQLiteStore:
    def __init__(self, db_path: str = "data/outputs/weather_telegram_console.db") -> None:
        Path("data/outputs").mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY,
                signal_id TEXT NOT NULL,
                operator_user_id INTEGER NOT NULL,
                decision TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                intent_id TEXT,
                is_consumed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self.conn.commit()
