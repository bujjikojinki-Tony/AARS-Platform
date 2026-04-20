from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from weather_telegram_console.storage.sqlite import SQLiteStore


class ApprovalRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def create_approval(
        self,
        signal_id: str,
        operator_user_id: int,
        decision: str,
        ttl_minutes: int = 15,
        intent_id: str | None = None,
    ) -> dict:
        approval_id = f"approval_{uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=ttl_minutes)

        cur = self.store.conn.cursor()
        cur.execute(
            """
            INSERT INTO approvals (
                approval_id, signal_id, operator_user_id, decision,
                expires_at, created_at, intent_id, is_consumed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                approval_id,
                signal_id,
                operator_user_id,
                decision,
                expires_at.isoformat(),
                now.isoformat(),
                intent_id,
                0,
            ),
        )
        self.store.conn.commit()

        return {
            "approval_id": approval_id,
            "signal_id": signal_id,
            "operator_user_id": operator_user_id,
            "decision": decision,
            "expires_at": expires_at.isoformat(),
            "created_at": now.isoformat(),
            "intent_id": intent_id,
            "is_consumed": False,
        }

    def attach_intent_id(self, approval_id: str, intent_id: str) -> None:
        cur = self.store.conn.cursor()
        cur.execute(
            """
            UPDATE approvals
            SET intent_id = ?
            WHERE approval_id = ?
            """,
            (intent_id, approval_id),
        )
        self.store.conn.commit()

    def find_active_approval(self, signal_id: str) -> dict | None:
        now = datetime.now(timezone.utc).isoformat()

        cur = self.store.conn.cursor()
        cur.execute(
            """
            SELECT approval_id, signal_id, operator_user_id, decision,
                   expires_at, created_at, intent_id, is_consumed
            FROM approvals
            WHERE signal_id = ?
              AND decision = 'approve_small'
              AND is_consumed = 0
              AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (signal_id, now),
        )

        row = cur.fetchone()
        if row is None:
            return None

        return {
            "approval_id": row[0],
            "signal_id": row[1],
            "operator_user_id": row[2],
            "decision": row[3],
            "expires_at": row[4],
            "created_at": row[5],
            "intent_id": row[6],
            "is_consumed": bool(row[7]),
        }

    def find_latest_approval(self, signal_id: str) -> dict | None:
        cur = self.store.conn.cursor()
        cur.execute(
            """
            SELECT approval_id, signal_id, operator_user_id, decision,
                   expires_at, created_at, intent_id, is_consumed
            FROM approvals
            WHERE signal_id = ?
              AND decision = 'approve_small'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (signal_id,),
        )

        row = cur.fetchone()
        if row is None:
            return None

        return {
            "approval_id": row[0],
            "signal_id": row[1],
            "operator_user_id": row[2],
            "decision": row[3],
            "expires_at": row[4],
            "created_at": row[5],
            "intent_id": row[6],
            "is_consumed": bool(row[7]),
        }

    def get_signal_approval_status(self, signal_id: str) -> dict[str, str | None]:
        record = self.find_latest_approval(signal_id)
        if record is None:
            return {"status": "未审批", "expires_at": None, "approval_id": None}

        expires_at = datetime.fromisoformat(record["expires_at"])
        now = datetime.now(timezone.utc)

        if record["is_consumed"]:
            status = "已消费"
        elif expires_at <= now:
            status = "已过期"
        else:
            status = "已审批"

        return {
            "status": status,
            "expires_at": record["expires_at"],
            "approval_id": record["approval_id"],
        }

    def mark_consumed(self, approval_id: str) -> None:
        cur = self.store.conn.cursor()
        cur.execute(
            """
            UPDATE approvals
            SET is_consumed = 1
            WHERE approval_id = ?
            """,
            (approval_id,),
        )
        self.store.conn.commit()
