from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ApprovalRecord:
    approval_id: str
    signal_id: str
    operator_user_id: int
    decision: str
    expires_at: str
    created_at: str
    intent_id: str | None
    is_consumed: bool

    def is_expired(self) -> bool:
        expires = datetime.fromisoformat(self.expires_at)
        now = datetime.now(timezone.utc)
        return expires <= now


class ApprovalReader:
    """
    Read approvals from weather-telegram-console SQLite DB.
    """

    def __init__(
        self,
        db_path: str | Path = "../weather-telegram-console/data/outputs/weather_telegram_console.db",
    ) -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Approval DB not found: {self.db_path}")
        return sqlite3.connect(str(self.db_path))

    def _fetch_latest(self, where_clause: str, value: str) -> ApprovalRecord | None:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT approval_id, signal_id, operator_user_id, decision,
                   expires_at, created_at, intent_id, is_consumed
            FROM approvals
            WHERE {where_clause}
              AND decision = 'approve_small'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (value,),
        )

        row = cur.fetchone()
        conn.close()

        if row is None:
            return None

        return ApprovalRecord(
            approval_id=row[0],
            signal_id=row[1],
            operator_user_id=row[2],
            decision=row[3],
            expires_at=row[4],
            created_at=row[5],
            intent_id=row[6],
            is_consumed=bool(row[7]),
        )

    def find_latest_by_signal_id(self, signal_id: str) -> ApprovalRecord | None:
        return self._fetch_latest("signal_id = ?", signal_id)

    def find_latest_by_intent_id(self, intent_id: str) -> ApprovalRecord | None:
        return self._fetch_latest("intent_id = ?", intent_id)

    def mark_consumed(self, approval_id: str) -> None:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE approvals
            SET is_consumed = 1
            WHERE approval_id = ?
            """,
            (approval_id,),
        )
        conn.commit()
        conn.close()
