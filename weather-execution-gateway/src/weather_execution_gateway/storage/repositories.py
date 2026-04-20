from weather_execution_gateway.models.audit_event import AuditEvent
from weather_execution_gateway.models.execution_result import ExecutionResult
from weather_execution_gateway.storage.sqlite import SQLiteStore


class ExecutionResultRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def save(self, result: ExecutionResult) -> None:
        cur = self.store.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO execution_results (
                intent_id, status, mode, accepted, reason, simulated_order_id
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                result.intent_id,
                result.status,
                result.mode,
                int(result.accepted),
                result.reason,
                result.simulated_order_id,
            ),
        )
        self.store.conn.commit()


class AuditRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def save(self, event: AuditEvent) -> None:
        self.store.conn.execute(
            "INSERT OR REPLACE INTO audit_events (event_id, intent_id, event_type, payload_json) VALUES (?, ?, ?, ?)",
            (event.event_id, event.intent_id, event.event_type, event.payload_json),
        )
        self.store.conn.commit()
