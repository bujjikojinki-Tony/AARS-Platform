from uuid import uuid4

from backend.models.core import AuditLogEvent
from backend.models.enums import ExecutionMode


SAFE_MODES = {
    ExecutionMode.OBSERVE_ONLY.value,
    ExecutionMode.SIMULATION.value,
    ExecutionMode.PAPER_TRADE.value,
}


class RuleRegistry:
    def __init__(self, repository):
        self.repository = repository

    def get_rules(self) -> dict:
        return self.repository.get_rules()

    def update_rules(self, updates: dict) -> dict:
        for key, value in updates.items():
            self.repository.set_rule(key, str(value))
            self.repository.save_audit_log(
                AuditLogEvent(
                    event_id=f"evt_{uuid4().hex[:10]}",
                    event_type="RULE_UPDATED",
                    object_type="RuleConfig",
                    object_id=key,
                    payload={"value": value},
                )
            )
        return self.get_rules()

    def get_mode(self) -> str:
        return self.repository.get_mode()

    def set_mode(self, mode: str) -> str:
        if mode == ExecutionMode.LIVE_EXECUTE.value:
            self.repository.save_audit_log(
                AuditLogEvent(
                    event_id=f"evt_{uuid4().hex[:10]}",
                    event_type="MODE_CHANGE_REJECTED",
                    object_type="SystemState",
                    object_id="execution_mode",
                    payload={"requested_mode": mode},
                )
            )
            raise ValueError("LIVE_EXECUTE is not allowed in PWB-01")
        if mode not in SAFE_MODES:
            raise ValueError(f"Unsupported mode: {mode}")
        self.repository.set_mode(mode)
        self.repository.save_audit_log(
            AuditLogEvent(
                event_id=f"evt_{uuid4().hex[:10]}",
                event_type="MODE_CHANGED",
                object_type="SystemState",
                object_id="execution_mode",
                payload={"mode": mode},
            )
        )
        return mode
