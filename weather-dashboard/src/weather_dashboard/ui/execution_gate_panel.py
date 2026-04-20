from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from uuid import uuid4

import streamlit as st

from weather_dashboard.ui.compact_panel import render_compact_note, render_kv_section, render_panel_title


def render_execution_gate_panel(
    *,
    market_snapshot: dict | None,
    forecast_snapshot: dict | None,
    resolver_rule: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
    validation_freshness_status: dict | None = None,
    label_coverage_report: dict | None = None,
    bot_authorized: bool,
    pending_intents_dir: Path,
    latest_intent_path: Path,
    telegram_signal_path: Path,
    whitelist_path: Path,
    gateway_dir: Path,
    approval_db_path: Path,
    production_readiness_path: Path | None = None,
    manual_advisory_audit_path: Path | None = None,
    key_prefix: str = "execution_gate",
    operator_mode: str = "dry_run_guarded",
) -> None:
    render_panel_title("Execution Gate")

    gate = build_execution_gate_state(
        market_snapshot=market_snapshot,
        forecast_snapshot=forecast_snapshot,
        resolver_rule=resolver_rule,
        probability_state=probability_state,
        comparison_row=comparison_row,
        validation_freshness_status=validation_freshness_status,
        label_coverage_report=label_coverage_report,
        bot_authorized=bot_authorized,
        whitelist_path=whitelist_path,
    )

    if gate["can_write_intent"]:
        render_compact_note(
            "Data is aligned and BOT authorization is ON. Dashboard can write a pending dry-run "
            "intent, but execution-gateway still applies whitelist, Telegram approval and risk gates.",
            tone="info",
        )
    else:
        render_compact_note(
            "BOT execution intent is blocked until market data, resolver, forecast, probability, "
            "comparison and authorization are aligned.",
            tone="warning",
        )

    if gate["probability_mode"] != "live_approved":
        render_compact_note(
            "Probability contract is not live-approved. Current flow remains manual advisory / dry-run only.",
            tone="warning",
        )

    _render_gate_cards(gate)

    c1, c2 = st.columns([0.45, 0.55], vertical_alignment="center")
    with c1:
        if st.button(
            "Write Pending Intent",
            key=f"{key_prefix}_write_execution_intent_{gate['market_id'] or 'none'}",
            use_container_width=True,
            disabled=not gate["can_write_intent"],
            help="Writes a dry-run order intent for the execution gateway. It does not place a trade.",
        ):
            intent = build_order_intent(gate)
            pending_path = write_order_intent(
                intent=intent,
                pending_intents_dir=pending_intents_dir,
                latest_intent_path=latest_intent_path,
                telegram_signal_path=telegram_signal_path,
                gate=gate,
                market_snapshot=market_snapshot,
                forecast_snapshot=forecast_snapshot,
                probability_state=probability_state,
                comparison_row=comparison_row,
                manual_advisory_audit_path=manual_advisory_audit_path,
            )
            st.session_state["last_execution_intent"] = {
                "intent": intent,
                "pending_path": str(pending_path),
                "latest_intent_path": str(latest_intent_path),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            st.toast(f"Pending dry-run intent written: {intent['intent_id']}", icon="✅")
            st.rerun()
    with c2:
        st.caption(
            "Intent writer is dry-run only. A real execution still requires execution-gateway "
            "risk gates and operator approval."
        )

    render_kv_section(
        "Gate Decision",
        [
            ("Market ID", gate["market_id"] or "-"),
            ("Recommended Outcome", gate["recommended_outcome"] or "-"),
            ("Order Side", gate["order_side"]),
            ("Intent Price", gate["price"] if gate["price"] is not None else "-"),
            ("Intent Size", gate["size"]),
            ("Data Aligned", gate["data_aligned"]),
            ("BOT Authorized", bot_authorized),
            ("Market Whitelisted", gate["market_whitelisted"]),
            ("Gateway Ready", gate["gateway_ready"]),
            ("Probability Mode", gate["probability_mode"]),
            ("Execution Constraint", gate["execution_constraint"]),
            ("Validation Freshness", gate["validation_freshness_status"]),
            ("Label Coverage", gate["label_coverage_status"]),
            ("Operator Mode", operator_mode),
            ("Autonomous Eligible", gate["autonomous_execution_eligible"]),
            ("Gate Status", gate["gate_status"]),
            ("Blockers", ", ".join(gate["blockers"]) if gate["blockers"] else "-"),
        ],
        metric_label="Gate",
        metric_value=gate["gate_status"],
    )

    latest_approval = load_latest_approval_status(
        db_path=approval_db_path,
        intent_id=str(st.session_state.get("last_execution_intent", {}).get("intent", {}).get("intent_id") or ""),
        signal_id=str(st.session_state.get("last_execution_intent", {}).get("intent", {}).get("signal_id") or ""),
    )
    if latest_approval is not None:
        render_kv_section(
            "Approval Status",
            [
                ("Approval ID", latest_approval.get("approval_id", "-")),
                ("Signal ID", latest_approval.get("signal_id", "-")),
                ("Intent ID", latest_approval.get("intent_id", "-")),
                ("Decision", latest_approval.get("decision", "-")),
                ("Status", latest_approval.get("status", "-")),
                ("Expires At", latest_approval.get("expires_at", "-")),
                ("Created At", latest_approval.get("created_at", "-")),
                ("Is Consumed", latest_approval.get("is_consumed", "-")),
            ],
            metric_label="Approval",
            metric_value=latest_approval.get("status", "-"),
        )

    readiness = load_production_readiness_report(production_readiness_path)
    if readiness is not None:
        render_production_readiness_summary(readiness)

    last_intent = st.session_state.get("last_execution_intent")
    if last_intent:
        if operator_mode == "dev_local_harness":
            _render_dev_execution_harness(
                last_intent=last_intent,
                market_id=gate["market_id"],
                whitelist_path=whitelist_path,
                approval_db_path=approval_db_path,
                key_prefix=key_prefix,
            )
        _render_gateway_dry_run_control(last_intent, gateway_dir, key_prefix=key_prefix)
        with st.expander("Last Written Intent", expanded=False):
            st.json(last_intent)

    gateway_result = st.session_state.get("last_gateway_dry_run_result")
    if gateway_result:
        with st.expander("Last Gateway Dry-Run Result", expanded=not gateway_result.get("ok", False)):
            st.json(gateway_result)


def build_execution_gate_state(
    *,
    market_snapshot: dict | None,
    forecast_snapshot: dict | None,
    resolver_rule: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
    validation_freshness_status: dict | None = None,
    label_coverage_report: dict | None = None,
    bot_authorized: bool,
    whitelist_path: Path,
) -> dict:
    market_id = _market_id(market_snapshot)
    forecast_id = _market_id(forecast_snapshot)
    resolver_id = _market_id(resolver_rule)
    probability_id = _market_id(probability_state)
    comparison_id = _market_id(comparison_row)
    resolver_status = str((resolver_rule or {}).get("resolver_status") or "")
    source_match_grade = str((resolver_rule or {}).get("source_match_grade") or "")
    source_policy = str((resolver_rule or {}).get("official_vs_proxy_source") or "")
    comparison_status = str((comparison_row or {}).get("comparison_status") or "")
    probability_mode = str((probability_state or {}).get("probability_mode") or "unknown")
    execution_constraint = str(
        (probability_state or {}).get("execution_constraint") or "manual_advisory_only"
    )
    validation_status = str((validation_freshness_status or {}).get("status") or "")
    label_coverage_status = str((label_coverage_report or {}).get("status") or "")

    blockers: list[str] = []
    if not market_id:
        blockers.append("selected_market_missing")
    if not forecast_id or forecast_id != market_id:
        blockers.append("forecast_market_mismatch")
    if not resolver_id or resolver_id != market_id or resolver_status != "matched":
        blockers.append("resolver_not_matched")
    if source_match_grade in {"family_only", "unmatched"} or source_policy == "fallback":
        blockers.append("resolver_source_not_exact")
    if not probability_id or probability_id != market_id:
        blockers.append("probability_missing_or_mismatch")
    if not comparison_id or comparison_id != market_id:
        blockers.append("comparison_missing_or_mismatch")
    if comparison_status in {"", "-", "market_mismatch", "unmatched_rule"}:
        blockers.append("comparison_not_actionable")
    if validation_status in {"warning", "blocked", "missing"}:
        blockers.append(f"validation_freshness_{validation_status}")
    if label_coverage_status in {"warning", "blocked", "missing"}:
        blockers.append(f"label_coverage_{label_coverage_status}")
    if not bot_authorized:
        blockers.append("bot_not_authorized")

    whitelisted = _is_market_whitelisted(whitelist_path, market_id)
    if not whitelisted:
        blockers.append("gateway_market_not_whitelisted")

    recommended_outcome = str((market_snapshot or {}).get("favored_side") or "yes").lower()
    price = _price_for_outcome(market_snapshot, recommended_outcome)
    if price is None:
        blockers.append("price_missing")

    data_blockers = [
        blocker
        for blocker in blockers
        if blocker not in {"bot_not_authorized", "gateway_market_not_whitelisted"}
    ]
    data_aligned = not data_blockers
    can_write_intent = data_aligned and bot_authorized and price is not None
    gateway_ready = can_write_intent and whitelisted
    gate_status = "READY" if gateway_ready else ("DRY_RUN_INTENT_READY" if can_write_intent else "BLOCKED")

    return {
        "market_id": market_id,
        "recommended_outcome": recommended_outcome,
        "order_side": "buy",
        "price": price,
        "size": 10.0,
        "data_aligned": data_aligned,
        "bot_authorized": bot_authorized,
        "market_whitelisted": whitelisted,
        "gateway_ready": gateway_ready,
        "can_write_intent": can_write_intent,
        "gate_status": gate_status,
        "comparison_status": comparison_status,
        "probability_mode": probability_mode,
        "execution_constraint": execution_constraint,
        "validation_freshness_status": validation_status or "-",
        "label_coverage_status": label_coverage_status or "-",
        "autonomous_execution_eligible": probability_mode == "live_approved",
        "blockers": blockers,
    }


def build_order_intent(gate: dict) -> dict:
    intent_id = f"intent_dashboard_{uuid4().hex[:10]}"
    probability_contract = _probability_contract_from_gate(gate)
    decision_ref = f"decision_dashboard_{gate['market_id']}_{intent_id[-10:]}"
    return {
        "schema_version": "execution_intent.v1",
        "intent_id": intent_id,
        "market_id": gate["market_id"],
        "signal_id": f"dashboard_{gate['market_id']}_{intent_id[-10:]}",
        "decision_ref": decision_ref,
        "authorization_ref": "approval_required",
        "side": gate["order_side"],
        "price": float(gate["price"]),
        "size": float(gate["size"]),
        "post_only": True,
        "max_slippage_pct": 0.02,
        "approved": bool(gate["bot_authorized"]),
        "probability_mode": gate.get("probability_mode"),
        "execution_constraint": gate.get("execution_constraint"),
        "calibration_status": probability_contract.get("calibration_status"),
        "contract_version": probability_contract.get("contract_version"),
        "probability_contract": probability_contract,
    }


def write_order_intent(
    *,
    intent: dict,
    pending_intents_dir: Path,
    latest_intent_path: Path,
    telegram_signal_path: Path | None = None,
    gate: dict | None = None,
    market_snapshot: dict | None = None,
    forecast_snapshot: dict | None = None,
    probability_state: dict | None = None,
    comparison_row: dict | None = None,
    manual_advisory_audit_path: Path | None = None,
) -> Path:
    pending_intents_dir.mkdir(parents=True, exist_ok=True)
    latest_intent_path.parent.mkdir(parents=True, exist_ok=True)

    pending_path = pending_intents_dir / f"{intent['intent_id']}.json"
    payload = json.dumps(intent, indent=2, ensure_ascii=False)
    pending_path.write_text(payload, encoding="utf-8")
    latest_intent_path.write_text(payload, encoding="utf-8")
    if telegram_signal_path is not None:
        write_telegram_approval_signal(
            path=telegram_signal_path,
            intent=intent,
            gate=gate or {},
            market_snapshot=market_snapshot,
            forecast_snapshot=forecast_snapshot,
            probability_state=probability_state,
            comparison_row=comparison_row,
        )
    if manual_advisory_audit_path is not None:
        write_manual_advisory_audit_event(
            path=manual_advisory_audit_path,
            event_type="manual_advisory_signal_created",
            intent=intent,
            gate=gate or {},
            market_snapshot=market_snapshot,
            forecast_snapshot=forecast_snapshot,
            probability_state=probability_state,
            comparison_row=comparison_row,
        )
    return pending_path


def write_telegram_approval_signal(
    *,
    path: Path,
    intent: dict,
    gate: dict,
    market_snapshot: dict | None = None,
    forecast_snapshot: dict | None = None,
    probability_state: dict | None = None,
    comparison_row: dict | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    signal = build_telegram_approval_signal(
        intent=intent,
        gate=gate,
        market_snapshot=market_snapshot,
        forecast_snapshot=forecast_snapshot,
        probability_state=probability_state,
        comparison_row=comparison_row,
    )
    path.write_text(json.dumps(signal, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_telegram_approval_signal(
    *,
    intent: dict,
    gate: dict,
    market_snapshot: dict | None = None,
    forecast_snapshot: dict | None = None,
    probability_state: dict | None = None,
    comparison_row: dict | None = None,
) -> dict:
    manual_trade_ticket = {
        "market_id": intent.get("market_id"),
        "recommended_side": intent.get("side"),
        "limit_price": intent.get("price"),
        "size": intent.get("size"),
        "post_only": intent.get("post_only"),
        "max_slippage_pct": intent.get("max_slippage_pct"),
    }
    return {
        "signal_id": intent.get("signal_id"),
        "intent_id": intent.get("intent_id"),
        "market_id": intent.get("market_id"),
        "execution_mode": "manual_advisory",
        "delivery_mode": "bot_reminder_manual_order",
        "manual_order_required": True,
        "autonomous_execution_allowed": False,
        "manual_trade_ticket": manual_trade_ticket,
        "location_name": (market_snapshot or {}).get("location_name"),
        "target_date": (forecast_snapshot or {}).get("target_date"),
        "variable_name": (forecast_snapshot or {}).get("variable_name"),
        "model_value": (forecast_snapshot or {}).get("value") or (comparison_row or {}).get("model_value"),
        "model_band": (forecast_snapshot or {}).get("model_band") or (comparison_row or {}).get("model_band"),
        "market_band": (market_snapshot or {}).get("market_band") or (comparison_row or {}).get("market_band"),
        "edge_direction": "dashboard_execution_intent",
        "edge_strength": (probability_state or {}).get("confidence_adjusted_edge"),
        "probability_mode": (probability_state or {}).get("probability_mode"),
        "execution_constraint": (probability_state or {}).get("execution_constraint"),
        "probability_contract": _probability_contract_from_state(probability_state),
        "action_hint": (comparison_row or {}).get("action_hint") or "approve_small",
        "confidence": {
            "level": gate.get("gate_status"),
            "score": (forecast_snapshot or {}).get("confidence_score")
            or (comparison_row or {}).get("confidence_score"),
            "reasons": [
                "dashboard_intent_ready",
                f"market_id={intent.get('market_id')}",
                f"intent_id={intent.get('intent_id')}",
            ],
        },
        "approval_context": {
            "source": "weather_dashboard",
            "intent_id": intent.get("intent_id"),
            "approval_purpose": "operator_review_not_auto_execution",
            "manual_order_required": True,
            "autonomous_execution_allowed": False,
            "probability_mode": (probability_state or {}).get("probability_mode"),
            "execution_constraint": (probability_state or {}).get("execution_constraint"),
            "probability_contract": _probability_contract_from_state(probability_state),
            "order_side": intent.get("side"),
            "price": intent.get("price"),
            "size": intent.get("size"),
            "gate_status": gate.get("gate_status"),
        },
    }


def _probability_contract_from_gate(gate: dict | None) -> dict:
    gate = gate or {}
    return {
        "contract_version": "probability_contract.v1",
        "probability_mode": gate.get("probability_mode") or "heuristic_not_calibrated",
        "calibration_status": gate.get("calibration_status") or "not_calibrated",
        "execution_constraint": gate.get("execution_constraint") or "manual_advisory_only",
    }


def _probability_contract_from_state(probability_state: dict | None) -> dict:
    state = probability_state or {}
    existing = state.get("probability_contract")
    if isinstance(existing, dict) and existing:
        return existing
    return {
        "contract_version": "probability_contract.v1",
        "probability_mode": state.get("probability_mode") or "heuristic_not_calibrated",
        "calibration_status": state.get("calibration_status") or "not_calibrated",
        "execution_constraint": state.get("execution_constraint") or "manual_advisory_only",
        "model_id": state.get("model_id"),
        "validation_ref": state.get("validation_ref") or state.get("validation_report_generated_at"),
        "approved_for_live": bool(state.get("approved_for_live", False)),
        "deployment_mode": state.get("deployment_mode") or "shadow",
        "promotion_reason": state.get("promotion_reason"),
        "contract_source": state.get("contract_source"),
        "validation_report_generated_at": state.get("validation_report_generated_at"),
    }


def write_manual_advisory_audit_event(
    *,
    path: Path,
    event_type: str,
    intent: dict,
    gate: dict | None = None,
    market_snapshot: dict | None = None,
    forecast_snapshot: dict | None = None,
    probability_state: dict | None = None,
    comparison_row: dict | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = build_manual_advisory_audit_event(
        event_type=event_type,
        intent=intent,
        gate=gate,
        market_snapshot=market_snapshot,
        forecast_snapshot=forecast_snapshot,
        probability_state=probability_state,
        comparison_row=comparison_row,
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return path


def build_manual_advisory_audit_event(
    *,
    event_type: str,
    intent: dict,
    gate: dict | None = None,
    market_snapshot: dict | None = None,
    forecast_snapshot: dict | None = None,
    probability_state: dict | None = None,
    comparison_row: dict | None = None,
) -> dict:
    return {
        "schema_version": "manual_advisory_event.v1",
        "event_id": f"manual_adv_{uuid4().hex[:10]}",
        "event_type": event_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "manual_advisory",
        "manual_order_required": True,
        "autonomous_execution_allowed": False,
        "intent_id": intent.get("intent_id"),
        "signal_id": intent.get("signal_id"),
        "market_id": intent.get("market_id"),
        "payload": {
            "manual_trade_ticket": {
                "side": intent.get("side"),
                "price": intent.get("price"),
                "size": intent.get("size"),
            },
            "probability_mode": (probability_state or {}).get("probability_mode"),
            "execution_constraint": (probability_state or {}).get("execution_constraint"),
            "gate_status": (gate or {}).get("gate_status"),
            "blockers": (gate or {}).get("blockers") or [],
            "market_question": (market_snapshot or {}).get("market_question"),
            "market_probability": (market_snapshot or {}).get("market_probability"),
            "model_band": (forecast_snapshot or {}).get("model_band")
            or (comparison_row or {}).get("model_band"),
            "edge_strength": (probability_state or {}).get("confidence_adjusted_edge"),
            "comparison_status": (comparison_row or {}).get("comparison_status"),
        },
    }


def run_gateway_dry_run_for_intent(
    *,
    gateway_dir: Path,
    intent_path: Path,
) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "weather_execution_gateway.main",
            "dry-run-intent-file",
            str(intent_path),
        ],
        cwd=str(gateway_dir),
        env=env,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    parsed_stdout = None
    try:
        parsed_stdout = json.loads(completed.stdout)
    except Exception:
        parsed_stdout = None

    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
        "parsed_stdout": parsed_stdout,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def ensure_market_in_dev_whitelist(path: Path, market_id: str) -> bool:
    if not market_id:
        raise ValueError("market_id is required")

    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"markets:\n  - {market_id}\n", encoding="utf-8")
        return True

    text = path.read_text(encoding="utf-8")
    if any(line.strip() == f"- {market_id}" for line in text.splitlines()):
        return False

    if not text.strip():
        text = "markets:\n"
    elif "markets:" not in text:
        text = f"markets:\n{text.rstrip()}\n"

    if not text.endswith("\n"):
        text += "\n"
    text += f"  - {market_id}\n"
    path.write_text(text, encoding="utf-8")
    return True


def create_local_test_approval(
    *,
    db_path: Path,
    intent: dict,
    operator_user_id: int = 0,
    ttl_minutes: int = 15,
) -> dict:
    intent_id = str(intent.get("intent_id") or "")
    signal_id = str(intent.get("signal_id") or "")
    if not intent_id:
        raise ValueError("intent missing intent_id")
    if not signal_id:
        raise ValueError("intent missing signal_id")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ttl_minutes)
    approval = {
        "approval_id": f"approval_dashboard_{uuid4().hex[:10]}",
        "signal_id": signal_id,
        "operator_user_id": operator_user_id,
        "decision": "approve_small",
        "expires_at": expires_at.isoformat(),
        "created_at": now.isoformat(),
        "intent_id": intent_id,
        "is_consumed": False,
    }

    conn = sqlite3.connect(str(db_path))
    try:
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
                approval["approval_id"],
                approval["signal_id"],
                approval["operator_user_id"],
                approval["decision"],
                approval["expires_at"],
                approval["created_at"],
                approval["intent_id"],
                0,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return approval


def load_latest_approval_status(
    *,
    db_path: Path,
    intent_id: str | None = None,
    signal_id: str | None = None,
) -> dict | None:
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        row = None
        if intent_id:
            cur.execute(
                """
                SELECT approval_id, signal_id, operator_user_id, decision,
                       expires_at, created_at, intent_id, is_consumed
                FROM approvals
                WHERE intent_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (intent_id,),
            )
            row = cur.fetchone()

        if row is None and signal_id:
            cur.execute(
                """
                SELECT approval_id, signal_id, operator_user_id, decision,
                       expires_at, created_at, intent_id, is_consumed
                FROM approvals
                WHERE signal_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (signal_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    expires_at = datetime.fromisoformat(row[4])
    now = datetime.now(timezone.utc)
    if row[7]:
        status = "已消费"
    elif expires_at <= now:
        status = "已过期"
    else:
        status = "已审批"

    return {
        "approval_id": row[0],
        "signal_id": row[1],
        "operator_user_id": row[2],
        "decision": row[3],
        "expires_at": row[4],
        "created_at": row[5],
        "intent_id": row[6],
        "is_consumed": bool(row[7]),
        "status": status,
    }


def load_production_readiness_report(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def render_production_readiness_summary(report: dict) -> None:
    groups = build_readiness_operator_checklist(report)
    blocked = groups["blocked"]
    warnings = groups["warning"]
    passed = groups["passed"]
    gate_tone = "critical" if blocked else ("warning" if warnings else "info")
    render_kv_section(
        "Production Readiness",
        [
            ("Decision", report.get("decision", "-")),
            ("Ready For Live", report.get("ready_for_live", "-")),
            ("Status", report.get("status", "-")),
            ("Blocking Checks", report.get("blocking_count", len(blocked))),
            ("Warnings", report.get("warning_count", len(warnings))),
            ("Generated At", report.get("generated_at", "-")),
        ],
        metric_label="Live Gate",
        metric_value=report.get("status", "-"),
    )
    render_compact_note(groups["operator_note"], tone=gate_tone)
    _render_readiness_status_strip(groups)
    _render_readiness_checklist(groups)


def build_readiness_operator_checklist(report: dict) -> dict:
    checks = [check for check in report.get("checks", []) if isinstance(check, dict)]
    grouped = {
        "blocked": [check for check in checks if check.get("status") == "blocked"],
        "warning": [check for check in checks if check.get("status") == "warning"],
        "passed": [check for check in checks if check.get("status") == "passed"],
    }

    if grouped["blocked"]:
        note = (
            "Live execution is blocked. Resolve every blocked check before BOT execution can "
            "move beyond dry-run."
        )
    elif grouped["warning"]:
        note = (
            "No hard readiness blocker remains, but warnings still need operator review before "
            "treating the run as production-safe."
        )
    else:
        note = "All readiness checks passed. Final order-level approval and risk gates still apply."

    return {
        **grouped,
        "counts": {
            "blocked": len(grouped["blocked"]),
            "warning": len(grouped["warning"]),
            "passed": len(grouped["passed"]),
        },
        "operator_note": note,
        "decision": report.get("decision", "-"),
        "generated_at": report.get("generated_at", "-"),
    }


def _render_readiness_status_strip(groups: dict) -> None:
    counts = groups["counts"]
    cards = [
        ("Blocked", counts["blocked"], "blocked"),
        ("Warnings", counts["warning"], "warning"),
        ("Passed", counts["passed"], "passed"),
    ]
    html = "".join(
        f"""
        <div class="readiness-count-card readiness-count-card--{escape(tone)}">
          <span>{escape(label)}</span>
          <strong>{escape(str(count))}</strong>
        </div>
        """
        for label, count, tone in cards
    )
    st.markdown(
        f"""
        <section class="readiness-status-strip">
          {html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_readiness_checklist(groups: dict) -> None:
    tabs = st.tabs(
        [
            f"Blocked ({groups['counts']['blocked']})",
            f"Warnings ({groups['counts']['warning']})",
            f"Passed ({groups['counts']['passed']})",
        ]
    )
    for tab, key, empty_text in [
        (tabs[0], "blocked", "No blocking checks."),
        (tabs[1], "warning", "No readiness warnings."),
        (tabs[2], "passed", "No passed checks yet."),
    ]:
        with tab:
            rows = _readiness_check_rows(groups[key])
            if not rows:
                render_compact_note(empty_text, tone="info")
            else:
                st.dataframe(rows, use_container_width=True, hide_index=True)


def _readiness_check_rows(checks: list[dict]) -> list[dict]:
    rows = []
    for check in checks:
        details = check.get("details") if isinstance(check.get("details"), dict) else {}
        rows.append(
            {
                "check": check.get("name", "-"),
                "status": check.get("status", "-"),
                "message": check.get("message", "-"),
                "key detail": _format_readiness_detail(details),
            }
        )
    return rows


def _format_readiness_detail(details: dict) -> str:
    priority_keys = [
        "mode",
        "enabled",
        "approved_for_live",
        "deployment_mode",
        "calibration_status",
        "clob_adapter_ready",
        "modes",
        "market_notional",
        "total_notional",
        "reason",
    ]
    for key in priority_keys:
        if key in details:
            return f"{key}={details[key]}"
    if not details:
        return "-"
    key = next(iter(details))
    return f"{key}={details[key]}"


def _render_dev_execution_harness(
    *,
    last_intent: dict,
    market_id: str,
    whitelist_path: Path,
    approval_db_path: Path,
    key_prefix: str,
) -> None:
    intent = last_intent.get("intent") or {}
    with st.expander("DEV ONLY: Gateway Test Harness", expanded=False):
        render_compact_note(
            "These controls are for local dry-run verification only. They do not place trades "
            "and should not be treated as production authorization.",
            tone="warning",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                "DEV: Add Market To Whitelist",
                key=f"{key_prefix}_dev_whitelist_{market_id or 'none'}",
                use_container_width=True,
                disabled=not bool(market_id),
            ):
                added = ensure_market_in_dev_whitelist(whitelist_path, market_id)
                st.session_state["last_dev_whitelist_update"] = {
                    "market_id": market_id,
                    "path": str(whitelist_path),
                    "added": added,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                st.toast(
                    f"{'Added' if added else 'Already whitelisted'} {market_id}",
                    icon="✅",
                )
                st.rerun()
        with c2:
            if st.button(
                "DEV: Create Local Approval",
                key=f"{key_prefix}_dev_approval_{intent.get('intent_id', 'none')}",
                use_container_width=True,
                disabled=not bool(intent.get("intent_id")),
            ):
                approval = create_local_test_approval(
                    db_path=approval_db_path,
                    intent=intent,
                )
                st.session_state["last_dev_approval"] = approval
                st.toast(f"Local approval created: {approval['approval_id']}", icon="✅")
                st.rerun()

        status = {
            "whitelist_update": st.session_state.get("last_dev_whitelist_update"),
            "approval": st.session_state.get("last_dev_approval"),
        }
        st.json(status)


def _render_gateway_dry_run_control(last_intent: dict, gateway_dir: Path, *, key_prefix: str) -> None:
    intent_path = Path(str(last_intent.get("pending_path") or ""))
    c1, c2 = st.columns([0.45, 0.55], vertical_alignment="center")
    with c1:
        if st.button(
            "Run Gateway Dry-Run Check",
            key=f"{key_prefix}_gateway_dry_run_{intent_path.name}",
            use_container_width=True,
            disabled=not intent_path.exists(),
            help="Validate this exact pending intent through execution-gateway without consuming the pending file.",
        ):
            with st.spinner("Running execution-gateway dry-run validation..."):
                result = run_gateway_dry_run_for_intent(
                    gateway_dir=gateway_dir,
                    intent_path=intent_path,
                )
            st.session_state["last_gateway_dry_run_result"] = result
            if result["ok"]:
                parsed = result.get("parsed_stdout") or {}
                execution_result = parsed.get("execution_result") or {}
                st.toast(
                    f"Gateway dry-run result: {execution_result.get('status', 'completed')}",
                    icon="✅",
                )
            else:
                st.warning("Gateway dry-run command failed.")
            st.rerun()
    with c2:
        st.caption(
            f"Gateway check target: `{intent_path.name if intent_path else '-'}`. "
            "This validates risk gates and approvals without consuming the pending intent."
        )


def _render_gate_cards(gate: dict) -> None:
    cards = [
        ("Data", "ok" if gate["data_aligned"] else "block", "aligned" if gate["data_aligned"] else "blocked"),
        ("Authorization", "ok" if gate["bot_authorized"] else "block", "on" if gate["bot_authorized"] else "off"),
        ("Whitelist", "ok" if gate["market_whitelisted"] else "warn", "yes" if gate["market_whitelisted"] else "no"),
        ("Gateway", "ok" if gate["gateway_ready"] else "warn", gate["gate_status"]),
    ]
    html_cards = "".join(
        (
            f"<div class='exec-gate-card exec-gate-card--{escape(tone)}'>"
            f"<div class='exec-gate-label'>{escape(label)}</div>"
            f"<div class='exec-gate-value'>{escape(value)}</div>"
            "</div>"
        )
        for label, tone, value in cards
    )
    st.markdown(
        f"""
        <style>
        .exec-gate-grid {{
            display:grid;
            grid-template-columns:repeat(4,minmax(0,1fr));
            gap:0.38rem;
            margin:0.42rem 0;
        }}
        .exec-gate-card {{
            border:1px solid rgba(35,72,82,0.14);
            border-radius:14px;
            background:linear-gradient(180deg,rgba(255,255,255,0.94),rgba(248,246,239,0.84));
            padding:0.48rem 0.56rem;
            box-shadow:0 8px 20px rgba(49,77,75,0.05);
        }}
        .exec-gate-card--ok {{ border-color:rgba(15,159,113,0.35); }}
        .exec-gate-card--warn {{ border-color:rgba(196,122,21,0.35); }}
        .exec-gate-card--block {{ border-color:rgba(196,77,70,0.35); }}
        .exec-gate-label {{
            color:#667782;
            font-family:"SF Mono","Menlo",monospace;
            font-size:0.58rem;
            font-weight:900;
            letter-spacing:0.08em;
            text-transform:uppercase;
        }}
        .exec-gate-value {{
            margin-top:0.16rem;
            color:#17252b;
            font-family:"Avenir Next Condensed","DIN Condensed","Trebuchet MS",sans-serif;
            font-size:1rem;
            font-weight:950;
            line-height:1.05;
        }}
        @media (max-width: 900px) {{
            .exec-gate-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
        }}
        </style>
        <div class='exec-gate-grid'>{html_cards}</div>
        """,
        unsafe_allow_html=True,
    )


def _market_id(payload: dict | None) -> str:
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("market_id") or "")


def _price_for_outcome(market_snapshot: dict | None, outcome: str) -> float | None:
    if not market_snapshot:
        return None
    key = "yes_price" if outcome == "yes" else "no_price"
    raw = market_snapshot.get(key)
    if raw is None:
        raw = market_snapshot.get("market_probability")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _is_market_whitelisted(path: Path, market_id: str) -> bool:
    if not market_id or not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return any(line.strip() == f"- {market_id}" for line in text.splitlines())
