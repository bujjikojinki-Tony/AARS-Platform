from __future__ import annotations

from weather_execution_gateway.execution.approval_reader import ApprovalReader, ApprovalRecord
from weather_execution_gateway.models.order_intent import OrderIntent


class ApprovalGate:
    def __init__(self, reader: ApprovalReader) -> None:
        self.reader = reader

    def validate(self, intent: OrderIntent) -> tuple[bool, str | None, ApprovalRecord | None]:
        approval = None

        if intent.intent_id:
            approval = self.reader.find_latest_by_intent_id(intent.intent_id)

        if approval is None and intent.signal_id:
            approval = self.reader.find_latest_by_signal_id(intent.signal_id)

        if approval is None:
            return False, "approval_not_found", None

        if approval.is_consumed:
            return False, "approval_already_consumed", approval

        if approval.is_expired():
            return False, "approval_expired", approval

        return True, None, approval
