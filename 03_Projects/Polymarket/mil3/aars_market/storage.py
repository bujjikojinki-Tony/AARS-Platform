from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator

from .models import Candle


_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS candles (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    open_time TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    source TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY (symbol, timeframe, open_time)
);

CREATE INDEX IF NOT EXISTS idx_candles_symbol_tf_time
ON candles(symbol, timeframe, open_time);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    requested_count INTEGER NOT NULL DEFAULT 0,
    upserted_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    error TEXT
);
"""


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


class MarketStore:
    """Small auditable SQLite store for normalized market candles.

    Writes are idempotent on (symbol, timeframe, open_time). Re-ingesting the
    same candle updates its values rather than creating duplicate history.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(_SCHEMA)

    def upsert_candles(self, candles: Iterable[Candle], source: str) -> int:
        rows = list(candles)
        if not rows:
            return 0
        now = _iso(datetime.now(timezone.utc))
        payload = [
            (
                c.symbol.upper(),
                c.timeframe,
                _iso(c.open_time),
                c.open,
                c.high,
                c.low,
                c.close,
                c.volume,
                source,
                now,
            )
            for c in rows
        ]
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT INTO candles(
                    symbol, timeframe, open_time, open, high, low, close, volume,
                    source, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, timeframe, open_time) DO UPDATE SET
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    close=excluded.close,
                    volume=excluded.volume,
                    source=excluded.source,
                    ingested_at=excluded.ingested_at
                """,
                payload,
            )
        return len(rows)

    def load_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Candle]:
        where = ["symbol = ?", "timeframe = ?"]
        params: list[object] = [symbol.upper(), timeframe]
        if start is not None:
            where.append("open_time >= ?")
            params.append(_iso(start))
        if end is not None:
            where.append("open_time <= ?")
            params.append(_iso(end))

        sql = f"""
            SELECT symbol, timeframe, open_time, open, high, low, close, volume
            FROM candles
            WHERE {' AND '.join(where)}
            ORDER BY open_time DESC
        """
        if limit is not None:
            if limit <= 0:
                raise ValueError("limit must be positive")
            sql += " LIMIT ?"
            params.append(limit)

        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        rows = list(reversed(rows))
        return [
            Candle(
                symbol=row["symbol"],
                timeframe=row["timeframe"],
                open_time=_parse(row["open_time"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            for row in rows
        ]

    def latest_open_time(self, symbol: str, timeframe: str) -> datetime | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT MAX(open_time) AS latest FROM candles WHERE symbol=? AND timeframe=?",
                (symbol.upper(), timeframe),
            ).fetchone()
        if row is None or row["latest"] is None:
            return None
        return _parse(row["latest"])

    def is_fresh(
        self,
        symbol: str,
        timeframe: str,
        *,
        now: datetime | None = None,
        max_age: timedelta = timedelta(hours=2),
    ) -> bool:
        latest = self.latest_open_time(symbol, timeframe)
        if latest is None:
            return False
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        age = current.astimezone(timezone.utc) - latest
        return timedelta(0) <= age <= max_age

    def count_candles(self, symbol: str, timeframe: str) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM candles WHERE symbol=? AND timeframe=?",
                (symbol.upper(), timeframe),
            ).fetchone()
        return int(row["n"])
