from __future__ import annotations

import json
from datetime import datetime, timezone

from typer.testing import CliRunner

from weather_telegram_console.integrations.ops_alert_bridge import (
    sync_ops_alerts_to_notification_queue,
)
from weather_telegram_console.integrations.ops_notification_dispatcher import (
    ack_ops_notification,
    dispatch_ops_notifications,
)
from weather_telegram_console.ops_bridge_cli import app


def test_sync_ops_alerts_to_notification_queue_deduplicates(tmp_path) -> None:
    alerts_path = tmp_path / "gate_stack_ops_alerts.jsonl"
    state_path = tmp_path / "ops_alert_bridge_state.json"
    queue_path = tmp_path / "telegram_ops_notifications.jsonl"

    alert = {
        "schema_version": "gate_stack_ops_alert.v1",
        "event_type": "gate_stack_runtime_alert",
        "event_at": "2026-04-19T12:00:00+00:00",
        "severity": "high",
        "automation_signal": "red",
        "market_id": "m-1",
        "primary_block_reason": "stale_worker",
        "recommended_operator_action": "refresh_pipeline_inputs",
        "block_reasons": ["stale_worker"],
    }
    alerts_path.write_text(
        json.dumps(alert, ensure_ascii=False) + "\n" + json.dumps(alert, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    first = sync_ops_alerts_to_notification_queue(
        alerts_path=alerts_path,
        state_path=state_path,
        queue_path=queue_path,
        max_batch=10,
    )
    second = sync_ops_alerts_to_notification_queue(
        alerts_path=alerts_path,
        state_path=state_path,
        queue_path=queue_path,
        max_batch=10,
    )
    alerts_path.write_text(
        json.dumps(
            {
                **alert,
                "event_at": "2026-04-19T12:31:00+00:00",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    third = sync_ops_alerts_to_notification_queue(
        alerts_path=alerts_path,
        state_path=state_path,
        queue_path=queue_path,
        max_batch=10,
    )

    assert first["queued"] == 1
    assert second["queued"] == 0
    assert second["suppressed"] == 2
    assert third["queued"] == 1
    assert third["queue_path"] == str(queue_path)
    lines = [line for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2
    payload = json.loads(lines[0])
    assert payload["schema_version"] == "telegram_ops_notification.v1"
    assert payload["status"] == "pending"
    assert payload["delivery_state"] == "pending"
    assert payload["dedupe_key"]
    assert payload["cooldown_until"]
    assert "AARS OPS ALERT" in payload["text"]


def test_ops_bridge_cli_sync_gate_alerts(monkeypatch, tmp_path) -> None:
    alerts_path = tmp_path / "gate_stack_ops_alerts.jsonl"
    state_path = tmp_path / "ops_alert_bridge_state.json"
    queue_path = tmp_path / "telegram_ops_notifications.jsonl"
    alerts_path.write_text(
        json.dumps(
            {
                "schema_version": "gate_stack_ops_alert.v1",
                "event_type": "gate_stack_runtime_alert",
                "event_at": "2026-04-19T12:00:00+00:00",
                "severity": "high",
                "automation_signal": "red",
                "market_id": "m-2",
                "primary_block_reason": "resolver_not_matched",
                "recommended_operator_action": "review_resolver_contract",
                "block_reasons": ["resolver_not_matched"],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("GATE_STACK_OPS_ALERTS_JSONL", str(alerts_path))
    monkeypatch.setenv("OPS_ALERT_BRIDGE_STATE_JSON", str(state_path))
    monkeypatch.setenv("TELEGRAM_OPS_NOTIFICATIONS_JSONL", str(queue_path))

    result = CliRunner().invoke(app, ["sync-gate-alerts", "--max-batch", "5"])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["queued"] == 1
    assert queue_path.exists()


def test_dispatch_and_ack_ops_notifications(tmp_path) -> None:
    queue_path = tmp_path / "telegram_ops_notifications.jsonl"
    delivery_log = tmp_path / "telegram_ops_delivery_log.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": "telegram_ops_notification.v1",
                "notification_id": "ops_1",
                "status": "pending",
                "channel": "telegram_ops_bridge",
                "text": "alert 1",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    dispatch_report = dispatch_ops_notifications(
        queue_path=queue_path,
        delivery_log_path=delivery_log,
        max_batch=10,
        dry_run=False,
    )
    assert dispatch_report["dispatched_count"] == 1
    assert dispatch_report["queue_summary"]["delivery_state_counts"]["sent"] == 1
    lines = [line for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = json.loads(lines[0])
    assert payload["status"] == "sent"
    assert "sent_at" in payload

    ack_report = ack_ops_notification(
        queue_path=queue_path,
        delivery_log_path=delivery_log,
        notification_id="ops_1",
        acked_by="tester",
    )
    assert ack_report["acked"] is True
    assert ack_report["queue_summary"]["delivery_state_counts"]["acked"] == 1
    lines = [line for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = json.loads(lines[0])
    assert payload["status"] == "acked"
    assert payload["acked_by"] == "tester"
    assert payload["delivery_state"] == "acked"
    assert delivery_log.exists()


def test_ops_bridge_cli_dispatch_and_ack(monkeypatch, tmp_path) -> None:
    queue_path = tmp_path / "telegram_ops_notifications.jsonl"
    delivery_log = tmp_path / "telegram_ops_delivery_log.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": "telegram_ops_notification.v1",
                "notification_id": "ops_2",
                "status": "pending",
                "channel": "telegram_ops_bridge",
                "text": "alert 2",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TELEGRAM_OPS_NOTIFICATIONS_JSONL", str(queue_path))
    monkeypatch.setenv("TELEGRAM_OPS_DELIVERY_LOG_JSONL", str(delivery_log))

    dispatch_result = CliRunner().invoke(app, ["dispatch-ops-queue", "--max-batch", "5"])
    assert dispatch_result.exit_code == 0
    dispatch_payload = json.loads(dispatch_result.stdout)
    assert dispatch_payload["dispatched_count"] == 1

    ack_result = CliRunner().invoke(app, ["ack-ops", "--notification-id", "ops_2", "--acked-by", "ops_user"])
    assert ack_result.exit_code == 0
    ack_payload = json.loads(ack_result.stdout)
    assert ack_payload["acked"] is True


def test_ops_bridge_cli_queue_status(monkeypatch, tmp_path) -> None:
    queue_path = tmp_path / "telegram_ops_notifications.jsonl"
    queue_path.write_text(
        json.dumps(
            {
                "schema_version": "telegram_ops_notification.v1",
                "notification_id": "ops_3",
                "status": "sent",
                "delivery_state": "sent",
                "channel": "telegram_ops_bridge",
                "text": "alert 3",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TELEGRAM_OPS_NOTIFICATIONS_JSONL", str(queue_path))

    result = CliRunner().invoke(app, ["ops-queue-status"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "telegram_ops_queue_summary.v1"
    assert payload["delivery_state_counts"]["sent"] == 1
