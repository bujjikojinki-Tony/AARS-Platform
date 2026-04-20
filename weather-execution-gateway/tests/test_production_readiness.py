import sqlite3
from datetime import datetime, timedelta, timezone

from weather_execution_gateway.risk.production_readiness import ProductionReadinessChecker
from weather_execution_gateway.risk.production_readiness import load_latest_approval_probe


def test_production_readiness_blocks_default_dry_run_config():
    report = ProductionReadinessChecker().evaluate(
        risk_config={
            "execution": {"enabled": False, "require_approval": True, "mode": "dry_run"},
            "exposure": {"max_notional_per_market": 100, "max_total_notional": 500},
            "safety": {"kill_switch_enabled": True},
        },
        execution_modes={"modes": ["dry_run", "live_disabled"]},
        whitelist_config={"markets": ["sample_market_001"]},
        model_validation_report={
            "approved_for_live": False,
            "deployment_mode": "shadow",
            "calibration_status": "not_calibrated",
        },
        approval_probe={"approval_valid": True},
        live_mode_policy={
            "policy": {
                "enabled": False,
                "allow_live_execution": False,
                "approved_by": [],
                "min_approver_count": 2,
                "expires_at": None,
            },
            "required_checks": {"kill_switch": True},
        },
        position_exposure={
            "snapshot_available": True,
            "market_notional": 0.0,
            "total_notional": 0.0,
            "total_position_count": 0,
        },
        clob_adapter_ready=False,
    )

    assert report["ready_for_live"] is False
    assert report["status"] == "blocked"
    blocked_names = {check["name"] for check in report["checks"] if check["status"] == "blocked"}
    assert "execution_enabled" in blocked_names
    assert "live_mode_policy" in blocked_names
    assert "model_validation" in blocked_names
    assert "clob_adapter" in blocked_names


def test_production_readiness_passes_when_all_live_requirements_are_met():
    report = ProductionReadinessChecker().evaluate(
        risk_config={
            "execution": {"enabled": True, "require_approval": True, "mode": "live"},
            "exposure": {"max_notional_per_market": 100, "max_total_notional": 500},
            "safety": {"kill_switch_enabled": True},
        },
        execution_modes={"modes": ["dry_run", "live"]},
        whitelist_config={"markets": ["sample_market_001"]},
        model_validation_report={
            "approved_for_live": True,
            "deployment_mode": "live",
            "calibration_status": "calibrated",
        },
        approval_probe={"approval_valid": True},
        live_mode_policy=_valid_live_mode_policy(),
        position_exposure={
            "snapshot_available": True,
            "market_notional": 0.0,
            "total_notional": 0.0,
            "total_position_count": 0,
        },
        clob_adapter_ready=True,
    )

    assert report["ready_for_live"] is True
    assert report["status"] == "ready"
    assert report["decision"] == "LIVE_EXECUTION_ALLOWED"


def test_latest_approval_probe_reads_active_approval(tmp_path):
    db_path = tmp_path / "weather_telegram_console.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE approvals (
            approval_id TEXT PRIMARY KEY,
            signal_id TEXT,
            operator_user_id INTEGER,
            decision TEXT,
            expires_at TEXT,
            created_at TEXT,
            intent_id TEXT,
            is_consumed INTEGER
        )
        """
    )
    cur.execute(
        """
        INSERT INTO approvals (
            approval_id, signal_id, operator_user_id, decision,
            expires_at, created_at, intent_id, is_consumed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "approval_1",
            "signal_1",
            123,
            "approve_small",
            (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            "intent_1",
            0,
        ),
    )
    conn.commit()
    conn.close()

    probe = load_latest_approval_probe(db_path)

    assert probe["probe_available"] is True
    assert probe["approval_valid"] is True
    assert probe["approval_id"] == "approval_1"


def test_latest_approval_probe_warns_when_latest_is_consumed(tmp_path):
    db_path = tmp_path / "weather_telegram_console.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE approvals (
            approval_id TEXT PRIMARY KEY,
            signal_id TEXT,
            operator_user_id INTEGER,
            decision TEXT,
            expires_at TEXT,
            created_at TEXT,
            intent_id TEXT,
            is_consumed INTEGER
        )
        """
    )
    cur.execute(
        """
        INSERT INTO approvals (
            approval_id, signal_id, operator_user_id, decision,
            expires_at, created_at, intent_id, is_consumed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "approval_1",
            "signal_1",
            123,
            "approve_small",
            (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            "intent_1",
            1,
        ),
    )
    conn.commit()
    conn.close()

    probe = load_latest_approval_probe(db_path)
    report = ProductionReadinessChecker().evaluate(
        risk_config={
            "execution": {"enabled": True, "require_approval": True, "mode": "live"},
            "exposure": {"max_notional_per_market": 100, "max_total_notional": 500},
            "safety": {"kill_switch_enabled": True},
        },
        execution_modes={"modes": ["dry_run", "live"]},
        whitelist_config={"markets": ["sample_market_001"]},
        model_validation_report={
            "approved_for_live": True,
            "deployment_mode": "live",
            "calibration_status": "calibrated",
        },
        approval_probe=probe,
        live_mode_policy=_valid_live_mode_policy(),
        position_exposure={
            "snapshot_available": True,
            "market_notional": 0.0,
            "total_notional": 0.0,
            "total_position_count": 0,
        },
        clob_adapter_ready=True,
    )

    warning_names = {check["name"] for check in report["checks"] if check["status"] == "warning"}
    assert probe["probe_available"] is False
    assert probe["reason"] == "latest_approval_consumed"
    assert "approval_probe" in warning_names


