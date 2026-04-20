from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

import yaml

from weather_execution_gateway import main as gateway_main
from weather_execution_gateway.audit.logger import AuditLogger
from weather_execution_gateway.storage.sqlite import SQLiteStore


def test_consume_first_pending_moves_and_processes_files(monkeypatch, tmp_path) -> None:
    pending_dir = tmp_path / "pending_intents"
    consumed_dir = tmp_path / "consumed_intents"
    output_dir = tmp_path / "outputs"
    pending_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    approval_db_path = tmp_path / "weather_telegram_console.db"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=15)
    conn = sqlite3.connect(str(approval_db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS approvals (
            approval_id TEXT PRIMARY KEY,
            signal_id TEXT NOT NULL,
            operator_user_id INTEGER NOT NULL,
            decision TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            intent_id TEXT,
            is_consumed INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        INSERT INTO approvals (
            approval_id, signal_id, operator_user_id, decision,
            expires_at, created_at, intent_id, is_consumed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "approval_1",
            "sig_1",
            123,
            "approve_small",
            expires_at.isoformat(),
            now.isoformat(),
            "intent_1",
            0,
        ),
    )
    conn.commit()
    conn.close()

    risk_path = tmp_path / "risk_limits.yaml"
    whitelist_path = tmp_path / "whitelist_markets.yaml"
    risk_path.write_text(
        yaml.safe_dump(
            {
                "execution": {"enabled": True},
                "exposure": {
                    "max_notional_per_market": 100,
                    "max_total_notional": 500,
                },
            }
        ),
        encoding="utf-8",
    )
    whitelist_path.write_text(
        yaml.safe_dump({"markets": ["sample_market_001"]}),
        encoding="utf-8",
    )

    intent_path = pending_dir / "intent_1.json"
    intent_path.write_text(
        json.dumps(
            {
                "schema_version": "execution_intent.v1",
                "intent_id": "intent_1",
                "market_id": "sample_market_001",
                "signal_id": "sig_1",
                "decision_ref": "decision_intent_1",
                "authorization_ref": "approval_1",
                "side": "buy",
                "price": 0.42,
                "size": 10,
                "post_only": True,
                "max_slippage_pct": 0.02,
                "approved": True,
                "probability_mode": "live_approved",
                "execution_constraint": "live_execution_allowed",
                "calibration_status": "calibrated",
                "contract_version": "probability_contract.v1",
                "probability_contract": {
                    "contract_version": "probability_contract.v1",
                    "probability_mode": "live_approved",
                    "calibration_status": "calibrated",
                    "execution_constraint": "live_execution_allowed",
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(gateway_main, "PENDING_INTENTS_DIR", pending_dir)
    monkeypatch.setattr(gateway_main, "APPROVAL_DB_PATH", approval_db_path)
    monkeypatch.setattr(gateway_main, "RISK_LIMITS_PATH", risk_path)
    monkeypatch.setattr(gateway_main, "WHITELIST_PATH", whitelist_path)
    monkeypatch.setattr(gateway_main, "UNIFIED_STATUS_PATH", tmp_path / "missing_unified_status.json")
    monkeypatch.setattr(gateway_main, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(
        gateway_main,
        "SQLiteStore",
        lambda: SQLiteStore(db_path=str(tmp_path / "weather_execution_gateway.db")),
    )
    monkeypatch.setattr(
        gateway_main,
        "AuditLogger",
        lambda: AuditLogger(path=str(tmp_path / "audit_log.jsonl")),
    )

    gateway_main.consume_first_pending()

    assert not intent_path.exists()
    assert (consumed_dir / "intent_1.json").exists()
    assert (tmp_path / "audit_log.jsonl").exists()

    conn = sqlite3.connect(str(approval_db_path))
    row = conn.execute(
        "SELECT is_consumed FROM approvals WHERE approval_id = ?",
        ("approval_1",),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == 1
