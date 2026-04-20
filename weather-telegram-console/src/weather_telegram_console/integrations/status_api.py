from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from weather_telegram_console.settings import (
    get_gate_stack_api_path,
    get_monitoring_status_path,
    get_production_readiness_path,
    get_signal_json_path,
    get_unified_status_path,
)
from weather_telegram_console.integrations.gate_stack_consumer import consume_gate_stack_payload


class StatusAPI:
    def load_latest_status(self) -> dict:
        gate_stack_api = self._load_json(get_gate_stack_api_path())
        unified = self._load_json(get_unified_status_path())
        selected_market_id = None
        if isinstance(unified, dict):
            selected_market_id = str((unified.get("current_market") or {}).get("market_id") or "").strip() or None
        elif isinstance(gate_stack_api, dict):
            selected_market_id = str(gate_stack_api.get("market_id") or "").strip() or None
        consumer = consume_gate_stack_payload(
            gate_stack_api if isinstance(gate_stack_api, dict) else {},
            market_id=selected_market_id,
        )
        if isinstance(unified, dict):
            return _ensure_gate_stack(_apply_gate_stack_api(unified, consumer))

        if isinstance(gate_stack_api, dict):
            return _build_status_from_gate_stack_api(consumer)

        monitoring = self._load_json(get_monitoring_status_path())
        readiness = self._load_json(get_production_readiness_path())
        signal = self._load_json(get_signal_json_path())

        if not isinstance(monitoring, dict) and not isinstance(readiness, dict) and not isinstance(signal, dict):
            raise FileNotFoundError(
                "No gate stack API, unified status, monitoring report, readiness report or signal payload found."
            )

        payload = self._build_fallback_status(
            monitoring=monitoring if isinstance(monitoring, dict) else {},
            readiness=readiness if isinstance(readiness, dict) else {},
            signal=signal if isinstance(signal, dict) else {},
        )
        return _apply_gate_stack_api(payload, consumer)

    def _build_fallback_status(
        self,
        *,
        monitoring: dict,
        readiness: dict,
        signal: dict,
    ) -> dict:
        overall_status = str(monitoring.get("overall_status") or "warning")
        promotion_state = _extract_promotion_state(signal)
        probability_contract = signal.get("probability_contract")
        if not isinstance(probability_contract, dict):
            probability_contract = {}
        base_probability_mode = str(
            probability_contract.get("probability_mode")
            or signal.get("base_probability_mode")
            or signal.get("probability_mode")
            or "unknown"
        )
        base_execution_constraint = str(
            probability_contract.get("execution_constraint")
            or signal.get("base_execution_constraint")
            or signal.get("execution_constraint")
            or "manual_advisory_only"
        )
        probability_mode = str(
            promotion_state.get("probability_mode") or signal.get("probability_mode") or "unknown"
        )
        execution_constraint = str(
            promotion_state.get("execution_constraint")
            or signal.get("execution_constraint")
            or "manual_advisory_only"
        )
        probability_contract = signal.get("probability_contract")
        if not isinstance(probability_contract, dict):
            probability_contract = {
                "contract_version": "probability_contract.v1",
                "probability_mode": base_probability_mode,
                "execution_constraint": base_execution_constraint,
                "calibration_status": signal.get("calibration_status") or "unknown",
            }
        execution_status = str(readiness.get("status") or "unknown")
        block_reasons = ["unified_status_missing"]
        operator_mode = _resolve_operator_mode(readiness=readiness)

        if overall_status != "healthy":
            block_reasons.append(f"monitoring:{overall_status}")
        if probability_mode != "live_approved":
            block_reasons.append(f"probability_mode:{probability_mode}")
        if execution_status != "ready":
            block_reasons.append(f"execution:{execution_status}")

        payload = {
            "schema_version": "unified_status.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "current_market": {
                "market_id": signal.get("market_id"),
                "market_question": signal.get("market_question"),
                "comparison_status": signal.get("comparison_status"),
                "action_hint": signal.get("action_hint"),
            },
            "monitoring": {
                "overall_status": overall_status,
                "counts": monitoring.get("counts") or {},
                "worker_count": len(monitoring.get("workers") or []),
                "workers": monitoring.get("workers") or [],
            },
            "probability": {
                "market_id": signal.get("market_id"),
                "probability_mode": probability_mode,
                "execution_constraint": execution_constraint,
                "calibration_status": signal.get("calibration_status") or "unknown",
                "contract_version": probability_contract.get("contract_version") or "probability_contract.v1",
                "probability_contract": probability_contract,
                "base_probability_mode": base_probability_mode,
                "base_execution_constraint": base_execution_constraint,
                "promotion_state": promotion_state,
                "promotion_reason": promotion_state.get("promotion_reason") or signal.get("promotion_reason"),
                "demotion_reason": promotion_state.get("demotion_reason") or signal.get("demotion_reason"),
                "confidence_adjusted_edge": signal.get("edge_strength"),
                "confidence_score": (signal.get("confidence") or {}).get("score"),
                "resolver_status": signal.get("rule_status"),
            },
            "execution": {
                "status": execution_status,
                "ready_for_live": bool(readiness.get("ready_for_live", False)),
                "decision": readiness.get("decision") or "-",
                "blocking_count": int(readiness.get("blocking_count") or 0),
                "warning_count": int(readiness.get("warning_count") or 0),
            },
            "operator": {
                "can_bot_trade": False,
                "human_action_required": True,
                "execution_mode": execution_constraint,
                "operator_mode": operator_mode,
                "mode_badge": _mode_badge(operator_mode),
                "dev_controls_enabled": operator_mode == "dev_local_harness",
            },
            "block_reasons": block_reasons,
            "promotion_state": promotion_state,
        }
        return _ensure_gate_stack(payload)

    def _load_json(self, path: Path) -> Any:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None


