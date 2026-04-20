import json

from typer.testing import CliRunner

from weather_execution_gateway import main as gateway_main
from weather_execution_gateway.advisory.manual_advisory import (
    ManualAdvisoryAuditStore,
    build_human_fill_record,
    build_manual_advisory_event,
)


def test_build_manual_advisory_event_marks_manual_order_only():
    event = build_manual_advisory_event(
        event_type="operator_acknowledged_manual_advisory",
        intent_id="intent_1",
        signal_id="sig_1",
        market_id="market_1",
        operator_user_id=123,
        payload={"decision": "approve_small"},
    )

    assert event["schema_version"] == "manual_advisory_event.v1"
    assert event["execution_mode"] == "manual_advisory"
    assert event["manual_order_required"] is True
    assert event["autonomous_execution_allowed"] is False
    assert event["intent_id"] == "intent_1"
    assert event["operator_user_id"] == 123


def test_manual_advisory_store_records_human_fill(tmp_path):
    audit_path = tmp_path / "manual_advisory_audit.jsonl"
    fills_path = tmp_path / "human_fills.jsonl"
    store = ManualAdvisoryAuditStore(audit_path=audit_path, fills_path=fills_path)
    fill = build_human_fill_record(
        intent_id="intent_1",
        signal_id="sig_1",
        market_id="market_1",
        side="buy",
        price=0.61,
        size=10.0,
        operator_user_id=123,
        notes="manual test",
    )

    saved_fills_path, saved_audit_path = store.record_human_fill(fill)

    assert saved_fills_path == fills_path
    assert saved_audit_path == audit_path
    saved_fill = json.loads(fills_path.read_text(encoding="utf-8").strip())
    saved_event = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert saved_fill["notional"] == 6.1
    assert saved_fill["source"] == "human_operator_reported"
    assert saved_event["event_type"] == "human_fill_reported"
    assert saved_event["payload"]["fill"]["fill_id"] == saved_fill["fill_id"]


def test_record_human_fill_cli_uses_configured_paths(monkeypatch, tmp_path):
    audit_path = tmp_path / "audit.jsonl"
    fills_path = tmp_path / "fills.jsonl"
    monkeypatch.setattr(gateway_main, "MANUAL_ADVISORY_AUDIT_PATH", audit_path)
    monkeypatch.setattr(gateway_main, "HUMAN_FILLS_PATH", fills_path)

    result = CliRunner().invoke(
        gateway_main.app,
        [
            "record-human-fill",
            "intent_1",
            "market_1",
            "buy",
            "0.61",
            "10",
            "--signal-id",
            "sig_1",
            "--operator-user-id",
            "123",
            "--notes",
            "manual test",
        ],
    )

    assert result.exit_code == 0
    assert "Human fill recorded" in result.output
    assert fills_path.exists()
    assert audit_path.exists()
    assert "human_fill_reported" in audit_path.read_text(encoding="utf-8")