def test_production_readiness_blocks_when_live_policy_has_too_few_approvers():
    report = ProductionReadinessChecker().evaluate(
        risk_config={
            "execution": {"enabled": True, "require_approval": True, "mode": "live"},
            "exposure": {"max_notional_per_market": 100, "max_total_notional": 500},
            "safety": {"kill_switch_enabled": True},
        },
        execution_modes={"modes": ["dry_run", "live"]},
        whitelist_config={"markets": ["sample_market_001"]},
        model_validation_report={
            "approved_for_live": True,
            "deployment_mode": "live",
            "calibration_status": "calibrated",
        },
        approval_probe={"approval_valid": True},
        live_mode_policy={
            "policy": {
                "enabled": True,
                "allow_live_execution": True,
                "approved_by": ["risk-lead"],
                "min_approver_count": 2,
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            },
            "required_checks": {
                "kill_switch": True,
                "approval_required": True,
                "market_whitelist": True,
                "exposure_limits": True,
                "model_validation": True,
                "approval_probe": True,
                "clob_adapter": True,
                "execution_modes": True,
            },
        },
        position_exposure={
            "snapshot_available": True,
            "market_notional": 0.0,
            "total_notional": 0.0,
            "total_position_count": 0,
        },
        clob_adapter_ready=True,
    )

    blocked_names = {check["name"] for check in report["checks"] if check["status"] == "blocked"}
    assert report["ready_for_live"] is False
    assert "live_mode_policy" in blocked_names


def test_production_readiness_blocks_when_live_policy_expired():
    report = ProductionReadinessChecker().evaluate(
        risk_config={
            "execution": {"enabled": True, "require_approval": True, "mode": "live"},
            "exposure": {"max_notional_per_market": 100, "max_total_notional": 500},
            "safety": {"kill_switch_enabled": True},
        },
        execution_modes={"modes": ["dry_run", "live"]},
        whitelist_config={"markets": ["sample_market_001"]},
        model_validation_report={
            "approved_for_live": True,
            "deployment_mode": "live",
            "calibration_status": "calibrated",
        },
        approval_probe={"approval_valid": True},
        live_mode_policy={
            **_valid_live_mode_policy(),
            "policy": {
                **_valid_live_mode_policy()["policy"],
                "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            },
        },
        position_exposure={
            "snapshot_available": True,
            "market_notional": 0.0,
            "total_notional": 0.0,
            "total_position_count": 0,
        },
        clob_adapter_ready=True,
    )

    blocked_names = {check["name"] for check in report["checks"] if check["status"] == "blocked"}
    assert report["ready_for_live"] is False
    assert "live_mode_policy" in blocked_names


def test_production_readiness_blocks_when_position_snapshot_missing():
    report = ProductionReadinessChecker().evaluate(
        risk_config={
            "execution": {"enabled": True, "require_approval": True, "mode": "live"},
            "exposure": {"max_notional_per_market": 100, "max_total_notional": 500},
            "safety": {"kill_switch_enabled": True},
        },
        execution_modes={"modes": ["dry_run", "live"]},
        whitelist_config={"markets": ["sample_market_001"]},
        model_validation_report={
            "approved_for_live": True,
            "deployment_mode": "live",
            "calibration_status": "calibrated",
        },
        approval_probe={"approval_valid": True},
        live_mode_policy=_valid_live_mode_policy(),
        position_exposure={"snapshot_available": False},
        clob_adapter_ready=True,
    )

    blocked_names = {check["name"] for check in report["checks"] if check["status"] == "blocked"}
    assert report["ready_for_live"] is False
    assert "position_exposure" in blocked_names


def _valid_live_mode_policy() -> dict:
    return {
        "policy": {
            "policy_id": "production_live_gate_test",
            "enabled": True,
            "allow_live_execution": True,
            "approved_by": ["risk-lead", "operator-lead"],
            "min_approver_count": 2,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        },
        "required_checks": {
            "kill_switch": True,
            "approval_required": True,
            "market_whitelist": True,
            "exposure_limits": True,
            "model_validation": True,
            "approval_probe": True,
            "clob_adapter": True,
            "execution_modes": True,
        },
    }