def _resolve_operator_mode(*, readiness: dict) -> str:
    configured = str(os.getenv("AARS_OPERATOR_MODE") or "").strip().lower()
    if configured in {"dev_local_harness", "dry_run_guarded", "production_read_only"}:
        return configured

    enable_dev = str(os.getenv("AARS_ENABLE_DEV_HARNESS") or "").strip().lower()
    if enable_dev in {"1", "true", "yes", "on"}:
        return "dev_local_harness"

    if bool(readiness.get("ready_for_live")) and str(readiness.get("status") or "") == "ready":
        return "production_read_only"

    return "dry_run_guarded"


def _mode_badge(operator_mode: str) -> dict[str, str]:
    mapping = {
        "dev_local_harness": {
            "label": "DEV LOCAL HARNESS",
            "tone": "warning",
            "description": "Local verification mode with development-only harness controls visible.",
        },
        "dry_run_guarded": {
            "label": "DRY-RUN GUARDED",
            "tone": "info",
            "description": "Guarded operator mode with manual advisory and dry-run semantics.",
        },
        "production_read_only": {
            "label": "PRODUCTION READ-ONLY",
            "tone": "neutral",
            "description": "Production observation mode with dev-only controls hidden.",
        },
    }
    return mapping.get(
        operator_mode,
        {
            "label": "UNKNOWN MODE",
            "tone": "warning",
            "description": "Operator mode is not recognized.",
        },
    )


