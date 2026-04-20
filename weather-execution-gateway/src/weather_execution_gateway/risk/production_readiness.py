from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ProductionReadinessChecker:
    def evaluate(
        self,
        *,
        risk_config: dict[str, Any],
        execution_modes: dict[str, Any] | None = None,
        whitelist_config: dict[str, Any] | None = None,
        model_validation_report: dict[str, Any] | None = None,
        approval_probe: dict[str, Any] | None = None,
        live_mode_policy: dict[str, Any] | None = None,
        position_exposure: dict[str, Any] | None = None,
        clob_adapter_ready: bool = False,
    ) -> dict:
        checks = [
            _check_live_mode_policy(live_mode_policy or {}),
            _check_execution_mode(risk_config),
            _check_kill_switch(risk_config),
            _check_approval_required(risk_config),
            _check_whitelist(whitelist_config or {}),
            _check_exposure_limits(risk_config),
            _check_position_exposure(position_exposure or {}),
            _check_model_validation(model_validation_report or {}),
            _check_approval_probe(approval_probe or {}),
            _check_clob_adapter(clob_adapter_ready),
            _check_execution_modes(execution_modes or {}),
        ]

        blocking = [check for check in checks if check["status"] == "blocked"]
        warnings = [check for check in checks if check["status"] == "warning"]

        return {
            "schema_version": "production_readiness_report.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ready_for_live": len(blocking) == 0,
            "status": "ready" if not blocking else "blocked",
            "blocking_count": len(blocking),
            "warning_count": len(warnings),
            "checks": checks,
            "decision": (
                "LIVE_EXECUTION_ALLOWED"
                if not blocking
                else "LIVE_EXECUTION_BLOCKED"
            ),
            "note": (
                "Production readiness is a pre-flight gate. A blocked status means the gateway "
                "must remain dry-run / disabled even if an operator approval exists."
            ),
        }


