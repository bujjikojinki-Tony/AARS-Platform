from __future__ import annotations

import json

from weather_signal_engine.models.signal_event import SignalEvent
from weather_signal_engine.storage.sqlite import SQLiteStore


class SignalEventRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def save(self, signal: SignalEvent) -> None:
        cur = self.store.conn.cursor()
        payload = signal.model_dump()

        cur.execute(
            """
            INSERT OR REPLACE INTO signal_events (
                signal_id, market_id, signal_type, location_name, target_date, variable_name,
                model_value, model_band, market_band, edge_direction, edge_strength,
                confidence_score, confidence_level, action_hint, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal.signal_id,
                signal.market_id,
                signal.signal_type,
                signal.location_name,
                signal.target_date,
                signal.variable_name,
                signal.model_value,
                signal.model_band,
                signal.market_band,
                signal.edge_direction,
                signal.edge_strength,
                signal.confidence.score,
                signal.confidence.level,
                signal.action_hint,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        self.store.conn.commit()

    def list_all(self) -> list[SignalEvent]:
        rows = self.store.conn.execute(
            "SELECT payload_json FROM signal_events ORDER BY target_date, market_id"
        ).fetchall()
        return [SignalEvent.model_validate_json(row[0]) for row in rows]