def _ensure_gate_stack(report: dict) -> dict:
    gate_stack = report.get("gate_stack")
    if isinstance(gate_stack, dict):
        return report

    monitoring = report.get("monitoring") or {}
    probability = report.get("probability") or {}
    execution = report.get("execution") or {}
    current_market = report.get("current_market") or {}

    resolver_status = str(
        current_market.get("rule_status")
        or probability.get("resolver_status")
        or ""
    ).lower()
    resolver_reasons: list[str] = []
    if resolver_status and resolver_status not in {"matched", "matched_index", "matched_snapshot"}:
        resolver_reasons.append("resolver_not_matched")
    if not resolver_status:
        resolver_reasons.append("resolver_not_matched")

    probability_reasons: list[str] = []
    if str(probability.get("probability_mode") or "") != "live_approved":
        probability_reasons.append("probability_not_live_approved")
    if str(probability.get("execution_constraint") or "") != "live_execution_allowed":
        probability_reasons.append("execution_constraint_not_live_allowed")
    if str(probability.get("calibration_status") or "") != "calibrated":
        probability_reasons.append("calibration_not_calibrated")

    freshness_reasons: list[str] = []
    if str(monitoring.get("overall_status") or "").lower() != "healthy":
        freshness_reasons.append("monitoring_not_healthy")
    for worker in monitoring.get("workers") or []:
        if str((worker or {}).get("status") or "").lower() != "healthy":
            freshness_reasons.append("stale_worker")
            break

    authorization_reasons: list[str] = []
    for reason in resolver_reasons + probability_reasons + freshness_reasons:
        if reason not in authorization_reasons:
            authorization_reasons.append(reason)

    execution_reasons: list[str] = []
    if str(execution.get("status") or "").lower() != "ready":
        execution_reasons.append("execution_not_ready")
    if not bool(execution.get("ready_for_live")):
        execution_reasons.append("execution_not_live_ready")

    data_reasons: list[str] = []
    comparison_status = str(current_market.get("comparison_status") or "")
    if comparison_status not in {"aligned", "mild_divergence", "strong_divergence"}:
        data_reasons.append("comparison_not_actionable")

    all_reasons: list[str] = []
    for bucket in (
        data_reasons,
        resolver_reasons,
        probability_reasons,
        freshness_reasons,
        authorization_reasons,
        execution_reasons,
    ):
        for reason in bucket:
            if reason not in all_reasons:
                all_reasons.append(reason)
    for reason in report.get("block_reasons") or []:
        token = str(reason)
        if token not in all_reasons:
            all_reasons.append(token)

    report["gate_stack"] = {
        "data_gate": "pass" if not data_reasons else "blocked",
        "data_gate_reasons": data_reasons,
        "resolver_gate": "pass" if not resolver_reasons else "blocked",
        "resolver_gate_reasons": resolver_reasons,
        "probability_gate": "pass" if not probability_reasons else "blocked",
        "probability_gate_reasons": probability_reasons,
        "freshness_gate": "pass" if not freshness_reasons else "blocked",
        "freshness_gate_reasons": freshness_reasons,
        "authorization_gate": "pass" if not authorization_reasons else "blocked",
        "authorization_gate_reasons": authorization_reasons,
        "execution_gate": "pass" if not execution_reasons else "blocked",
        "execution_gate_reasons": execution_reasons,
        "block_reasons": all_reasons,
    }
    return report


def _is_gate_stack_api(payload: dict | None) -> bool:
    return isinstance(payload, dict) and str(payload.get("schema_version") or "") == "gate_stack_api.v1"


