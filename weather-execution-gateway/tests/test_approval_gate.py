from datetime import datetime, timedelta, timezone

from weather_execution_gateway.execution.approval_reader import ApprovalRecord
from weather_execution_gateway.risk.approval_gate import ApprovalGate


class FakeApprovalReader:
    def __init__(self, record):
        self.record = record

    def find_latest_by_intent_id(self, intent_id: str):
        return self.record

    def find_latest_by_signal_id(self, signal_id: str):
        return self.record


class FakeIntent:
    intent_id = "intent_001"
    signal_id = "sig_001"


def test_approval_gate_accepts_valid_approval():
    future = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

    record = ApprovalRecord(
        approval_id="a1",
        signal_id="sig_001",
        operator_user_id=123,
        decision="approve_small",
        expires_at=future,
        created_at=future,
        intent_id="intent_001",
        is_consumed=False,
    )

    gate = ApprovalGate(FakeApprovalReader(record))
    ok, reason, found = gate.validate(FakeIntent())

    assert ok is True
    assert reason is None
    assert found is not None


def test_approval_gate_rejects_expired_approval():
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

    record = ApprovalRecord(
        approval_id="a1",
        signal_id="sig_001",
        operator_user_id=123,
        decision="approve_small",
        expires_at=past,
        created_at=past,
        intent_id="intent_001",
        is_consumed=False,
    )

    gate = ApprovalGate(FakeApprovalReader(record))
    ok, reason, found = gate.validate(FakeIntent())

    assert ok is False
    assert reason == "approval_expired"
    assert found is not None


def test_approval_gate_rejects_consumed_approval():
    future = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

    record = ApprovalRecord(
        approval_id="a1",
        signal_id="sig_001",
        operator_user_id=123,
        decision="approve_small",
        expires_at=future,
        created_at=future,
        intent_id="intent_001",
        is_consumed=True,
    )

    gate = ApprovalGate(FakeApprovalReader(record))
    ok, reason, found = gate.validate(FakeIntent())

    assert ok is False
    assert reason == "approval_already_consumed"
    assert found is not None