def load_optional_json(path: str | Path) -> dict:
    import json

    src = Path(path)
    if not src.exists():
        return {}
    payload = json.loads(src.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_latest_approval_probe(db_path: str | Path) -> dict:
    src = Path(db_path)
    if not src.exists():
        return {}

    try:
        conn = sqlite3.connect(str(src))
        cur = conn.cursor()
        cur.execute(
            """
            SELECT approval_id, signal_id, decision, expires_at, created_at, intent_id, is_consumed
            FROM approvals
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        conn.close()
    except sqlite3.DatabaseError:
        return {}

    if row is None:
        return {
            "probe_available": False,
            "reason": "no_approvals",
            "db_path": str(src),
        }

    expires_at = row[3]
    try:
        expires = datetime.fromisoformat(expires_at)
    except ValueError:
        expires = datetime.min.replace(tzinfo=timezone.utc)

    is_consumed = bool(row[6])
    is_expired = expires <= datetime.now(timezone.utc)
    approval_valid = row[2] == "approve_small" and not is_consumed and not is_expired

    reason = None
    if row[2] != "approve_small":
        reason = "latest_approval_not_approve_small"
    elif is_consumed:
        reason = "latest_approval_consumed"
    elif is_expired:
        reason = "latest_approval_expired"

    return {
        "probe_available": approval_valid,
        "approval_valid": approval_valid,
        "reason": reason,
        "approval_id": row[0],
        "signal_id": row[1],
        "decision": row[2],
        "expires_at": expires_at,
        "created_at": row[4],
        "intent_id": row[5],
        "is_consumed": is_consumed,
        "db_path": str(src),
    }


def _check_execution_mode(risk_config: dict[str, Any]) -> dict:
    execution = risk_config.get("execution") or {}
    enabled = bool(execution.get("enabled", False))
    mode = str(execution.get("mode") or "unknown")
    if not enabled:
        return _blocked(
            "execution_enabled",
            "Execution is disabled; gateway remains dry-run only.",
            {"enabled": enabled, "mode": mode},
        )
    if mode != "live":
        return _blocked(
            "execution_mode_live",
            "Execution mode is not live.",
            {"enabled": enabled, "mode": mode},
        )
    return _passed("execution_mode_live", "Execution config is live-enabled.", {"mode": mode})


def _check_live_mode_policy(live_mode_policy: dict[str, Any]) -> dict:
    if not live_mode_policy:
        return _blocked("live_mode_policy", "Live-mode policy file is missing.", {})

    policy = live_mode_policy.get("policy") or {}
    required_checks = live_mode_policy.get("required_checks") or {}
    enabled = bool(policy.get("enabled", False))
    allow_live = bool(policy.get("allow_live_execution", False))
    approved_by = policy.get("approved_by") or []
    min_approver_count = int(policy.get("min_approver_count") or 0)
    expires_at = policy.get("expires_at")
    disabled_required = [
        name
        for name, required in required_checks.items()
        if required is not True
    ]

    details = {
        "policy_id": policy.get("policy_id"),
        "enabled": enabled,
        "allow_live_execution": allow_live,
        "approved_by_count": len(approved_by),
        "min_approver_count": min_approver_count,
        "expires_at": expires_at,
        "disabled_required_checks": disabled_required,
    }

    if not enabled:
        return _blocked("live_mode_policy", "Live-mode policy is disabled.", details)
    if not allow_live:
        return _blocked("live_mode_policy", "Live execution is not allowed by policy.", details)
    if len(approved_by) < min_approver_count:
        return _blocked("live_mode_policy", "Live-mode policy has insufficient approvers.", details)
    if not expires_at:
        return _blocked("live_mode_policy", "Live-mode policy requires an expiration timestamp.", details)

    try:
        expires = datetime.fromisoformat(str(expires_at))
    except ValueError:
        return _blocked("live_mode_policy", "Live-mode policy expiration is invalid.", details)

    if expires <= datetime.now(timezone.utc):
        return _blocked("live_mode_policy", "Live-mode policy has expired.", details)

    if disabled_required:
        return _blocked("live_mode_policy", "Live-mode policy disables required checks.", details)

    return _passed("live_mode_policy", "Live-mode policy permits readiness evaluation.", details)


def _check_kill_switch(risk_config: dict[str, Any]) -> dict:
    safety = risk_config.get("safety") or {}
    enabled = bool(safety.get("kill_switch_enabled", False))
    if not enabled:
        return _blocked("kill_switch", "Kill switch is not enabled in risk config.", safety)
    return _passed("kill_switch", "Kill switch is enabled.", safety)


def _check_approval_required(risk_config: dict[str, Any]) -> dict:
    execution = risk_config.get("execution") or {}
    required = bool(execution.get("require_approval", False))
    if not required:
        return _blocked("approval_required", "Operator approval is not required.", execution)
    return _passed("approval_required", "Operator approval is required.", execution)


def _check_whitelist(whitelist_config: dict[str, Any]) -> dict:
    markets = whitelist_config.get("markets") or []
    if not markets:
        return _blocked("market_whitelist", "No markets are whitelisted.", whitelist_config)
    return _passed("market_whitelist", "Market whitelist is configured.", {"count": len(markets)})


def _check_exposure_limits(risk_config: dict[str, Any]) -> dict:
    exposure = risk_config.get("exposure") or {}
    max_market = float(exposure.get("max_notional_per_market") or 0)
    max_total = float(exposure.get("max_total_notional") or 0)
    if max_market <= 0 or max_total <= 0:
        return _blocked("exposure_limits", "Exposure limits are missing or non-positive.", exposure)
    return _passed("exposure_limits", "Exposure limits are configured.", exposure)


def _check_position_exposure(position_exposure: dict[str, Any]) -> dict:
    if not position_exposure:
        return _blocked("position_exposure", "Position exposure snapshot is missing.", {})

    if position_exposure.get("snapshot_available") is not True:
        return _blocked(
            "position_exposure",
            "Position exposure snapshot is unavailable.",
            position_exposure,
        )

    return _passed(
        "position_exposure",
        "Position exposure snapshot is available.",
        {
            "snapshot_updated_at": position_exposure.get("snapshot_updated_at"),
            "market_notional": position_exposure.get("market_notional"),
            "total_notional": position_exposure.get("total_notional"),
            "total_position_count": position_exposure.get("total_position_count"),
            "total_open_order_count": position_exposure.get("total_open_order_count"),
            "available_balance": position_exposure.get("available_balance"),
            "balance_currency": position_exposure.get("balance_currency"),
            "manual_order_only": position_exposure.get("manual_order_only"),
            "balance_snapshot_available": position_exposure.get("balance_snapshot_available"),
            "source_path": position_exposure.get("source_path"),
        },
    )


def _check_model_validation(report: dict[str, Any]) -> dict:
    if not report:
        return _blocked("model_validation", "Model validation report is missing.", {})
    approved = bool(report.get("approved_for_live", False))
    deployment_mode = str(report.get("deployment_mode") or "unknown")
    calibration_status = str(report.get("calibration_status") or "unknown")
    if not approved:
        return _blocked(
            "model_validation",
            "Model validation is not approved for live execution.",
            {
                "approved_for_live": approved,
                "deployment_mode": deployment_mode,
                "calibration_status": calibration_status,
            },
        )
    if deployment_mode != "live":
        return _blocked(
            "model_deployment_mode",
            "Model deployment mode is not live.",
            {"deployment_mode": deployment_mode},
        )
    return _passed("model_validation", "Model validation permits live execution.", report)


def _check_approval_probe(approval_probe: dict[str, Any]) -> dict:
    if not approval_probe:
        return _warning("approval_probe", "No recent approval probe was supplied.", {})
    if approval_probe.get("probe_available") is False:
        return _warning(
            "approval_probe",
            "No active approval probe is currently available.",
            approval_probe,
        )
    if approval_probe.get("approval_valid") is not True:
        return _blocked("approval_probe", "Latest approval probe is not valid.", approval_probe)
    return _passed("approval_probe", "Latest approval probe is valid.", approval_probe)


def _check_clob_adapter(ready: bool) -> dict:
    if not ready:
        return _blocked(
            "clob_adapter",
            "Real Polymarket CLOB execution adapter is not enabled.",
            {"clob_adapter_ready": ready},
        )
    return _passed("clob_adapter", "Real CLOB adapter is enabled.", {"clob_adapter_ready": ready})


def _check_execution_modes(execution_modes: dict[str, Any]) -> dict:
    modes = execution_modes.get("modes") or []
    if "live" not in modes:
        return _blocked(
            "execution_modes",
            "Execution modes config does not include live mode.",
            {"modes": modes},
        )
    return _passed("execution_modes", "Execution modes include live.", {"modes": modes})


def _passed(name: str, message: str, details: dict[str, Any]) -> dict:
    return {"name": name, "status": "passed", "message": message, "details": details}


def _warning(name: str, message: str, details: dict[str, Any]) -> dict:
    return {"name": name, "status": "warning", "message": message, "details": details}


def _blocked(name: str, message: str, details: dict[str, Any]) -> dict:
    return {"name": name, "status": "blocked", "message": message, "details": details}