def _apply_gate_stack_api(report: dict, consumer) -> dict:
    gate_stack_api = consumer.raw_payload if isinstance(getattr(consumer, "raw_payload", None), dict) else None
    if not _is_gate_stack_api(gate_stack_api):
        return report
    current_market = report.get("current_market")
    market_id = str((current_market or {}).get("market_id") or "")
    gate_stack = consumer.market_view if isinstance(getattr(consumer, "market_view", None), dict) else None
    if not isinstance(gate_stack, dict):
        gate_stack = consumer.payload.get("gate_stack") if isinstance(consumer.payload.get("gate_stack"), dict) else consumer.payload
    if not isinstance(gate_stack, dict):
        return report

    merged = dict(report)
    merged["gate_stack"] = gate_stack
    merged["block_reasons"] = [str(item) for item in gate_stack.get("block_reasons") or gate_stack_api.get("block_reasons") or []]

    contracts = merged.get("contracts")
    if not isinstance(contracts, dict):
        contracts = {}
    contracts["gate_stack_api_version"] = "gate_stack_api.v1"
    contracts["gate_stack_source_schema_version"] = str(
        gate_stack_api.get("source_schema_version") or "unknown"
    )
    contracts["gate_source"] = consumer.gate_source
    merged["contracts"] = contracts
    merged["gate_severity"] = str(
        gate_stack.get("severity")
        or gate_stack_api.get("severity")
        or _recommended_severity(
            str(gate_stack.get("primary_block_reason") or gate_stack_api.get("primary_block_reason") or ""),
            can_execute=bool(gate_stack_api.get("can_execute", False)),
        )
    )
    merged["recommended_operator_action"] = str(
        gate_stack.get("recommended_operator_action")
        or gate_stack_api.get("recommended_operator_action")
        or _recommended_action(
            str(gate_stack.get("primary_block_reason") or gate_stack_api.get("primary_block_reason") or ""),
            can_execute=bool(gate_stack_api.get("can_execute", False)),
        )
    )
    promotion_state = _extract_promotion_state(merged, gate_stack_api, gate_stack)
    if promotion_state:
        merged["promotion_state"] = promotion_state
        probability = merged.get("probability")
        if not isinstance(probability, dict):
            probability = {}
        probability["promotion_state"] = promotion_state
        probability["probability_mode"] = str(
            promotion_state.get("probability_mode") or probability.get("probability_mode") or "unknown"
        )
        probability["execution_constraint"] = str(
            promotion_state.get("execution_constraint")
            or probability.get("execution_constraint")
            or "manual_advisory_only"
        )
        probability["promotion_reason"] = promotion_state.get("promotion_reason")
        probability["demotion_reason"] = promotion_state.get("demotion_reason")
        merged["probability"] = probability
    return merged


