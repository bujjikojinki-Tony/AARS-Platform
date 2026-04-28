from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from weather_comparison_engine.governance.page_context import normalize_page_context


def build_command_context_view(
    *,
    selected_market_id: str | None = None,
    page_context: dict[str, Any] | None = None,
    market_workstation_view: dict[str, Any] | None = None,
    gate_stack_summary: dict[str, Any] | None = None,
    authorization_status: dict[str, Any] | None = None,
    pending_intent: dict[str, Any] | None = None,
    dry_run_result: dict[str, Any] | None = None,
    latest_signal: dict[str, Any] | None = None,
    audit_trail: list[dict[str, Any]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    page_context = normalize_page_context(
        page_context,
        source_page=str((page_context or {}).get("source_page") or "unknown"),
        target_page=str((page_context or {}).get("target_page") or "command"),
        selected_market_id=str(
            selected_market_id
            or (page_context or {}).get("selected_market_id")
            or (market_workstation_view or {}).get("selected_market_id")
            or ""
        ),
        selected_row_id=str((page_context or {}).get("selected_row_id") or ""),
        entry_reason=str((page_context or {}).get("entry_reason") or "decision_closure"),
        entry_context=(page_context or {}).get("entry_context") if isinstance(page_context, dict) else {},
        upstream_refs={
            "workstation_ref": str((market_workstation_view or {}).get("generated_at") or "-"),
            "gate_ref": str((gate_stack_summary or {}).get("generated_at") or "-"),
        },
        now=now,
    )
    market_workstation_view = market_workstation_view if isinstance(market_workstation_view, dict) else {}
    gate_stack_summary = gate_stack_summary if isinstance(gate_stack_summary, dict) else {}
    authorization_status = authorization_status if isinstance(authorization_status, dict) else {}
    pending_intent = pending_intent if isinstance(pending_intent, dict) else {}
    dry_run_result = dry_run_result if isinstance(dry_run_result, dict) else {}
    latest_signal = latest_signal if isinstance(latest_signal, dict) else {}
    audit_trail = [item for item in (audit_trail or []) if isinstance(item, dict)]

    entry_context = _entry_context_from_page_context(page_context, market_workstation_view)
    gate_summary = _build_gate_stack_summary(gate_stack_summary, market_workstation_view)
    operator_decision_panel = _build_operator_decision_panel(
        entry_context=entry_context,
        gate_summary=gate_summary,
        latest_signal=latest_signal,
        dry_run_result=dry_run_result,
        market_workstation_view=market_workstation_view,
    )
    authorization_gateway_panel = _build_authorization_gateway_panel(
        authorization_status=authorization_status,
        pending_intent=pending_intent,
        dry_run_result=dry_run_result,
        gate_summary=gate_summary,
    )
    available_actions, disabled_actions = _build_actions(
        gate_summary=gate_summary,
        authorization_gateway_panel=authorization_gateway_panel,
    )
    return {
        "schema_version": "command_context_view.v1",
        "generated_at": now.isoformat(),
        "selected_market_id": str(page_context.get("selected_market_id") or entry_context.get("selected_market_id") or "-"),
        "page_context": page_context,
        "entry_context": entry_context,
        "gate_stack_summary": gate_summary,
        "operator_decision_panel": operator_decision_panel,
        "authorization_gateway_panel": authorization_gateway_panel,
        "audit_trail": audit_trail,
        "available_actions": available_actions,
        "disabled_actions": disabled_actions,
        "latest_signal": latest_signal,
        "latest_dry_run_result": dry_run_result,
        "pending_intent": pending_intent,
    }


def _entry_context_from_page_context(page_context: dict[str, Any], market_workstation_view: dict[str, Any]) -> dict[str, Any]:
    entry_context = page_context.get("entry_context") if isinstance(page_context.get("entry_context"), dict) else {}
    opportunity_context = market_workstation_view.get("entry_context") if isinstance(market_workstation_view.get("entry_context"), dict) else {}
    merged = {**opportunity_context, **entry_context}
    merged.setdefault("selected_market_id", page_context.get("selected_market_id") or market_workstation_view.get("selected_market_id") or "-")
    merged.setdefault("source_page", page_context.get("source_page") or "-")
    merged.setdefault("target_page", page_context.get("target_page") or "command")
    merged.setdefault("entry_reason", page_context.get("entry_reason") or "decision_closure")
    return merged


def _build_gate_stack_summary(gate_stack_summary: dict[str, Any], market_workstation_view: dict[str, Any]) -> dict[str, Any]:
    gate_panel = market_workstation_view.get("gate_advisory_panel") if isinstance(market_workstation_view.get("gate_advisory_panel"), dict) else {}
    gate = gate_panel.get("gate_summary") if isinstance(gate_panel.get("gate_summary"), dict) else {}
    merged = {**gate, **gate_stack_summary}
    merged.setdefault("can_execute", gate.get("can_execute"))
    merged.setdefault("primary_block_reason", gate.get("primary_block_reason") or "-")
    merged.setdefault("execution_gate", gate.get("execution_gate") or gate.get("gate_status") or "-")
    merged.setdefault("resolver_gate", gate.get("resolver_gate") or "-")
    merged.setdefault("evidence_gate", gate.get("evidence_gate") or "-")
    merged.setdefault("probability_gate", gate.get("probability_gate") or "-")
    merged.setdefault("data_gate", gate.get("data_gate") or "-")
    merged.setdefault("authorization_gate", gate.get("authorization_gate") or "-")
    return merged


def _build_operator_decision_panel(
    *,
    entry_context: dict[str, Any],
    gate_summary: dict[str, Any],
    latest_signal: dict[str, Any],
    dry_run_result: dict[str, Any],
    market_workstation_view: dict[str, Any],
) -> dict[str, Any]:
    buy_sell_panel = (
        market_workstation_view.get("buy_sell_decision_panel")
        if isinstance(market_workstation_view.get("buy_sell_decision_panel"), dict)
        else {}
    )
    recommended_action = str(
        entry_context.get("recommended_action")
        or latest_signal.get("recommended_operator_action")
        or gate_summary.get("recommended_operator_action")
        or "review_evidence"
    )
    return {
        "recommended_next_action": recommended_action,
        "decision_reason": str(
            entry_context.get("recommended_action_reason")
            or latest_signal.get("primary_reason")
            or gate_summary.get("primary_block_reason")
            or "Decision should close the operator loop."
        ),
        "research_direction": str(buy_sell_panel.get("decision_outcome") or "review_evidence"),
        "research_direction_reason": str(buy_sell_panel.get("decision_reason") or "-"),
        "market_implied_probability": buy_sell_panel.get("market_implied_probability", "-"),
        "fair_value": buy_sell_panel.get("fair_value", "-"),
        "edge": buy_sell_panel.get("edge", "-"),
        "market_question": str(entry_context.get("market_question") or "-"),
        "best_model": str(entry_context.get("best_model") or "-"),
        "difficulty_label": str(entry_context.get("difficulty_label") or "-"),
        "dry_run_status": str(dry_run_result.get("status") or "-"),
    }


def _build_authorization_gateway_panel(
    *,
    authorization_status: dict[str, Any],
    pending_intent: dict[str, Any],
    dry_run_result: dict[str, Any],
    gate_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "bot_authorization": str(authorization_status.get("bot_authorization") or authorization_status.get("status") or "off"),
        "approval_status": str(authorization_status.get("approval_status") or "none"),
        "gateway_mode": str(authorization_status.get("gateway_mode") or "dry-run-only"),
        "kill_switch": str(authorization_status.get("kill_switch") or "safe"),
        "pending_intent_id": str(pending_intent.get("intent_id") or "-"),
        "pending_intent_status": str(pending_intent.get("status") or "none"),
        "dry_run_status": str(dry_run_result.get("status") or "-"),
        "latest_gate_allow": gate_summary.get("can_execute"),
        "latest_gate_block_reason": str(gate_summary.get("primary_block_reason") or "-"),
    }


def _build_actions(
    *,
    gate_summary: dict[str, Any],
    authorization_gateway_panel: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    can_execute = bool(gate_summary.get("can_execute"))
    live_enabled = can_execute and str(authorization_gateway_panel.get("gateway_mode") or "").lower() == "live"
    pending_intent_id = str(authorization_gateway_panel.get("pending_intent_id") or "").strip()
    actions = [
        {"action": "open_workstation", "enabled": True},
        {"action": "review_evidence", "enabled": True},
        {"action": "acknowledge_signal", "enabled": True},
        {"action": "create_pending_intent", "enabled": True},
        {
            "action": "run_dry_run_check",
            "enabled": pending_intent_id not in {"", "-"},
        },
        {"action": "live_execute", "enabled": live_enabled},
    ]
    available = [item for item in actions if item["enabled"]]
    disabled = [item for item in actions if not item["enabled"]]
    return available, disabled