def _build_status_from_gate_stack_api(consumer) -> dict:
    gate_stack_api = consumer.raw_payload if isinstance(getattr(consumer, "raw_payload", None), dict) else None
    if not _is_gate_stack_api(gate_stack_api):
        return _ensure_gate_stack({})

    gate_stack = consumer.market_view if isinstance(getattr(consumer, "market_view", None), dict) else None
    if not isinstance(gate_stack, dict):
        gate_stack = consumer.payload.get("gate_stack") if isinstance(consumer.payload.get("gate_stack"), dict) else consumer.payload
    if not isinstance(gate_stack, dict):
        gate_stack = {}

    payload = {
        "schema_version": "unified_status.v1",
        "generated_at": str(gate_stack_api.get("generated_at") or datetime.now(timezone.utc).isoformat()),
        "overall_status": str(gate_stack_api.get("overall_status") or "warning"),
        "current_market": {
            "market_id": gate_stack_api.get("market_id"),
            "comparison_status": consumer.market_view.get("comparison_status") if consumer.market_view else gate_stack_api.get("comparison_status"),
            "action_hint": consumer.market_view.get("action_hint") if consumer.market_view else gate_stack_api.get("action_hint"),
        },
        "monitoring": {
            "overall_status": "unknown",
            "counts": {},
            "worker_count": 0,
            "workers": [],
        },
        "probability": {
            "market_id": gate_stack_api.get("market_id"),
            "probability_mode": str(_extract_promotion_state(gate_stack_api).get("probability_mode") or "unknown"),
            "execution_constraint": str(
                _extract_promotion_state(gate_stack_api).get("execution_constraint") or "manual_advisory_only"
            ),
            "calibration_status": "unknown",
            "contract_version": "probability_contract.v1",
            "probability_contract": {
                "contract_version": "probability_contract.v1",
                "probability_mode": str(_extract_promotion_state(gate_stack_api).get("base_probability_mode") or "unknown"),
                "execution_constraint": str(
                    _extract_promotion_state(gate_stack_api).get("base_execution_constraint")
                    or "manual_advisory_only"
                ),
                "calibration_status": "unknown",
            },
            "promotion_state": _extract_promotion_state(gate_stack_api),
            "promotion_reason": _extract_promotion_state(gate_stack_api).get("promotion_reason"),
            "demotion_reason": _extract_promotion_state(gate_stack_api).get("demotion_reason"),
        },
        "execution": {
            "status": "unknown",
            "ready_for_live": bool(gate_stack_api.get("can_execute", False)),
            "decision": "-",
            "blocking_count": len(gate_stack_api.get("block_reasons") or []),
            "warning_count": 0,
        },
        "operator": {
            "can_bot_trade": bool(gate_stack_api.get("can_execute", False)),
            "human_action_required": not bool(gate_stack_api.get("can_execute", False)),
            "execution_mode": "manual_advisory_only",
            "operator_mode": "dry_run_guarded",
            "mode_badge": _mode_badge("dry_run_guarded"),
            "dev_controls_enabled": False,
        },
        "gate_stack": gate_stack,
        "block_reasons": [str(item) for item in gate_stack_api.get("block_reasons") or []],
        "contracts": {
            "gate_stack_api_version": "gate_stack_api.v1",
            "gate_stack_source_schema_version": str(
                gate_stack_api.get("source_schema_version") or "unknown"
            ),
            "gate_source": consumer.gate_source,
        },
        "gate_severity": str(
            gate_stack.get("severity")
            or gate_stack_api.get("severity")
            or _recommended_severity(
                str(gate_stack.get("primary_block_reason") or gate_stack_api.get("primary_block_reason") or ""),
                can_execute=bool(gate_stack_api.get("can_execute", False)),
            )
        ),
        "recommended_operator_action": str(
            gate_stack.get("recommended_operator_action")
            or gate_stack_api.get("recommended_operator_action")
            or _recommended_action(
                str(gate_stack.get("primary_block_reason") or gate_stack_api.get("primary_block_reason") or ""),
            can_execute=bool(gate_stack_api.get("can_execute", False)),
        )
    ),
        "promotion_state": _extract_promotion_state(gate_stack_api),
    }
    return _ensure_gate_stack(payload)


def _recommended_severity(primary_block_reason: str, *, can_execute: bool) -> str:
    if can_execute:
        return "low"
    if primary_block_reason in {
        "stale_worker",
        "monitoring_not_healthy",
        "validation_freshness_unhealthy",
        "label_coverage_unhealthy",
    }:
        return "high"
    return "medium"


def _recommended_action(primary_block_reason: str, *, can_execute: bool) -> str:
    if can_execute:
        return "allow_live_execution"
    if primary_block_reason in {
        "resolver_not_matched",
        "resolver_confidence_low",
        "resolver_source_not_exact",
        "comparison_not_actionable",
    }:
        return "review_resolver_contract"
    if primary_block_reason in {
        "stale_worker",
        "monitoring_not_healthy",
        "validation_freshness_unhealthy",
        "label_coverage_unhealthy",
    }:
        return "refresh_pipeline_inputs"
    if primary_block_reason in {
        "probability_not_live_approved",
        "execution_constraint_not_live_allowed",
        "calibration_not_calibrated",
    }:
        return "manual_advisory_only"
    if primary_block_reason in {"execution_not_ready", "execution_not_live_ready"}:
        return "check_gateway_readiness"
    return "hold_execution_and_review"


def _extract_promotion_state(*payloads: dict | None) -> dict:
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        candidate = payload.get("promotion_state")
        if isinstance(candidate, dict):
            return candidate
        probability = payload.get("probability")
        if isinstance(probability, dict):
            candidate = probability.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
        validation = payload.get("validation")
        if isinstance(validation, dict):
            candidate = validation.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
    return {}
