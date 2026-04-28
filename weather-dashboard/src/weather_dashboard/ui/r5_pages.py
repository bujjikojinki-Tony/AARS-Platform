from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from html import escape
from math import isnan
from pathlib import Path
import re
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from weather_dashboard.settings import OUTPUT_DIR, PAGE_CONTEXT_JSON
from weather_dashboard.ui.action_policy import decide_action_visibility
from weather_dashboard.ui.compact_panel import (
    default_market_evidence_curve_legend_items,
    default_state_legend_items,
    render_chart_legend_card,
    render_legend_card,
)


def build_command_context_view(
    *,
    workstation_view: dict | None,
    page_context: dict | None = None,
    bot_authorized: bool = False,
) -> dict:
    workstation_view = workstation_view if isinstance(workstation_view, dict) else {}
    page_context = page_context if isinstance(page_context, dict) else {}
    top = _dict(workstation_view.get("top_parameter_view"))
    latest_gate = _dict(workstation_view.get("latest_gate"))
    gate_panel = _dict(workstation_view.get("gate_advisory_panel"))
    advisory = _dict(gate_panel.get("advisory_summary"))
    validation = _dict(workstation_view.get("validation_compare_panel"))
    buy_sell = _dict(workstation_view.get("buy_sell_decision_panel"))
    opportunity_context = _dict(workstation_view.get("opportunity_context") or workstation_view.get("entry_context"))
    selected_market_id = _first_text(
        page_context.get("selected_market_id"),
        workstation_view.get("selected_market_id"),
        top.get("market_id"),
        "",
    )
    entry_context = page_context.get("entry_context") if isinstance(page_context.get("entry_context"), dict) else {}
    next_action = _first_text(
        entry_context.get("recommended_action"),
        advisory.get("recommended_operator_action"),
        "Review evidence",
    )
    can_execute = _truthy(latest_gate.get("can_execute"))
    primary_block_reason = _first_text(latest_gate.get("primary_block_reason"), "Validation coverage < 80%")
    page_context = {
        "schema_version": "page_context.v1",
        "source_page": page_context.get("source_page") or "workstation",
        "target_page": page_context.get("target_page") or "command",
        "selected_market_id": selected_market_id or None,
        "selected_signal_id": page_context.get("selected_signal_id"),
        "selected_row_id": page_context.get("selected_row_id"),
        "entry_reason": page_context.get("entry_reason") or "send_to_command",
        "entry_context": entry_context,
        "upstream_refs": page_context.get("upstream_refs") if isinstance(page_context.get("upstream_refs"), dict) else {},
    }
    return {
        **workstation_view,
        "schema_version": "command_context_view.v1",
        "selected_market_id": selected_market_id,
        "page_context": page_context,
        "entry_context": {
            "source_page": page_context.get("source_page"),
            "target_page": page_context.get("target_page"),
            "selected_market_id": selected_market_id,
            "entry_reason": page_context.get("entry_reason"),
            "recommended_action": next_action,
            "best_model": _first_text(entry_context.get("best_model"), opportunity_context.get("best_model"), "-"),
            "best_source_stack": entry_context.get("best_source_stack") or opportunity_context.get("best_source_stack") or [],
            "validation_coverage": validation.get("label_coverage"),
        },
        "command_context": {
            "current_state": "ALLOW" if can_execute else "BLOCKED",
            "primary_block_reason": primary_block_reason,
            "next_operator_action": next_action,
            "research_direction": _first_text(buy_sell.get("decision_outcome"), "review_evidence"),
            "research_direction_reason": _first_text(buy_sell.get("decision_reason"), primary_block_reason),
            "market_implied_probability": buy_sell.get("market_implied_probability", "-"),
            "fair_value": buy_sell.get("fair_value", "-"),
            "edge": buy_sell.get("edge", "-"),
            "available_actions": [
                "open_workstation",
                "review_evidence",
                "acknowledge_signal",
                "mute_signal",
                "create_pending_intent",
                "run_dry_run_check",
            ],
            "disabled_actions": [] if can_execute else ["live_execute"],
            "bot_authorized": bool(bot_authorized),
        },
        "command_gate_summary": {
            "gate_status": "ALLOW" if can_execute else "BLOCKED",
            "primary_block_reason": primary_block_reason,
            "validation_coverage": validation.get("label_coverage"),
        },
    }


def render_r5_command_page(
    view: dict | None,
    *,
    bot_authorized: bool = False,
    page_context: dict | None = None,
    on_open_workstation=None,
) -> None:
    _render_r5_theme()
    view = view if isinstance(view, dict) else {}
    page_context = page_context if isinstance(page_context, dict) else {}
    view = build_command_context_view(
        workstation_view=view,
        page_context=page_context,
        bot_authorized=bot_authorized,
    )
    top = _dict(view.get("top_parameter_view"))
    latest_gate = _dict(view.get("latest_gate"))
    gate_panel = _dict(view.get("gate_advisory_panel"))
    advisory = _dict(gate_panel.get("advisory_summary"))
    validation = _dict(view.get("validation_compare_panel"))
    latest_alert = _dict(view.get("latest_alert"))
    latest_anomaly = _dict(view.get("latest_anomaly"))
    command_context = _dict(view.get("command_context"))

    city = _first_text(top.get("location_name"), top.get("city"), "New York, US")
    question = _first_text(top.get("market_question"), top.get("question"), "Rainfall > 50mm in 72h")
    market_id = _first_text(
        page_context.get("selected_market_id"),
        top.get("market_id"),
        view.get("selected_market_id"),
        "mkt_ny_rain_50mm_72h",
    )
    can_execute = _truthy(latest_gate.get("can_execute"))
    gate_status = "ALLOW" if can_execute else "BLOCKED"
    alert = _first_text(latest_alert.get("severity"), "red").upper()
    anomaly_score = _first_text(latest_anomaly.get("anomaly_score"), "0.76")
    next_action = _first_text(
        _dict(page_context.get("entry_context")).get("recommended_action"),
        advisory.get("recommended_operator_action"),
        "Review evidence",
    )
    research_direction = _first_text(command_context.get("research_direction"), "review_evidence")
    research_direction_reason = _first_text(command_context.get("research_direction_reason"), "Research direction unavailable.")
    research_market_probability = _first_text(command_context.get("market_implied_probability"), "-")
    research_fair_value = _first_text(command_context.get("fair_value"), "-")
    research_edge = _first_text(command_context.get("edge"), "-")
    block_reason = _first_text(latest_gate.get("primary_block_reason"), "Validation coverage < 80%")
    validation_coverage = _pct(validation.get("label_coverage"), "72.3%")
    entry_source = _format_page_context_source(page_context)
    entry_reason = _first_text(page_context.get("entry_reason"), "send_to_command")
    pending_intent = st.session_state.get("command_pending_intent")
    has_pending_intent = isinstance(pending_intent, dict) and str(pending_intent.get("market_id") or "") == str(market_id)
    action_context = {
        "market_id": market_id,
        "gate_allow": can_execute,
        "pending_intent": has_pending_intent,
        "gateway_available": True,
        "valid_approval": False,
        "live_mode_enabled": False,
        "operator_reason": next_action,
    }
    pending_intent_decision = decide_action_visibility("create_pending_intent", page="command", context=action_context)
    dry_run_decision = decide_action_visibility("run_dry_run_check", page="command", context=action_context)
    request_approval_decision = decide_action_visibility("request_approval", page="command", context=action_context)
    live_execute_decision = decide_action_visibility("live_execute", page="command", context=action_context)

    action_cols = st.columns([1.15, 1.15, 4.7], gap="small")
    if action_cols[0].button(
        "Open Workstation",
        key=f"cmd_open_workstation_{sanitize_text(str(market_id or city))}",
        use_container_width=True,
    ):
        if on_open_workstation is not None:
            on_open_workstation()
        st.rerun()
    action_cols[1].button(
        "Command Context",
        key=f"cmd_context_state_{sanitize_text(str(market_id or city))}",
        use_container_width=True,
        disabled=True,
    )
    action_cols[2].caption(f"Entry Source: {entry_source} · Reason: {entry_reason}")

    tool_cols = st.columns([0.9, 1.15, 0.9, 3.35], gap="small")
    if tool_cols[0].button(
        "Refresh",
        key=f"cmd_refresh_{sanitize_text(str(market_id or city))}",
        use_container_width=True,
    ):
        _write_ui_action_audit("command_refresh", market_id=market_id, page="command", detail={"city": city})
        st.toast("Command context refreshed.", icon="🔄")
        st.rerun()
    tool_cols[1].download_button(
        "Export Context",
        data=json.dumps(
            {
                "market_id": market_id,
                "city": city,
                "question": question,
                "page_context": page_context,
                "latest_gate": latest_gate,
                "latest_alert": latest_alert,
                "latest_anomaly": latest_anomaly,
            },
            ensure_ascii=False,
            indent=2,
        ),
        file_name=f"command_context_{sanitize_text(str(market_id))}.json",
        mime="application/json",
        use_container_width=True,
        key=f"cmd_export_context_{sanitize_text(str(market_id or city))}",
    )
    if tool_cols[2].button(
        "View History",
        key=f"cmd_view_history_{sanitize_text(str(market_id or city))}",
        use_container_width=True,
    ):
        _navigate_page(
            source_page="command",
            target_page="history",
            selected_market_id=market_id,
            entry_reason="view_history",
            entry_context={"city": city, "question": question, "gate_status": gate_status},
        )
        st.toast("Opening History with the current command context.", icon="🕘")
        st.rerun()
    tool_cols[3].caption("Live actions below update runtime state, audit notes, or current page navigation.")

    st.html(
        f"""
        <div class="r5-command-shell">
          <div class="r5-topbar">
            <div>
              <div class="r5-title">COMMAND CENTER <span>(操作员决策闭环)</span></div>
              <div class="r5-subtitle">Operator action closure, gate authorization and audit capture.</div>
              <div class="r5-subtitle">Entry Source: {escape(entry_source)} · Reason: {escape(entry_reason)}</div>
            </div>
            <div class="r5-top-actions"><span>Live Runtime</span><span>Audit Enabled</span><span>Dry-run Only</span></div>
          </div>
          <div class="r5-command-context">
            <div class="wide"><span>SELECTED MARKET</span><strong>{escape(city)} · {escape(question)}</strong><em>Market ID: {escape(market_id)} · Focus Market</em></div>
            <div><span>PRIMARY STATE</span><strong class="r5-red">ALERT {escape(alert)}</strong></div>
            <div><span>GATE STATUS</span><strong class="{'r5-green' if can_execute else 'r5-red'}">{escape(gate_status)}</strong></div>
            <div><span>NEXT ACTION</span><strong>{escape(next_action)}</strong></div>
            <div><span>ENTRY SOURCE</span><strong>{escape(entry_source)}</strong></div>
            <div><span>LAST UPDATED</span><strong>30s ago</strong><em>2026-04-24 14:35:12 UTC</em></div>
          </div>
        </div>
        """
    )

    gate_col, decision_col, auth_col = st.columns([0.27, 0.43, 0.30], gap="small")
    with gate_col:
        _panel(
            "1. GATE STACK (执行门控)",
            _gate_stack_html(
                [
                    ("Market Gate", "PASS", "Market configuration valid", "green", ""),
                    ("Evidence Gate", "WARN", "Evidence quality acceptable", "amber", f"Validation coverage {validation_coverage} < 80%<br><span>Open validation detail</span>"),
                    ("Resolver Gate", "PASS", "Resolver status healthy", "green", ""),
                    ("Probability Gate", "WARN", "Probability within acceptable band", "amber", f"Anomaly score high ({escape(anomaly_score)})<br><span>Open probability detail</span>"),
                    ("Execution Gate", "BLOCK", "Execution conditions not met", "red", f"Blocking Reason:<br>{escape(block_reason)}<br><br>Required Action:<br>Improve validation coverage or override with approval"),
                ]
            ),
        )
        if st.button(
            "View Gate Detail",
            key=f"cmd_gate_detail_{sanitize_text(str(market_id or city))}",
            use_container_width=True,
        ):
            st.session_state["r5_last_gate_detail_market"] = market_id
            _write_ui_action_audit("view_gate_detail", market_id=market_id, page="command")
            st.toast(f"Gate detail opened for {city}.", icon="🛡️")
    with decision_col:
        _panel(
            "2. OPERATOR DECISION",
            f"""
            <div class="r5-command-reco">
              <div class="r5-warning-icon">!</div>
              <div><span>RECOMMENDED NEXT ACTION</span><strong>{escape(next_action)} before dry-run.</strong><p>Execution gate is <b>BLOCKED</b> due to {escape(block_reason).lower()}.</p></div>
            </div>
            <div class="r5-command-metrics">
              <div><span>Research Direction</span><strong>{escape(research_direction)}</strong></div>
              <div><span>Market Prob</span><strong>{escape(research_market_probability)}</strong></div>
              <div><span>Fair Value</span><strong>{escape(research_fair_value)}</strong></div>
              <div><span>Edge</span><strong>{escape(research_edge)}</strong></div>
            </div>
            <div class="r5-muted">{escape(research_direction_reason)}</div>
            <div class="r5-command-metrics">
              <div><span>Severity</span><strong class="r5-red">● RED</strong></div>
              <div><span>Anomaly Score</span><strong>{escape(anomaly_score)}</strong></div>
              <div><span>Validation Coverage</span><strong>{escape(validation_coverage)}</strong></div>
              <div><span>Confidence</span><strong class="r5-green">High</strong></div>
              <div><span>Liquidity</span><strong class="r5-green">High</strong></div>
            </div>
            <div class="r5-command-section-label">AVAILABLE ACTIONS</div>
            <div class="r5-muted">Action glyphs are status hints only. The buttons below are the live controls.</div>
            <div class="r5-action-grid">
              {_action_card('Open Workstation', 'View full market analysis & evidence', 'open')}
              {_action_card('Create Pending Intent', 'Create a pending trading intent', 'intent')}
              {_action_card('Review Evidence', 'View evidence & validation detail', 'evidence')}
              {_action_card('Run Dry-run Check', 'Check with gateway (dry-run only)', 'play')}
              {_action_card('Acknowledge Signal', 'Mark this signal as acknowledged', 'ack')}
              {_action_card('Request Approval', 'Requires pending intent', 'locked', disabled=True)}
              {_action_card('Mute Signal', 'Temporarily mute this alert/signal', 'mute')}
              {_action_card('Live Execute', 'Disabled (gate blocked)', 'locked', disabled=True)}
            </div>
            """,
        )
        live_action_specs = [
            (
                "Open Workstation",
                "View full market analysis & evidence",
                "open",
                None,
                lambda: (
                    on_open_workstation() if on_open_workstation is not None else _navigate_page(
                        source_page="command",
                        target_page="workstation",
                        selected_market_id=market_id,
                        entry_reason="open_workstation",
                        entry_context={"city": city, "question": question, "gate_status": gate_status},
                    )
                ),
            ),
            (
                "Review Evidence",
                "View evidence & validation detail",
                "evidence",
                None,
                lambda: (
                    _navigate_page(
                        source_page="command",
                        target_page="evidence_raw",
                        selected_market_id=market_id,
                        entry_reason="review_evidence",
                        entry_context={"city": city, "question": question, "gate_status": gate_status},
                    )
                ),
            ),
            (
                "Create Pending Intent",
                "Create a pending trading intent",
                "intent",
                pending_intent_decision,
                lambda: (
                    st.session_state.__setitem__(
                        "command_pending_intent",
                        {
                            "market_id": market_id,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "mode": "dry_run_review",
                        },
                    )
                ),
            ),
            (
                "Run Dry-run Check",
                "Check with gateway (dry-run only)",
                "play",
                dry_run_decision,
                lambda: (
                    st.session_state.__setitem__(
                        "command_last_dry_run",
                        {
                            "market_id": market_id,
                            "status": "passed" if can_execute else "blocked",
                            "checked_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                ),
            ),
            (
                "Acknowledge Signal",
                "Mark this signal as acknowledged",
                "ack",
                None,
                lambda: st.session_state.__setitem__("command_last_ack_market", market_id),
            ),
            (
                "Mute Signal",
                "Temporarily mute this alert/signal",
                "mute",
                None,
                lambda: st.session_state.__setitem__("command_last_muted_market", market_id),
            ),
            (
                "Request Approval",
                "Requires pending intent",
                "locked",
                request_approval_decision,
                lambda: None,
            ),
            (
                "Live Execute",
                "Disabled (gate blocked)",
                "locked",
                live_execute_decision,
                lambda: None,
            ),
        ]
        live_cols = st.columns(2, gap="small")
        for idx, (label, subtitle, icon, decision, handler) in enumerate(live_action_specs):
            col = live_cols[idx % 2]
            with col:
                disabled = bool(decision.disabled) if decision is not None else False
                help_text = None if decision is None or decision.allowed else decision.reason
                if st.button(
                    f"{label}",
                    key=f"cmd_live_{sanitize_text(str(market_id or city))}_{sanitize_text(label)}",
                    use_container_width=True,
                    disabled=disabled,
                    help=help_text,
                ):
                    if label == "Open Workstation":
                        if on_open_workstation is not None:
                            on_open_workstation()
                        else:
                            _navigate_page(
                                source_page="command",
                                target_page="workstation",
                                selected_market_id=market_id,
                                entry_reason="open_workstation",
                                entry_context={"city": city, "question": question, "gate_status": gate_status},
                            )
                        st.rerun()
                    elif label == "Review Evidence":
                        _navigate_page(
                            source_page="command",
                            target_page="evidence_raw",
                            selected_market_id=market_id,
                            entry_reason="review_evidence",
                            entry_context={"city": city, "question": question, "gate_status": gate_status},
                        )
                        st.toast("Opening Evidence / Raw from Command.", icon="🧾")
                        st.rerun()
                    elif label == "Create Pending Intent":
                        st.session_state["command_pending_intent"] = {
                            "market_id": market_id,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "mode": "dry_run_review",
                        }
                        _write_ui_action_audit("create_pending_intent", market_id=market_id, page="command")
                        st.toast("Pending intent created for dry-run review.", icon="🧾")
                    elif label == "Run Dry-run Check":
                        st.session_state["command_last_dry_run"] = {
                            "market_id": market_id,
                            "status": "passed" if can_execute else "blocked",
                            "checked_at": datetime.now(timezone.utc).isoformat(),
                        }
                        _write_ui_action_audit("run_dry_run_check", market_id=market_id, page="command")
                        st.toast("Dry-run check recorded.", icon="▶")
                    elif label == "Acknowledge Signal":
                        st.session_state["command_last_ack_market"] = market_id
                        _write_ui_action_audit("acknowledge_signal", market_id=market_id, page="command")
                        st.toast(f"Signal acknowledged for {city}.", icon="✅")
                    elif label == "Mute Signal":
                        st.session_state["command_last_muted_market"] = market_id
                        _write_ui_action_audit("mute_signal", market_id=market_id, page="command")
                        st.toast(f"Signal muted temporarily for {city}.", icon="🔕")
                    st.rerun()
                st.caption(f"{icon.upper()} · {subtitle}")
        note_key = f"cmd_note_{sanitize_text(str(market_id or city))}"
        note_value = st.text_area(
            "Command note",
            key=note_key,
            placeholder="Add your note here...",
            height=80,
        )
        note_actions = st.columns(2, gap="small")
        if note_actions[0].button(
            "Save Note",
            key=f"cmd_save_note_{sanitize_text(str(market_id or city))}",
            use_container_width=True,
        ):
            st.session_state["command_saved_note"] = {
                "market_id": market_id,
                "note": note_value.strip(),
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
            _write_ui_action_audit(
                "save_note",
                market_id=market_id,
                page="command",
                detail={"note": note_value.strip()[:240]},
            )
            st.toast("Command note saved.", icon="📝")
    with auth_col:
        _panel(
            "3. AUTHORIZATION & GATEWAY",
            "".join(
                [
                    _gateway_row("BOT Authorization", "ON" if bot_authorized else "OFF", "green" if bot_authorized else "neutral"),
                    _gateway_row("Approval Status", "None", "neutral"),
                    _gateway_row("Pending Intent", "Present" if has_pending_intent else "None", "green" if has_pending_intent else "neutral"),
                    _gateway_row("Gateway Mode", "DRY-RUN ONLY", "blue"),
                    _gateway_row("Gateway Connection", "● Connected", "green"),
                    _gateway_row("Latest Dry-run Result", gate_status, "green" if can_execute else "red"),
                    _gateway_row("Kill Switch", "SAFE (OFF)", "green"),
                    _gateway_row("Max Exposure Limit", "$1,000,000", "neutral"),
                    _gateway_row("Current Exposure", "$324,120 (32.4%)", "green"),
                    _gateway_row("Risk Status", "WITHIN LIMIT", "green"),
                ]
            ),
        )
        auth_actions = st.columns(2, gap="small")
        if auth_actions[0].button(
            "View Gateway Detail",
            key=f"cmd_gateway_detail_{sanitize_text(str(market_id or city))}",
            use_container_width=True,
        ):
            st.session_state["command_gateway_detail_market"] = market_id
            _write_ui_action_audit("view_gateway_detail", market_id=market_id, page="command")
            st.toast("Gateway and risk detail opened.", icon="🔐")
        auth_actions[1].button(
            "Request Approval",
            key=f"cmd_request_approval_{sanitize_text(str(market_id or city))}",
            use_container_width=True,
            disabled=request_approval_decision.disabled,
            help=None if request_approval_decision.allowed else request_approval_decision.reason,
        )
        st.caption(f"Live Execute: {'allowed' if live_execute_decision.allowed else live_execute_decision.reason}")

    audit_col, context_col = st.columns([0.61, 0.39], gap="small")
    with audit_col:
        _panel(
            "4. COMMAND AUDIT TRAIL (最近操作链)",
            _html_table(
                ["Time (UTC)", "Event", "Operator / System", "Detail", "Action"],
                [
                    ["14:35:01", "● Gate Check", "System", f"Execution gate {gate_status} ({block_reason})", "View"],
                    ["14:34:12", "● Evidence Review Started", "operator_local", "Opened evidence for validation review", "View"],
                    ["14:33:45", "● Market Selected", "operator_local", "Selected from Focus Market in Operations Monitor", "View"],
                    ["14:31:18", "● Signal Detected", "System", f"{question} detected", "View"],
                    ["14:30:55", "● Market Scanned", "Scanner", "Market scanned & anomaly detected", "View"],
                ],
            )
            + '<div class="r5-table-footer"><span></span><span>Use the live View History control above.</span></div>',
        )
    with context_col:
        _panel(
            "5. CONTEXT SUMMARY",
            f"""
            <div class="r5-context-summary">
              <div>{_kv('Market', city)}{_kv('Event', question)}{_kv('Observed', '42.6 mm')}{_kv('Forecast (P90)', '28.1 mm')}{_kv('Anomaly', '+14.5 mm (51.6%)')}{_kv('First Detected', '2026-04-24 14:31:18 UTC')}{_kv('Data Freshness', '● LIVE', 'green')}{_kv('Latest Update', '30s ago')}</div>
              <div><div class="r5-radar r5-radar--large"></div></div>
            </div>
            """,
        )
        if st.button(
            "Open In Workstation",
            key=f"cmd_context_open_workstation_{sanitize_text(str(market_id or city))}",
            use_container_width=True,
        ):
            _write_ui_action_audit("open_workstation", market_id=market_id, page="command")
            if on_open_workstation is not None:
                on_open_workstation()
            else:
                _navigate_page(
                    source_page="command",
                    target_page="workstation",
                    selected_market_id=market_id,
                    entry_reason="open_workstation",
                    entry_context={"city": city, "question": question, "gate_status": gate_status},
                )
            st.rerun()


def render_r5_workstation_page(
    view: dict | None,
    *,
    page_context: dict | None = None,
    on_send_to_command=None,
) -> None:
    _render_r5_theme()
    view = view if isinstance(view, dict) else {}
    page_context = view.get("page_context") if isinstance(view.get("page_context"), dict) else page_context
    top = _dict(view.get("top_parameter_view"))
    gate = _dict(view.get("gate_advisory_panel"))
    latest_gate = _dict(view.get("latest_gate"))
    opp = _dict(view.get("opportunity_context") or view.get("entry_context"))
    validation = _dict(view.get("validation_compare_panel"))
    buy_sell = _dict(view.get("buy_sell_decision_panel"))

    city = _first_text(top.get("location_name"), top.get("city"), "New York, US")
    question = _first_text(top.get("market_question"), top.get("question"), "Rainfall > 50mm in 72h")
    alert = _first_text((_dict(view.get("latest_alert"))).get("severity"), "red").upper()
    gate_status = "BLOCKED" if not _truthy(latest_gate.get("can_execute")) else "ALLOW"
    opportunity = _score(opp.get("opportunity_score"), 82)
    difficulty = _first_text(opp.get("difficulty_label"), "M").upper()[:1]
    confidence = _number(top.get("source_confidence"), 0.74)
    liquidity = _first_text(top.get("liquidity_label"), "High")
    fresh = _first_text(top.get("freshness_status"), "LIVE").upper()
    entry_source = _format_page_context_source(page_context)
    entry_reason = _first_text(page_context.get("entry_reason"), "open_workstation")
    current_market_id = str(view.get("selected_market_id") or top.get("market_id") or city)

    action_cols = st.columns([1.15, 1.15, 4.7], gap="small")
    if action_cols[0].button(
        "Review in Command",
        key=f"wk_send_to_command_{sanitize_text(str(view.get('selected_market_id') or city))}",
        use_container_width=True,
    ):
        if on_send_to_command is not None:
            on_send_to_command()
        st.rerun()
    action_cols[1].button(
        "Workstation Context",
        key=f"wk_context_state_{sanitize_text(str(view.get('selected_market_id') or city))}",
        use_container_width=True,
        disabled=True,
    )
    action_cols[2].caption(f"Entry Source: {entry_source} · Reason: {entry_reason}")

    tool_cols = st.columns([1.05, 1.15, 1.15, 3.05], gap="small")
    if tool_cols[0].button(
        "Open Charts",
        key=f"wk_open_charts_{sanitize_text(str(view.get('selected_market_id') or city))}",
        use_container_width=True,
    ):
        _navigate_page(
            source_page="workstation",
            target_page="charts",
            selected_market_id=current_market_id,
            entry_reason="open_charts",
            entry_context={"city": city, "question": question},
        )
        st.toast("Opening Charts from Workstation.", icon="📈")
        st.rerun()
    tool_cols[1].download_button(
        "Export Report",
        data=json.dumps(view, ensure_ascii=False, indent=2),
        file_name=f"workstation_{sanitize_text(str(view.get('selected_market_id') or city))}.json",
        mime="application/json",
        use_container_width=True,
        key=f"wk_export_{sanitize_text(str(view.get('selected_market_id') or city))}",
    )
    if tool_cols[2].button(
        "Review Evidence",
        key=f"wk_open_evidence_{sanitize_text(str(view.get('selected_market_id') or city))}",
        use_container_width=True,
    ):
        _navigate_page(
            source_page="workstation",
            target_page="evidence_raw",
            selected_market_id=current_market_id,
            entry_reason="review_evidence",
            entry_context={"city": city, "question": question},
        )
        st.toast("Opening Evidence / Raw from Workstation.", icon="🧾")
        st.rerun()
    tool_cols[3].caption("These controls now update runtime navigation or export the active workstation payload.")

    st.html(
        f"""
        <div class="r5-page">
          <div class="r5-topbar">
            <div>
              <div class="r5-title">WORKSTATION <span>(单市场深度分析)</span></div>
              <div class="r5-market-head">
                <strong>{escape(city)}</strong><span class="r5-star">★</span>
                <span class="r5-pill r5-pill--red">ALERT {escape(alert)}</span>
                <span class="r5-pill r5-pill--red">GATE {escape(gate_status)}</span>
              </div>
              <div class="r5-subtitle">{escape(question)}</div>
              <div class="r5-subtitle">Entry Source: {escape(entry_source)} · Reason: {escape(entry_reason)}</div>
            </div>
            <div class="r5-top-actions"><span>Evidence Guided</span><span>Validation Aware</span><span>Research Mode</span></div>
          </div>
          <div class="r5-kpi-strip">
            {_metric('Opportunity', opportunity, 'green')}
            {_metric('Difficulty', difficulty, 'amber')}
            {_metric('Confidence', f'{confidence:.2f}', 'green')}
            {_metric('Liquidity', liquidity, 'green')}
            {_metric('Data Freshness', fresh, 'green' if fresh in {'LIVE', 'FRESH'} else 'amber')}
            {_metric('Last Scan', '30s ago', 'neutral')}
            {_metric('Auto Refresh', 'ON', 'green')}
          </div>
        </div>
        """
    )
    active_tab = _render_live_tabs(
        ["Overview", "Observations", "Models", "Signals", "Validation", "Evidence", "Strategy", "Notes"],
        key=f"wk_active_tab_{sanitize_text(current_market_id)}",
    )
    if active_tab != "Overview":
        _render_workstation_secondary_tab(active_tab, current_market_id=current_market_id, city=city, question=question)
        return

    left, mid, right = st.columns([0.28, 0.43, 0.29], gap="small")
    with left:
        _panel(
            "1. CURRENT RISK SUMMARY",
            f"""
            <div class="r5-risk-line"><span>ALERT RED</span><span>Since 13:41 UTC</span></div>
            {_kv('Gate Status', gate_status, 'red' if gate_status == 'BLOCKED' else 'green')}
            {_kv('Block Reason', _first_text(latest_gate.get('primary_block_reason'), 'Validation coverage < 80%'))}
            {_kv('Next Action', _first_text((_dict(gate.get('advisory_summary'))).get('recommended_operator_action'), 'Review evidence'))}
            """,
        )
        if st.button(
            "View Gate Detail",
            key=f"wk_gate_detail_{sanitize_text(current_market_id)}",
            use_container_width=True,
        ):
            st.session_state["workstation_last_gate_detail_market"] = current_market_id
            _write_ui_action_audit("view_gate_detail", market_id=current_market_id, page="workstation")
            st.toast("Gate detail opened from Workstation.", icon="🛡️")
        _panel(
            "2. MARKET SNAPSHOT",
            "".join(
                [
                    _kv("Location", city),
                    _kv("Region", _first_text(top.get("region"), "Northeast")),
                    _kv("Time Window", _first_text(top.get("time_window"), "72 hours")),
                    _kv("Event Type", _first_text(top.get("market_family"), "Rainfall")),
                    _kv("Threshold", _first_text(top.get("threshold"), "> 50 mm")),
                    _kv("Climatology", "P90"),
                    _kv("Season", "Spring"),
                ]
            ),
        )
    with mid:
        _panel("3. OBSERVED VS FORECAST", _chart_shell("Observed / ECMWF / GFS / ICON / NAM"))
        _render_forecast_chart()
        lower_a, lower_b = st.columns([1, 1], gap="small")
        with lower_a:
            _panel(
                "7. MODEL SUMMARY (Total 7 Days)",
                _html_table(
                    ["Model", "Total", "Bias", "Skill", "Trend"],
                    [
                        ["ECMWF", "128.4", "+12%", "0.78", "↑"],
                        ["GFS", "124.1", "+8%", "0.65", "↑"],
                        ["ICON", "119.6", "+5%", "0.66", "↑"],
                        ["NAM", "134.2", "+18%", "0.51", "↓"],
                    ],
                ),
            )
        with lower_b:
            _panel(
                "8. VALIDATION SUMMARY",
                _html_table(
                    ["Metric", "Value", "Status"],
                    [
                        ["Validation Coverage", _pct(validation.get("label_coverage"), "72.3%"), "Below 80%"],
                        ["Anomaly Score", "0.76", "High"],
                        ["Data Quality Score", "0.68", "Med"],
                        ["Consistency Score", "0.71", "Med"],
                    ],
                ),
            )
            if st.button(
                "View Validation Detail",
                key=f"wk_validation_detail_{sanitize_text(str(view.get('selected_market_id') or city))}",
                use_container_width=True,
            ):
                _navigate_page(
                    source_page="workstation",
                    target_page="charts",
                    selected_market_id=current_market_id,
                    entry_reason="view_validation_detail",
                    entry_context={"city": city, "question": question, "chart_preset": "validation_quality"},
                )
                st.toast("Opening validation-related charts.", icon="🧪")
                st.rerun()
            _panel(
                "9. BUY / SELL RESEARCH DIRECTION",
                "".join(
                    [
                        _kv("Decision", _first_text(buy_sell.get("decision_outcome"), "-")),
                        _kv("Reason", _first_text(buy_sell.get("decision_reason"), "-")),
                        _kv("Market Probability", _first_text(buy_sell.get("market_implied_probability"), "-")),
                        _kv("Fair Value", _first_text(buy_sell.get("fair_value"), "-")),
                        _kv("Edge", _first_text(buy_sell.get("edge"), "-")),
                        _kv("Probability Mode", _first_text(buy_sell.get("probability_mode"), "-")),
                        _kv("Validation Coverage", _first_text(buy_sell.get("validation_coverage"), "-")),
                        _kv("Boundary", _first_text(buy_sell.get("execution_boundary"), "gate_stack_api.v1_only")),
                    ]
                ),
            )
    with right:
        _panel(
            "4. SIGNAL STATUS",
            _html_table(
                ["Signal", "Status", "Score", "Since"],
                [
                    ["ALERT", "ACTIVE", "0.92", "13:41"],
                    ["ANOMALY", "ACTIVE", "0.76", "13:41"],
                    ["OPPORTUNITY", "ACTIVE", "0.82", "13:41"],
                    ["VALIDATION", "DEGRADED", "0.58", "13:41"],
                ],
            ),
        )
        _panel(
            "5. TOP DRIVERS",
            _html_table(
                ["Driver", "Impact", "Contribution"],
                [
                    ["Moisture Convergence", "High", "0.42"],
                    ["Low Pressure System", "High", "0.31"],
                    ["Wind Direction Change", "Med", "0.18"],
                    ["Temperature Anomaly", "Low", "0.09"],
                ],
            ),
        )
        obs_value = _first_text(top.get("display_value"), "42.6")
        _panel(
            "6. LATEST OBSERVATION",
            f"""
            <div class="r5-big-value">{escape(obs_value)} <span>mm</span></div>
            <div class="r5-muted">Rainfall (24h) · 2026-04-24 12:00 UTC</div>
            {_kv('Source', 'ECMWF API')}
            {_kv('Latency', '15 min')}
            {_kv('Coverage', '92%')}
            <div class="r5-radar"></div>
            """,
        )
        _panel(
            "10. RECOMMENDED ACTION",
            """
            <div class="r5-action-status active">Primary · Review evidence</div>
            <div class="r5-action-status">Next · Check validation gaps</div>
            <div class="r5-action-status">Conditional · Run dry-run review</div>
            <div class="r5-action-status">Fallback · Wait for new observations</div>
            """,
        )
        if st.button(
            "Open Workstation Assistant",
            key=f"wk_assistant_{sanitize_text(str(view.get('selected_market_id') or city))}",
            use_container_width=True,
        ):
            _write_ui_action_audit("open_workstation_assistant", market_id=current_market_id, page="workstation")
            st.toast("Workstation assistant context prepared.", icon="🤖")

    focus_key = "r5_focus_market_ids"
    focus_ids = set(st.session_state.get(focus_key, []))
    action_row_one = st.columns(4, gap="small")
    if action_row_one[0].button(
        "Add To Focus" if current_market_id not in focus_ids else "Focused",
        key=f"wk_focus_{sanitize_text(current_market_id)}",
        use_container_width=True,
        disabled=current_market_id in focus_ids,
    ):
        focus_ids.add(current_market_id)
        st.session_state[focus_key] = sorted(focus_ids)
        _write_ui_action_audit("add_to_focus", market_id=current_market_id, page="workstation")
        st.toast(f"Added {city} to focus markets.", icon="📌")
    if action_row_one[1].button(
        "Mute Signal",
        key=f"wk_mute_{sanitize_text(current_market_id)}",
        use_container_width=True,
    ):
        st.session_state["workstation_last_muted_market"] = current_market_id
        _write_ui_action_audit("mute_signal", market_id=current_market_id, page="workstation")
        st.toast("Signal muted from Workstation.", icon="🔕")
    if action_row_one[2].button(
        "Create Alert Rule",
        key=f"wk_create_rule_{sanitize_text(current_market_id)}",
        use_container_width=True,
    ):
        _navigate_page(
            source_page="workstation",
            target_page="alerts_rules",
            selected_market_id=current_market_id,
            entry_reason="create_alert_rule",
            entry_context={"city": city, "question": question},
        )
        st.toast("Opening Alerts & Rules with this market in mind.", icon="🚨")
        st.rerun()
    action_row_one[3].download_button(
        "Export Report",
        data=json.dumps(view, ensure_ascii=False, indent=2),
        file_name=f"workstation_report_{sanitize_text(current_market_id)}.json",
        mime="application/json",
        use_container_width=True,
        key=f"wk_export_report_{sanitize_text(current_market_id)}",
    )
    action_row_two = st.columns(3, gap="small")
    if action_row_two[0].button(
        "Share Context",
        key=f"wk_share_{sanitize_text(current_market_id)}",
        use_container_width=True,
    ):
        st.session_state["workstation_last_shared_market"] = current_market_id
        _write_ui_action_audit("share_context", market_id=current_market_id, page="workstation")
        st.toast("Share payload prepared locally.", icon="🔗")
    if action_row_two[1].button(
        "Open History",
        key=f"wk_history_{sanitize_text(current_market_id)}",
        use_container_width=True,
    ):
        _navigate_page(
            source_page="workstation",
            target_page="history",
            selected_market_id=current_market_id,
            entry_reason="open_history",
            entry_context={"city": city, "question": question},
        )
        st.toast("Opening History from Workstation.", icon="🕘")
        st.rerun()
    workstation_note = st.text_input(
        "Add Note",
        key=f"wk_note_{sanitize_text(current_market_id)}",
        placeholder="Add a workstation note...",
    )
    if action_row_two[2].button(
        "Save Note",
        key=f"wk_save_note_{sanitize_text(current_market_id)}",
        use_container_width=True,
    ):
        st.session_state["workstation_saved_note"] = {
            "market_id": current_market_id,
            "note": workstation_note.strip(),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        _write_ui_action_audit(
            "save_note",
            market_id=current_market_id,
            page="workstation",
            detail={"note": workstation_note.strip()[:240]},
        )
        st.toast("Workstation note saved.", icon="📝")


def render_r5_pipeline_page() -> None:
    _render_r5_theme()
    st.html(_page_header("PIPELINE", "数据管道与处理流程", "LIVE"))
    active_tab = _render_live_tabs(["Overview", "Scanner Health", "Data Sources", "Jobs", "Logs"], key="pipeline_active_tab")
    pipeline_actions = st.columns([1, 1, 1, 3], gap="small")
    if pipeline_actions[0].button("Run Diagnostics", key="pipeline_run_diagnostics", use_container_width=True):
        _navigate_page(source_page="pipeline", target_page="system", entry_reason="run_diagnostics")
        st.toast("Opening System diagnostics controls.", icon="🩺")
        st.rerun()
    if pipeline_actions[1].button("Open Data Sources", key="pipeline_open_data_sources", use_container_width=True):
        _navigate_page(source_page="pipeline", target_page="data_sources", entry_reason="open_data_sources")
        st.toast("Opening Data & Sources from Pipeline.", icon="🧰")
        st.rerun()
    pipeline_actions[2].download_button(
        "Export Pipeline",
        data=json.dumps({"page": "pipeline", "exported_at": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False, indent=2),
        file_name="pipeline_snapshot.json",
        mime="application/json",
        use_container_width=True,
        key="pipeline_export_snapshot",
    )
    pipeline_actions[3].caption("Pipeline controls are now live and route into System / Data & Sources instead of decorative chrome.")
    if active_tab != "Overview":
        _render_pipeline_secondary_tab(active_tab)
        return
    stages = [
        ("1. DISCOVERY SCANNER", "244", "Markets", "LIVE"),
        ("2. COLLECTION", "512", "Sources", "LIVE"),
        ("3. NORMALIZATION", "128,542", "Records", "LIVE"),
        ("4. VALIDATION", "124,874", "Validated", "LIVE"),
        ("5. SIGNAL ENGINE", "1,432", "Signals", "LIVE"),
        ("6. ALERT ROUTER", "68", "Alerts", "LIVE"),
    ]
    st.html(
        '<div class="r5-pipeline-flow">'
        + "".join(
            f"""
            <div class="r5-stage">
              <div class="r5-stage-title">{escape(name)} <span>{escape(status)}</span></div>
              <div class="r5-stage-icon">⌁</div>
              <div class="r5-stage-value">{escape(value)}</div>
              <div class="r5-muted">{escape(label)}</div>
              <div class="r5-stage-ok">✓</div>
            </div>
            """
            for name, value, label, status in stages
        )
        + "</div>"
    )
    a, b, c = st.columns([0.48, 0.28, 0.24], gap="small")
    with a:
        _panel(
            "PIPELINE METRICS (Last 1 Hour)",
            '<div class="r5-metric-grid">'
            + "".join(
                _metric_card(label, value, delta)
                for label, value, delta in [
                    ("Ingested", "128,542", "+12.4%"),
                    ("Validated", "124,874", "+11.8%"),
                    ("Signals Generated", "1,432", "+9.6%"),
                    ("Alerts Sent", "68", "-5.6%"),
                    ("Avg Latency", "2.3s", "+0.4s"),
                    ("Error Rate", "0.18%", "-0.05%"),
                ]
            )
            + "</div>",
        )
    with b:
        _panel(
            "TOP DATA SOURCES BY LATENCY",
            _html_table(
                ["Source", "Latency", "Status"],
                [["ECMWF API", "1.36s", "LIVE"], ["NWS API", "1.98s", "LIVE"], ["BOM API", "2.56s", "LIVE"], ["NOAA GFS", "1.82s", "LIVE"], ["EUMETSAT", "2.14s", "LIVE"]],
            ),
        )
    with c:
        _panel("DATA FLOW (Last 1 Hour)", _donut_legend([("Ingested", "128,542"), ("Validated", "124,874"), ("Rejected", "2,856"), ("Skipped", "812"), ("Error", "0")]))
        _panel("PIPELINE HEALTH", '<div class="r5-health-score">97%<span>Overall Health</span></div>')
    st.html(
        """
        <div class="r5-bottom-strip">
          <div>SCHEDULE<br><strong>Every 30 seconds</strong></div><div>NEXT RUN<br><strong>in 12s</strong></div>
          <div>PARALLEL JOBS<br><strong>8</strong></div><div>FAILED JOBS<br><strong>0</strong></div>
          <div>QUEUED JOBS<br><strong>3</strong></div><div>PIPELINE CONFIG<br><strong>View / Edit Configuration</strong></div>
        </div>
        """
    )


def render_r5_markets_page(df: pd.DataFrame | None) -> None:
    _render_r5_theme()
    rows = _market_rows(df)
    inventory_rows = _market_inventory_rows(rows)
    context = _write_markets_page_context(
        source_page="markets",
        target_page="markets",
        entry_reason="inventory_review",
        entry_context={
            "active_group": st.session_state.get("markets_group_filter", "All"),
            "active_watchlist": st.session_state.get("markets_watch_filter", "All"),
            "active_focus": st.session_state.get("markets_focus_filter", "All"),
            "active_resolver": st.session_state.get("markets_resolver_filter", "All"),
            "active_priority": st.session_state.get("markets_priority_filter", "All"),
        },
    )
    st.html(_page_header("Markets", "市场总览", "LIVE"))
    total_markets = len(inventory_rows)
    focus_markets = sum(1 for row in inventory_rows if row.get("group") == "FOCUS")
    watchlist_markets = sum(1 for row in inventory_rows if row.get("watchlist") in {"WATCHED", "CANDIDATE"})
    auto_markets = sum(1 for row in inventory_rows if row.get("group") == "AUTO")
    hidden_markets = sum(1 for row in inventory_rows if row.get("group") == "HIDDEN")
    resolver_issues = sum(1 for row in inventory_rows if row.get("resolver") not in {"OK", "LIVE"})
    st.html(
        '<div class="r5-market-stats">'
        + "".join(
            _stat_tile(label, value, delta)
            for label, value, delta in [
                ("Total Markets", str(total_markets), ""),
                ("Focus", str(focus_markets), "Opportunity-led"),
                ("Watchlist", str(watchlist_markets), "Tracked"),
                ("Auto Discovered", str(auto_markets), "Active"),
                ("Hidden / Removed", str(hidden_markets), "Locally hidden"),
                ("Resolver Issues", str(resolver_issues), "Needs review"),
            ]
        )
        + "</div>"
    )
    _render_markets_context_strip(
        active_group=_first_text(st.session_state.get("markets_group_filter"), "All"),
        selection_label="Inventory",
        selection_value=_first_text(_dict(context.get("entry_context")).get("active_group"), "All"),
        action_hint="Page: markets",
    )
    _render_markets_result_banner(
        "markets",
        fallback_title="Inventory ready",
        fallback_message="Markets inventory is ready for selection, focus, hide, and workstation handoff.",
    )
    st.caption(
        "Counts on this page describe the full managed inventory snapshot, including focus, watchlist, auto-discovered, and hidden/removed markets. "
        "The table below is paged, so `Total Markets` can be larger than the rows currently visible on screen."
    )
    market_filters = st.columns([1.4, 1, 1, 1, 1, 1], gap="small")
    search_text = market_filters[0].text_input("Search", placeholder="Search market or region...", key="markets_search_text")
    group_filter = market_filters[1].selectbox("Group", ["All", "FOCUS", "WATCH", "AUTO", "HIDDEN"], key="markets_group_filter")
    watch_filter = market_filters[2].selectbox("Watchlist", ["All", "WATCHED", "CANDIDATE", "REMOVED", "HIDDEN"], key="markets_watch_filter")
    focus_filter = market_filters[3].selectbox("Focus", ["All", "PINNED", "AUTO", "NO"], key="markets_focus_filter")
    resolver_filter = market_filters[4].selectbox("Resolver", ["All", "OK", "REVIEW", "DISABLED"], key="markets_resolver_filter")
    priority_filter = market_filters[5].selectbox("Scan Priority", ["All", "P1", "P2", "P3", "OFF"], key="markets_priority_filter")
    filtered_inventory = []
    for row in inventory_rows:
        hay = " ".join([row["market"], row["region"], row["signal"]]).lower()
        if search_text.strip() and search_text.lower().strip() not in hay:
            continue
        if group_filter != "All" and row["group"] != group_filter:
            continue
        if watch_filter != "All" and row["watchlist"] != watch_filter:
            continue
        if focus_filter != "All" and row["focus"] != focus_filter:
            continue
        if resolver_filter != "All" and row["resolver"] != resolver_filter:
            continue
        if priority_filter != "All" and row["scan_priority"] != priority_filter:
            continue
        filtered_inventory.append(row)
    if filtered_inventory:
        current_selection = st.session_state.get("markets_selected_inventory_row")
        if current_selection not in {row["market"] for row in filtered_inventory}:
            st.session_state["markets_selected_inventory_row"] = filtered_inventory[0]["market"]
    focus, watch, auto, hidden = st.columns([0.25, 0.25, 0.25, 0.25], gap="small")
    with focus:
        _panel("Focus Markets", _market_group_cards(inventory_rows, "FOCUS", limit=2))
    with watch:
        _panel("Watchlist Markets", _market_group_cards(inventory_rows, "WATCH", limit=2))
    with auto:
        _panel("Auto-discovered Markets", _market_group_cards(inventory_rows, "AUTO", limit=2))
    with hidden:
        _panel("Hidden / Removed", _market_group_cards(inventory_rows, "HIDDEN", limit=2))

    page_size = int(st.session_state.get("markets_page_size", 10))
    if page_size not in {10, 20, 50}:
        page_size = 10
    total_rows = len(filtered_inventory)
    total_pages = max(1, (total_rows + page_size - 1) // page_size) if total_rows else 1
    current_page = int(st.session_state.get("markets_current_page", 1))
    current_page = max(1, min(current_page, total_pages))
    paging_cols = st.columns([0.9, 0.8, 0.8, 1.0, 3.5], gap="small")
    page_size = paging_cols[0].selectbox(
        "Rows / page",
        [10, 20, 50],
        index=[10, 20, 50].index(page_size),
        key="markets_page_size",
    )
    total_pages = max(1, (total_rows + int(page_size) - 1) // int(page_size)) if total_rows else 1
    current_page = max(1, min(int(st.session_state.get("markets_current_page", 1)), total_pages))
    if paging_cols[1].button("‹ Prev", key="markets_page_prev", use_container_width=True, disabled=current_page <= 1):
        st.session_state["markets_current_page"] = current_page - 1
        st.rerun()
    if paging_cols[2].button("Next ›", key="markets_page_next", use_container_width=True, disabled=current_page >= total_pages):
        st.session_state["markets_current_page"] = current_page + 1
        st.rerun()
    selected_page = paging_cols[3].selectbox(
        "Page",
        list(range(1, total_pages + 1)),
        index=current_page - 1,
        key=f"markets_page_select_{page_size}_{total_rows}",
    )
    current_page = int(selected_page)
    st.session_state["markets_current_page"] = current_page
    page_start = (current_page - 1) * int(page_size)
    page_end = min(total_rows, page_start + int(page_size))
    page_rows = filtered_inventory[page_start:page_end]
    paging_cols[4].caption(
        f"Showing {page_start + 1 if page_rows else 0} to {page_end} of {total_rows} filtered inventory rows. "
        "Use the filters and page controls to browse the full market pool."
    )

    main, side = st.columns([0.76, 0.24], gap="small")
    with main:
        _panel(
            "Market Inventory",
            _html_table(
                ["Market", "Region", "Watchlist", "Focus", "Scan Priority", "Resolver", "Source", "Latest Signal", "Gate", "Freshness", "Action Hint"],
                [
                    [
                        row["market"],
                        row["region"],
                        row["watchlist"],
                        row["focus"],
                        row["scan_priority"],
                        row["resolver"],
                        row["source"],
                        row["signal"],
                        row["gate"],
                        row["fresh"],
                        row["action_hint"],
                    ]
                    for row in page_rows
                ],
            )
            + (
                f'<div class="r5-table-footer">Inventory view: focus / watchlist / hidden state, not opportunity ranking '
                f'<span>{escape(str(len(filtered_inventory)))} filtered · page {escape(str(current_page))} / {escape(str(total_pages))}</span></div>'
            ),
        )
    with side:
        selected_options = [row["market"] for row in filtered_inventory] or [row["market"] for row in inventory_rows]
        selected_label = st.selectbox(
            "Selected market",
            selected_options,
            key="markets_selected_inventory_row",
            label_visibility="collapsed",
        )
        selected_pool = filtered_inventory if filtered_inventory else inventory_rows
        selected = next((row for row in selected_pool if row["market"] == selected_label), selected_pool[0])
        _write_markets_page_context(
            source_page="markets",
            target_page="markets",
            selected_market_id=selected.get("market_id") or sanitize_text(selected["market"]),
            selected_row_id=selected.get("market_id") or sanitize_text(selected["market"]),
            entry_reason="selection_change",
            entry_context={
                "selected_market": selected["market"],
                "selected_group": selected["group"],
                "selected_watchlist": selected["watchlist"],
                "selected_focus": selected["focus"],
                "selected_scan_priority": selected["scan_priority"],
                "selected_resolver": selected["resolver"],
                "selected_source": selected["source"],
                "current_filters": {
                    "group": group_filter,
                    "watchlist": watch_filter,
                    "focus": focus_filter,
                    "resolver": resolver_filter,
                    "priority": priority_filter,
                    "search": search_text,
                },
            },
        )
        _panel(
            "Market Control Detail",
            "".join(
                [
                    _kv("Selected", selected["market"]),
                    _kv("Inventory State", selected["watchlist"]),
                    _kv("Focus State", selected["focus"]),
                    _kv("Scan Priority", selected["scan_priority"], "amber"),
                    _kv("Resolver", selected["resolver"], "green"),
                    _kv("Source", selected["source"], "green"),
                    _kv("Freshness Meaning", "LIVE = current snapshot · STALE = needs refresh · OFF = locally hidden/disabled"),
                    _kv("Update Mode", "Inventory state updates on UI actions; market fields refresh when dashboard autorefresh ticks"),
                ]
            ),
        )
        market_actions = st.columns(2, gap="small")
        if market_actions[0].button("View Workstation", key=f"markets_view_ws_{sanitize_text(selected['market'])}", use_container_width=True):
            _set_markets_result(
                "Workstation opened",
                f"Handed {selected['market']} to Workstation with inventory context.",
                "info",
            )
            _navigate_page(
                source_page="markets",
                target_page="workstation",
                selected_market_id=selected.get("market_id") or sanitize_text(selected["market"]),
                entry_reason="open_workstation",
                entry_context={"market": selected["market"], "inventory_state": selected["watchlist"], "focus_state": selected["focus"]},
            )
            st.toast(f"Opening workstation for {selected['market']}.", icon="🔎")
            st.rerun()
        if market_actions[1].button("Open Evidence", key=f"markets_open_ev_{sanitize_text(selected['market'])}", use_container_width=True):
            _set_markets_result(
                "Evidence opened",
                f"Handed {selected['market']} to Evidence / Raw with inventory context.",
                "info",
            )
            _navigate_page(
                source_page="markets",
                target_page="evidence_raw",
                selected_market_id=selected.get("market_id") or sanitize_text(selected["market"]),
                entry_reason="review_evidence",
                entry_context={"market": selected["market"], "inventory_state": selected["watchlist"]},
            )
            st.toast(f"Opening evidence for {selected['market']}.", icon="🧾")
            st.rerun()
        market_actions_2 = st.columns(2, gap="small")
        if market_actions_2[0].button("Add / Remove Focus", key=f"markets_focus_toggle_{sanitize_text(selected['market'])}", use_container_width=True):
            focus_key = "r5_focus_market_ids"
            current = {str(item) for item in st.session_state.get(focus_key, []) if str(item).strip()}
            market_key = selected.get("market_id") or sanitize_text(selected["market"])
            if market_key in current:
                current.remove(market_key)
                _set_markets_result(
                    "Focus removed",
                    f"{selected['market']} removed from focus markets.",
                    "warn",
                )
                st.toast(f"Removed {selected['market']} from focus.", icon="➖")
            else:
                current.add(market_key)
                _set_markets_result(
                    "Focus added",
                    f"{selected['market']} added to focus markets.",
                    "good",
                )
                st.toast(f"Added {selected['market']} to focus.", icon="📌")
            st.session_state[focus_key] = sorted(current)
            _write_ui_action_audit("toggle_focus", page="markets", detail={"market": selected["market"]})
        removed_key = "market_watchlist_removed"
        removed_rows = st.session_state.setdefault(removed_key, [])
        selected_market_id = selected.get("market_id") or sanitize_text(selected["market"])
        removed_ids = {
            str(item.get("market_id") or item.get("market") or "").strip()
            for item in removed_rows
            if isinstance(item, dict)
        }
        hide_label = "Restore Market" if selected_market_id in removed_ids else "Hide Market"
        if market_actions_2[1].button(hide_label, key=f"markets_hide_{sanitize_text(selected['market'])}", use_container_width=True):
            if selected_market_id in removed_ids:
                removed_rows[:] = [
                    item
                    for item in removed_rows
                    if str(item.get("market_id") or item.get("market") or "").strip() != selected_market_id
                ]
                _set_markets_result(
                    "Market restored",
                    f"{selected['market']} restored to active inventory.",
                    "good",
                )
                st.toast(f"Restored {selected['market']} to inventory.", icon="↩️")
                _write_ui_action_audit("restore_market", page="markets", detail={"market": selected["market"]})
            else:
                focus_ids = {
                    str(item)
                    for item in st.session_state.get("r5_focus_market_ids", [])
                    if str(item).strip()
                }
                if selected_market_id in focus_ids:
                    focus_ids.remove(selected_market_id)
                    st.session_state["r5_focus_market_ids"] = sorted(focus_ids)
                removed_rows.insert(
                    0,
                    {
                        "market_id": selected_market_id,
                        "market": selected["market"],
                        "region": selected["region"],
                        "removed_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                _set_markets_result(
                    "Market hidden",
                    f"{selected['market']} marked hidden locally.",
                    "warn",
                )
                st.toast(f"Marked {selected['market']} as hidden locally.", icon="🙈")
                _write_ui_action_audit("hide_market", page="markets", detail={"market": selected["market"]})
            st.session_state[removed_key] = removed_rows
            st.session_state["markets_hidden_market"] = selected["market"]
            st.session_state.pop("markets_selected_inventory_row", None)


def _write_markets_page_context(
    *,
    source_page: str,
    target_page: str,
    entry_reason: str,
    entry_context: dict[str, Any] | None = None,
    selected_market_id: str | None = None,
    selected_row_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": "page_context.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_page": source_page,
        "target_page": target_page,
        "selected_market_id": str(selected_market_id or "") or None,
        "selected_signal_id": None,
        "selected_row_id": str(selected_row_id or "") or None,
        "entry_reason": entry_reason,
        "entry_context": entry_context if isinstance(entry_context, dict) else {},
        "upstream_refs": {},
    }
    st.session_state["dashboard_page_context"] = payload
    try:
        PAGE_CONTEXT_JSON.parent.mkdir(parents=True, exist_ok=True)
        PAGE_CONTEXT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return payload


def _set_markets_result(title: str, message: str, tone: str) -> None:
    st.session_state.setdefault("markets_page_results", {})["markets"] = {
        "title": title,
        "message": message,
        "tone": tone,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def _render_markets_context_strip(active_group: str, selection_label: str, selection_value: str, action_hint: str) -> None:
    st.html(
        f"""
        <div class="settings-mid-card" style="padding:.58rem .68rem;margin:.1rem 0 .45rem;">
          <div class="settings-section-title" style="margin-top:0;">Current Context</div>
          <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.4rem;">
            <div class="settings-kv"><span>Page</span><strong>Markets</strong></div>
            <div class="settings-kv"><span>Group</span><strong>{escape(active_group)}</strong></div>
            <div class="settings-kv"><span>Selection</span><strong>{escape(selection_label)}</strong></div>
            <div class="settings-kv"><span>Value</span><strong>{escape(selection_value)}</strong></div>
          </div>
          <div class="settings-kv" style="margin-top:.35rem;"><span>Action</span><strong>{escape(action_hint)}</strong></div>
        </div>
        """
    )


def _render_markets_result_banner(page: str, *, fallback_title: str, fallback_message: str) -> None:
    results = st.session_state.get("markets_page_results", {})
    page_result = results.get(page) if isinstance(results, dict) else {}
    if not isinstance(page_result, dict) or not page_result:
        page_result = {
            "title": fallback_title,
            "message": fallback_message,
            "tone": "info",
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
    tone = str(page_result.get("tone") or "info")
    color = {"good": "#4bd968", "warn": "#ffb020", "danger": "#ff493f", "info": "#32b7ff"}.get(tone, "#32b7ff")
    st.html(
        f"""
        <div class="settings-mid-card" style="padding:.58rem .68rem;margin:.1rem 0 .45rem;border-left:4px solid {color};">
          <div class="settings-section-title" style="margin-top:0;">Last Action Result</div>
          <div class="settings-kv"><span>State</span><strong>{escape(str(page_result.get('title') or fallback_title))}</strong></div>
          <div class="settings-kv"><span>Message</span><strong>{escape(str(page_result.get('message') or fallback_message))}</strong></div>
          <div class="settings-kv"><span>Updated</span><strong>{escape(str(page_result.get('updated_at') or '-'))}</strong></div>
        </div>
        """
    )


def render_r5_charts_page(df: pd.DataFrame | None, history_df: pd.DataFrame | None = None, ts_df: pd.DataFrame | None = None) -> None:
    _render_r5_theme()
    context = st.session_state.get("dashboard_page_context")
    context = context if isinstance(context, dict) else {}
    preset_from_context = _dict(context.get("entry_context")).get("chart_preset")
    presets = ["Market Evidence", "Alert & Anomaly", "Source Freshness", "Validation Quality", "Opportunity Trend", "Custom"]
    default_preset = "Validation Quality" if preset_from_context == "validation_quality" else "Market Evidence"
    st.html(_page_header("Charts", "可视化图表", "LIVE", right="+ Add Chart · Last 7 Days"))
    preset_cols = st.columns([1.25, 1, 1, 1.2, 2.1], gap="small")
    active_preset = preset_cols[0].selectbox("Preset", presets, index=presets.index(default_preset), key="charts_active_preset")
    market_scope = preset_cols[1].selectbox("Market", ["All", "Current Context", "New York, US", "Houston, US", "London, UK"], key="charts_market_scope")
    time_window = preset_cols[2].selectbox("Window", ["Last 7 Days", "Last 24 Hours", "Last 30 Days"], key="charts_time_window")
    if preset_cols[3].button("Apply Chart View", key="charts_apply_view", use_container_width=True):
        _write_ui_action_audit(
            "apply_chart_view",
            page="charts",
            market_id=str(context.get("selected_market_id") or ""),
            detail={"preset": active_preset, "market_scope": market_scope, "time_window": time_window},
        )
        st.toast("Chart view updated.", icon="📈")
    preset_cols[4].caption(f"Context: {_format_page_context_source(context)}")
    st.html(f'<div class="r5-presetbar"><span>Preset: {escape(active_preset)} Timeline</span><span>Window: {escape(time_window)}</span><span>Mode: Trend analysis, not realtime alert intake</span></div>')
    legend_a, legend_b = st.columns(2, gap="small")
    with legend_a:
        render_legend_card(
            "State Legend",
            subtitle="Shared HMI meanings for runtime states and quality markers.",
            items=default_state_legend_items(),
        )
    with legend_b:
        render_chart_legend_card(
            "Curve Legend",
            subtitle="How the chart colors and markers should be read.",
            items=default_market_evidence_curve_legend_items(),
        )
    _panel("Market Evidence Timeline (同轴证据图)", "")
    st.plotly_chart(_market_evidence_timeline_chart(), use_container_width=True, config={"displayModeBar": False})
    c1, c2 = st.columns(2, gap="small")
    with c1:
        _panel("Anomaly Score Over Time (风险总趋势)", "")
        st.plotly_chart(_line_chart(["New York, US", "Houston, US", "London, UK", "São Paulo, BR"]), use_container_width=True, config={"displayModeBar": False})
        _panel("Forecast vs Observation Bias (预报与观测偏差)", "")
        st.plotly_chart(_bar_line_chart(), use_container_width=True, config={"displayModeBar": False})
        _panel("Market Alerts Over Time (市场告警趋势)", "")
        st.plotly_chart(_stacked_bar_chart(), use_container_width=True, config={"displayModeBar": False})
    with c2:
        _panel("Opportunity Score Distribution (机会分数分布)", "")
        st.plotly_chart(_hist_chart(), use_container_width=True, config={"displayModeBar": False})
        _panel("Data Freshness by Source (数据新鲜度 - 技术源)", _freshness_heatmap())
        _panel("Validation Coverage (验证覆盖率均值)", "")
        st.plotly_chart(_validation_line_chart(), use_container_width=True, config={"displayModeBar": False})


def render_r5_history_page(history_df: pd.DataFrame | None) -> None:
    _render_r5_theme()
    st.html(_page_header("History", "历史记录", "LIVE"))
    active_tab = _render_live_tabs(["Signals", "Alerts", "Actions", "Validation", "System Events"], key="history_active_tab")
    rows = _history_rows(history_df)
    ui_audit_rows = _load_ui_action_audit_rows(limit=80)
    history_filters = st.columns([1.2, 1, 1, 1, 1.2, 1], gap="small")
    history_search = history_filters[0].text_input("Search", placeholder="Search notes, sources...", key="history_search_text")
    market_filter = history_filters[1].selectbox("Market", ["All", *sorted({row[1] for row in rows + ui_audit_rows})], key="history_market_filter")
    event_filter = history_filters[2].selectbox("Event Type", ["All", *sorted({row[2] for row in rows + ui_audit_rows})], key="history_event_filter")
    severity_filter = history_filters[3].selectbox("Severity", ["All", *sorted({row[3] for row in rows + ui_audit_rows})], key="history_severity_filter")
    if history_filters[4].button("Open Replay", key="history_open_replay", use_container_width=True):
        _write_ui_action_audit("open_replay", page="history")
        st.toast("Replay context opened from History.", icon="🎞️")
    history_filters[5].download_button(
        "Export History",
        data=json.dumps(rows, ensure_ascii=False, indent=2),
        file_name="history_rows.json",
        mime="application/json",
        use_container_width=True,
        key="history_export_rows",
    )
    combined_rows = rows + ui_audit_rows
    filtered_rows = []
    for row in combined_rows:
        hay = " ".join(row).lower()
        if history_search.strip() and history_search.lower().strip() not in hay:
            continue
        if market_filter != "All" and row[1] != market_filter:
            continue
        if event_filter != "All" and row[2] != event_filter:
            continue
        if severity_filter != "All" and row[3] != severity_filter:
            continue
        if active_tab == "Actions" and row[2] != "UI_ACTION":
            continue
        if active_tab == "Validation" and "VALIDATION" not in row[2].upper() and "validation" not in " ".join(row).lower():
            continue
        if active_tab == "System Events" and row[6] not in {"SYSTEM", "system", "pipeline", "command"}:
            continue
        if active_tab == "Alerts" and row[2] not in {"ALERT", "ANOMALY", "GATE"}:
            continue
        filtered_rows.append(row)
    left, right = st.columns([0.72, 0.28], gap="small")
    with left:
        _panel("Event Chain Replay", _event_chain_html())
        _panel(
            "Audit Event Log",
            _html_table(
                ["Time (UTC)", "Market", "Event Type", "Severity", "Signal / Event", "Value", "Source", "Notes"],
                filtered_rows[:10],
            )
            + f'<div class="r5-table-footer">Showing 1 to 10 of {escape(str(len(filtered_rows)))} filtered records <span>History replay ready</span></div>',
        )
        if ui_audit_rows:
            _panel(
                "Recent UI Action Audit",
                _html_table(
                    ["Time (UTC)", "Market", "Event Type", "Severity", "Signal / Event", "Value", "Source", "Notes"],
                    ui_audit_rows[:8],
                )
                + '<div class="r5-table-footer">UI actions now flow into History for operator replay</div>',
            )
    with right:
        _panel(
            "Audit Detail Drawer",
            "".join(
                [
                    _kv("Selected Event", "market_anomaly_event.v2"),
                    _kv("Upstream Refs", "comparison_143101, obs_142000"),
                    _kv("Policy Refs", "anomaly_policy.v2"),
                    _kv("Raw Evidence Ref", "ecmwf_1420.json"),
                    _kv("Operator Action", "review_pending"),
                ]
            ),
        )
        if st.button("Open Replay", key="history_open_replay_side", use_container_width=True):
            _write_ui_action_audit("open_replay", page="history", detail={"selected_event": "market_anomaly_event.v2"})
            st.toast("Replay detail opened.", icon="🎞️")


def render_r5_evidence_page(df: pd.DataFrame | None) -> None:
    _render_r5_theme()
    context = st.session_state.get("dashboard_page_context")
    context = context if isinstance(context, dict) else {}
    context_market = _first_text(_dict(context.get("entry_context")).get("city"), context.get("selected_market_id"), "")
    st.html(_page_header("Evidence / Raw", "证据 & 原始数据", "LIVE"))
    st.html('<div class="r5-warning-banner"><strong>AUDIT / RAW DATA VIEW</strong><span>Not for primary operational decision. Use canonical workstation fields for operator judgment.</span></div>')
    active_tab = _render_live_tabs(["Observations", "Model Raw", "Validation Files", "Logs", "Exports"], key="evidence_active_tab")
    evidence_filters = st.columns([1.2, 1, 1, 1, 1, 1], gap="small")
    market_options = ["New York, US", "Houston, US", "London, UK"]
    if context_market and context_market not in market_options:
        market_options = [context_market, *market_options]
    market_choice = evidence_filters[0].selectbox("Market", market_options, key="evidence_market_filter")
    source_choice = evidence_filters[1].selectbox("Source", ["All Sources", "ECMWF API", "NWS API", "NOAA GFS", "BOM API"], key="evidence_source_filter")
    type_options = ["All", "Rainfall", "Humidity", "Pressure", "Wind Gust"]
    if active_tab == "Model Raw":
        type_options = ["All", "Rainfall", "Wind Gust", "Pressure"]
    if active_tab == "Validation Files":
        type_options = ["All", "Validation", "Coverage", "Policy"]
    if active_tab == "Logs":
        type_options = ["All", "Scanner", "Router", "Gateway"]
    type_choice = evidence_filters[2].selectbox("Data Type", type_options, key=f"evidence_type_filter_{sanitize_text(active_tab)}")
    time_choice = evidence_filters[3].selectbox("Window", ["Last 24 Hours", "Last 12 Hours", "Last 6 Hours"], key="evidence_window_filter")
    preview_clicked = evidence_filters[4].button("Preview", key="evidence_preview", use_container_width=True)
    export_clicked = evidence_filters[5].download_button(
        "Download",
        data=json.dumps({"market": market_choice, "source": source_choice, "type": type_choice, "window": time_choice}, ensure_ascii=False, indent=2),
        file_name="evidence_filter_export.json",
        mime="application/json",
        use_container_width=True,
        key="evidence_download",
    )
    if preview_clicked:
        _write_ui_action_audit("preview_evidence", page="evidence_raw", detail={"market": market_choice, "source": source_choice})
        st.toast("Preview refreshed for evidence filters.", icon="👁️")
    left, right = st.columns([0.74, 0.26], gap="small")
    with left:
        evidence_rows = [
            ["2026-04-24 14:20:00", "ECMWF API", "Rainfall", "52.4 mm", "52.4 mm", "52.4 mm", "A", "rainfall_mm.v1", "ecmwf_1420.json"],
            ["2026-04-24 14:15:00", "NWS API", "Rainfall", "48.7 mm", "48.7 mm", "48.7 mm", "A", "rainfall_mm.v1", "nws_1415.json"],
            ["2026-04-24 14:10:00", "NOAA GFS", "Rainfall", "45.1 mm", "45.1 mm", "45.1 mm", "B", "rainfall_mm.v1", "gfs_1410.grib"],
            ["2026-04-24 14:05:00", "Satellite Feed", "Cloud Top Temp", "-62.1 C", "-62.1 C", "-62 C", "A", "temp_c.v2", "sat_1405.png"],
            ["2026-04-24 14:00:00", "ECMWF API", "Rainfall", "52.4 mm", "52.4 mm", "52.4 mm", "A", "rainfall_mm.v1", "ecmwf_1400.json"],
            ["2026-04-24 13:55:00", "NWS API", "Humidity", "87 %", "0.87", "87%", "B", "humidity_pct.v1", "nws_1355.json"],
            ["2026-04-24 13:50:00", "BOM API", "Pressure", "1002 hPa", "1002 hPa", "1002 hPa", "A", "pressure_hpa.v1", "bom_1350.json"],
            ["2026-04-24 13:45:00", "ECMWF API", "Rainfall", "41.3 mm", "41.3 mm", "41.3 mm", "A", "rainfall_mm.v1", "ecmwf_1345.json"],
            ["2026-04-24 13:40:00", "NOAA GFS", "Rainfall", "38.6 mm", "38.6 mm", "38.6 mm", "B", "rainfall_mm.v1", "gfs_1340.grib"],
            ["2026-04-24 13:35:00", "NWS API", "Wind Gust", "24.3 m/s", "24.3 m/s", "24.3 m/s", "A", "wind_ms.v1", "nws_1335.json"],
        ]
        filtered_evidence_rows = [
            row for row in evidence_rows
            if (source_choice == "All Sources" or row[1] == source_choice)
            and (type_choice == "All" or row[2] == type_choice)
        ]
        _panel(
            "Raw / Canonical / Display Evidence",
            _html_table(
                ["Time (UTC)", "Source", "Type", "Raw Value", "Canonical", "Display", "Quality", "Policy", "File / ID"],
                filtered_evidence_rows,
            )
            + f'<div class="r5-table-footer">Showing 1 to 10 of {escape(str(len(filtered_evidence_rows)))} filtered records <span>Preview mode ready</span></div>',
        )
    with right:
        _panel(
            "Observation Detail",
            "".join(
                [
                    _kv("Source", "ECMWF API"),
                    _kv("Type", "Rainfall"),
                    _kv("Time (UTC)", "2026-04-24 14:20:00"),
                    _kv("Observed Value", "52.4 mm"),
                    _kv("Unit", "mm"),
                    _kv("Location", "New York, US"),
                    _kv("Quality", "A (High)"),
                    _kv("Latency", "3 min"),
                    _kv("File / ID", "ecmwf_1420.json"),
                    '<div class="r5-lineage-title">Data Lineage</div>',
                    _lineage_html(),
                    '<div class="r5-radar r5-radar--large"></div>',
                ]
            ),
        )
        evidence_actions = st.columns(2, gap="small")
        if evidence_actions[0].button("Open Workstation", key="evidence_open_workstation", use_container_width=True):
            _navigate_page(
                source_page="evidence_raw",
                target_page="workstation",
                selected_market_id=context.get("selected_market_id") or sanitize_text(market_choice),
                entry_reason="open_workstation",
                entry_context={"market": market_choice, "source": source_choice, "data_type": type_choice},
            )
            st.toast("Opening Workstation from Evidence / Raw.", icon="🔎")
            st.rerun()
        if evidence_actions[1].button("Open History", key="evidence_open_history", use_container_width=True):
            _navigate_page(
                source_page="evidence_raw",
                target_page="history",
                selected_market_id=context.get("selected_market_id") or sanitize_text(market_choice),
                entry_reason="open_history",
                entry_context={"market": market_choice, "source": source_choice, "data_type": type_choice},
            )
            st.toast("Opening History from Evidence / Raw.", icon="🕘")
            st.rerun()


def _render_r5_theme() -> None:
    st.html(
        """
        <style>
        :root {
          --r5-bg:#061019; --r5-panel:#0b1824; --r5-panel-2:#0e2030; --r5-line:rgba(116,151,184,.22);
          --r5-line-strong:rgba(63,161,255,.38); --r5-text:#dce7ef; --r5-soft:#a7b6c3; --r5-dim:#74889a;
          --r5-blue:#2f9bff; --r5-green:#35d46f; --r5-red:#ff493f; --r5-amber:#ffad28; --r5-magenta:#db4df3;
        }
        .r5-page, .r5-topbar, .r5-tabs, .r5-kpi-strip, .r5-panel, .r5-action-bar, .r5-pipeline-flow, .r5-bottom-strip, .r5-market-stats, .r5-toolbar {
          font-family: "Aptos", "IBM Plex Sans", "SF Pro Display", sans-serif;
        }
        .r5-topbar {display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid var(--r5-line);padding:.15rem 0 .6rem;margin-bottom:.5rem;}
        .r5-title {font-size:1.34rem;font-weight:900;color:var(--r5-text);letter-spacing:0;}
        .r5-title span, .r5-subtitle {color:var(--r5-soft);font-size:.78rem;font-weight:650;}
        .r5-market-head {display:flex;align-items:center;gap:.6rem;margin-top:.5rem;color:var(--r5-text);font-size:1rem;}
        .r5-star {color:var(--r5-amber)} .r5-top-actions {display:flex;gap:.5rem}
        .r5-top-actions button, .r5-action-bar button, .r5-primary-btn {background:#0a356d;border:1px solid rgba(47,155,255,.45);color:#fff;border-radius:4px;padding:.42rem .72rem;font-weight:800;}
        .r5-pill {border-radius:3px;padding:.2rem .42rem;font-size:.72rem;font-weight:900;border:1px solid var(--r5-line);}
        .r5-pill--red {color:var(--r5-red);background:rgba(255,73,63,.12);border-color:rgba(255,73,63,.35)}
        .r5-kpi-strip {display:grid;grid-template-columns:repeat(7,1fr);border-bottom:1px solid var(--r5-line);margin-bottom:.45rem}
        .r5-metric {padding:.45rem .75rem;border-left:1px solid var(--r5-line)} .r5-metric:first-child{border-left:0}
        .r5-metric span {display:block;color:var(--r5-soft);font-size:.68rem}.r5-metric strong{display:block;font-size:1.05rem;color:var(--r5-text)}
        .r5-green{color:var(--r5-green)!important}.r5-red{color:var(--r5-red)!important}.r5-amber{color:var(--r5-amber)!important}
        .r5-tabs {display:flex;gap:.35rem;border:1px solid var(--r5-line);background:rgba(10,24,36,.75);border-radius:4px;margin:.45rem 0 .55rem;padding:.18rem}
        .r5-tabs span {padding:.42rem .78rem;border-radius:4px;color:var(--r5-soft);font-size:.74rem;font-weight:780}.r5-tabs .active{background:#0d4589;color:#fff}
        .r5-panel {border:1px solid var(--r5-line);background:linear-gradient(180deg,rgba(11,24,36,.96),rgba(6,16,25,.96));border-radius:5px;padding:.72rem;margin-bottom:.45rem;min-height:0}
        .r5-panel-title {color:var(--r5-text);font-size:.78rem;font-weight:900;margin-bottom:.58rem;text-transform:uppercase}
        .r5-kv {display:flex;justify-content:space-between;gap:1rem;padding:.33rem 0;border-bottom:1px solid rgba(116,151,184,.13);color:var(--r5-soft);font-size:.72rem}
        .r5-kv strong {color:var(--r5-text);text-align:right}.r5-risk-line {display:flex;justify-content:space-between;color:var(--r5-soft);font-size:.72rem;margin-bottom:.5rem}.r5-risk-line span:first-child{color:var(--r5-red);font-weight:900}
        .r5-chart-shell {height:20px;color:var(--r5-soft);font-size:.72rem}.r5-big-value{font-size:1.9rem;color:#fff;font-weight:900}.r5-big-value span{font-size:.9rem;color:var(--r5-soft)}
        .r5-muted {color:var(--r5-soft);font-size:.72rem}.r5-radar{height:110px;border:1px solid var(--r5-line);border-radius:4px;margin-top:.55rem;background:radial-gradient(circle at 68% 48%, rgba(255,173,40,.8), transparent 8%),radial-gradient(circle at 52% 48%, rgba(53,212,111,.75), transparent 14%),linear-gradient(135deg,#173650,#07131e)}
        .r5-radar--large{height:210px}.r5-action-status{padding:.26rem 0;color:var(--r5-soft);font-size:.75rem}.r5-action-status:before{content:"•";color:var(--r5-blue);margin-right:.35rem}.r5-action-status.active{color:var(--r5-text);font-weight:850}.r5-action-status.active:before{content:"NEXT";font-size:.58rem;border:1px solid rgba(255,176,32,.34);border-radius:.24rem;padding:.06rem .22rem;color:var(--r5-amber)}
        .r5-table{width:100%;border-collapse:collapse;font-size:.72rem;color:var(--r5-soft)}.r5-table th{color:#8aa2b8;text-align:left;font-size:.64rem;font-weight:850;border-bottom:1px solid var(--r5-line);padding:.42rem}.r5-table td{border-bottom:1px solid rgba(116,151,184,.12);padding:.42rem}.r5-table td:nth-child(3),.r5-table td:nth-child(4),.r5-table td:nth-child(9){color:var(--r5-green);font-weight:850}
        .r5-action-bar,.r5-bottom-strip,.r5-toolbar{display:flex;gap:.55rem;align-items:center;border:1px solid var(--r5-line);border-radius:5px;background:rgba(11,24,36,.92);padding:.55rem;margin-top:.25rem}
        .r5-toolbar span{border:1px solid var(--r5-line);padding:.38rem .55rem;border-radius:4px;color:var(--r5-soft);font-size:.72rem}
        .r5-pipeline-flow{display:grid;grid-template-columns:repeat(6,1fr);gap:.7rem;margin:.5rem 0}.r5-stage{border:1px solid var(--r5-line);border-radius:5px;padding:.8rem;text-align:center;background:rgba(11,24,36,.92)}.r5-stage-title{font-size:.68rem;color:#fff;font-weight:900;text-align:left}.r5-stage-title span{float:right;color:var(--r5-green);background:rgba(53,212,111,.14);padding:.08rem .22rem}.r5-stage-icon{font-size:2rem;color:var(--r5-blue);margin:.6rem}.r5-stage-value{font-size:1.35rem;color:#fff;font-weight:900}.r5-stage-ok{color:var(--r5-green);font-size:1.1rem;margin-top:.35rem}
        .r5-metric-grid,.r5-market-stats{display:grid;grid-template-columns:repeat(6,1fr);gap:.5rem}.r5-metric-card,.r5-stat-tile{border:1px solid var(--r5-line);border-radius:5px;padding:.72rem;background:rgba(11,24,36,.76)}.r5-metric-card span,.r5-stat-tile span{color:var(--r5-soft);font-size:.68rem}.r5-metric-card strong,.r5-stat-tile strong{display:block;color:#fff;font-size:1.35rem}.r5-metric-card em,.r5-stat-tile em{color:var(--r5-green);font-style:normal;font-size:.75rem}
        .r5-health-score{display:grid;place-items:center;height:160px;color:var(--r5-green);font-size:2.2rem;font-weight:950}.r5-health-score span{display:block;font-size:.72rem;color:var(--r5-soft)}
        .r5-table-footer{display:flex;justify-content:space-between;color:var(--r5-soft);font-size:.72rem;padding:.65rem .25rem .2rem}.r5-freshness{display:grid;grid-template-columns:90px repeat(8,1fr);gap:3px;font-size:.64rem;color:var(--r5-soft)}.r5-cell{height:20px;border-radius:2px}.r5-cell.g{background:#37c35f}.r5-cell.a{background:#ffad28}.r5-cell.r{background:#b7332f}
        .r5-group-list{display:grid;gap:.45rem}.r5-group-card{border:1px solid var(--r5-line);border-left:3px solid var(--r5-blue);border-radius:5px;background:rgba(6,16,25,.58);padding:.55rem}.r5-group-card--focus{border-left-color:var(--r5-red)}.r5-group-card--watch{border-left-color:var(--r5-amber)}.r5-group-card--auto{border-left-color:var(--r5-green)}.r5-group-card--hidden{border-left-color:var(--r5-dim);opacity:.76}.r5-group-card strong{display:block;color:#fff;font-size:.8rem}.r5-group-card span{color:var(--r5-soft);font-size:.66rem}.r5-group-card em{float:right;color:var(--r5-blue);font-style:normal;font-size:.66rem;font-weight:900}
        .r5-control-stack{display:grid;gap:.42rem;margin-top:.65rem}.r5-control-stack button{background:#0a356d;border:1px solid rgba(47,155,255,.45);color:#fff;border-radius:4px;padding:.42rem .55rem;text-align:left;font-weight:800}
        .r5-presetbar{display:flex;gap:.55rem;align-items:center;border:1px solid var(--r5-line);border-radius:5px;background:rgba(11,24,36,.72);padding:.5rem;margin:.25rem 0 .55rem}.r5-presetbar span{color:var(--r5-soft);font-size:.72rem;border-right:1px solid var(--r5-line);padding-right:.65rem}.r5-presetbar span:first-child{color:#fff;font-weight:900}.r5-presetbar span:last-child{border-right:0}
        .r5-chain{display:grid;grid-template-columns:repeat(6,1fr);gap:.42rem}.r5-chain-step{border:1px solid var(--r5-line);border-radius:5px;padding:.58rem;background:rgba(8,18,28,.72);position:relative}.r5-chain-step:not(:last-child):after{content:"→";position:absolute;right:-.34rem;top:38%;color:var(--r5-blue);font-weight:900}.r5-chain-step span{display:block;color:var(--r5-soft);font-size:.64rem}.r5-chain-step strong{display:block;color:#fff;font-size:.78rem}.r5-chain-step.red strong{color:var(--r5-red)}.r5-chain-step.amber strong{color:var(--r5-amber)}.r5-chain-step.green strong{color:var(--r5-green)}
        .r5-warning-banner{display:flex;gap:.9rem;align-items:center;border:1px solid rgba(255,173,40,.45);border-left:4px solid var(--r5-amber);border-radius:5px;background:rgba(255,173,40,.08);padding:.58rem .7rem;margin:.25rem 0 .55rem}.r5-warning-banner strong{color:var(--r5-amber);font-size:.76rem}.r5-warning-banner span{color:#d5c8a8;font-size:.72rem}
        .r5-lineage-title{color:var(--r5-blue);font-size:.7rem;font-weight:900;margin:.65rem 0 .35rem;text-transform:uppercase}.r5-lineage{display:grid;gap:.28rem}.r5-lineage-step{border:1px solid var(--r5-line);border-radius:4px;padding:.35rem .45rem;color:var(--r5-soft);font-size:.68rem;background:rgba(8,18,28,.68)}.r5-lineage-step strong{color:#fff}.r5-lineage-step:before{content:"↳";color:var(--r5-blue);margin-right:.32rem}
        .r5-command-context{display:grid;grid-template-columns:2.5fr repeat(5,1fr);border:1px solid var(--r5-line);border-radius:5px;background:linear-gradient(90deg,rgba(11,24,36,.96),rgba(6,16,25,.96));margin:.35rem 0 .55rem}.r5-command-context>div{padding:.75rem .9rem;border-left:1px solid var(--r5-line)}.r5-command-context>div:first-child{border-left:0}.r5-command-context span{display:block;color:var(--r5-soft);font-size:.66rem;font-weight:900}.r5-command-context strong{display:block;color:#fff;font-size:.86rem;margin:.25rem 0}.r5-command-context .wide strong{font-size:1.2rem}.r5-command-context em{display:block;color:var(--r5-soft);font-style:normal;font-size:.68rem}
        .r5-gate-stack{display:grid;gap:.42rem}.r5-gate-item{display:grid;grid-template-columns:28px 1fr auto;gap:.55rem;align-items:start;border:1px solid var(--r5-line);border-radius:5px;padding:.58rem;background:rgba(8,18,28,.72)}.r5-gate-dot{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;font-weight:950;border:2px solid currentColor}.r5-gate-dot.green{color:var(--r5-green)}.r5-gate-dot.amber{color:var(--r5-amber)}.r5-gate-dot.red{color:var(--r5-red)}.r5-gate-copy strong{display:block;color:#fff;font-size:.78rem}.r5-gate-copy span{display:block;color:var(--r5-soft);font-size:.68rem}.r5-gate-detail{grid-column:2 / 4;border-top:1px solid rgba(116,151,184,.13);margin-top:.35rem;padding-top:.4rem;color:#d8e4ef;font-size:.68rem}.r5-gate-detail span{color:var(--r5-blue)}.r5-gate-badge{font-size:.66rem;font-weight:950;border-radius:4px;padding:.18rem .38rem;background:rgba(116,151,184,.12)}.r5-gate-badge.green{color:var(--r5-green);background:rgba(53,212,111,.13)}.r5-gate-badge.amber{color:var(--r5-amber);background:rgba(255,173,40,.13)}.r5-gate-badge.red{color:var(--r5-red);background:rgba(255,73,63,.13)}
        .r5-command-reco{display:grid;grid-template-columns:58px 1fr;gap:.8rem;align-items:center;border:1px solid var(--r5-line);border-radius:5px;background:rgba(8,18,28,.74);padding:.8rem}.r5-warning-icon{width:48px;height:48px;border-radius:10px;background:rgba(255,173,40,.16);color:var(--r5-amber);display:grid;place-items:center;font-size:2rem;font-weight:950}.r5-command-reco span{color:#fff;font-size:.68rem;font-weight:900}.r5-command-reco strong{display:block;color:var(--r5-amber);font-size:1.16rem;margin:.15rem 0}.r5-command-reco p{margin:0;color:var(--r5-soft);font-size:.76rem}.r5-command-reco b{color:var(--r5-red)}
        .r5-command-metrics{display:grid;grid-template-columns:repeat(5,1fr);border-bottom:1px solid var(--r5-line);margin:.55rem 0 .65rem}.r5-command-metrics div{padding:.35rem .5rem;border-left:1px solid var(--r5-line)}.r5-command-metrics div:first-child{border-left:0}.r5-command-metrics span{display:block;color:var(--r5-soft);font-size:.64rem}.r5-command-metrics strong{display:block;color:#fff;font-size:1rem}.r5-command-section-label{color:#fff;font-weight:950;font-size:.72rem;margin:.25rem 0 .45rem}
        .r5-action-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.48rem}.r5-action-card{border:1px solid var(--r5-line);border-radius:5px;background:rgba(13,32,48,.74);padding:.58rem;display:grid;grid-template-columns:26px 1fr auto;gap:.55rem;align-items:center}.r5-action-card.disabled{opacity:.48}.r5-action-card .icon{width:24px;height:24px;border-radius:6px;border:1px solid rgba(47,155,255,.5);color:var(--r5-blue);display:grid;place-items:center}.r5-action-card strong{display:block;color:#fff;font-size:.76rem}.r5-action-card span{display:block;color:var(--r5-soft);font-size:.66rem}.r5-action-card em{font-style:normal;color:#fff}
        .r5-note-row{display:grid;grid-template-columns:1fr 88px;gap:.55rem;margin-top:.65rem}.r5-note-row span{border:1px solid var(--r5-line);border-radius:5px;padding:.55rem;color:var(--r5-soft);font-size:.72rem}.r5-note-row button,.r5-wide-btn{width:100%}.r5-gateway-row{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(116,151,184,.16);padding:.55rem .15rem;color:var(--r5-soft);font-size:.73rem}.r5-gateway-row strong{color:#fff}.r5-blue{color:var(--r5-blue)!important}.r5-context-summary{display:grid;grid-template-columns:1fr 230px;gap:.75rem}
        .r5-page, .r5-command-shell {
          width: 100%;
          max-width: 100%;
          min-height: calc(100dvh - 0.45rem);
          font-size: 15px;
        }
        .r5-page .r5-panel,
        .r5-command-shell .r5-panel {
          min-height: 0;
        }
        @media (min-height: 2100px) {
          .r5-page, .r5-command-shell {
            font-size: 15.5px;
          }
          .r5-panel {padding: .78rem;margin-bottom:.5rem}
          .r5-topbar {padding:.18rem 0 .72rem;margin-bottom:.58rem}
          .r5-kpi-strip {margin-bottom:.52rem}
        }
        @media (min-height: 1400px) and (max-height: 2099px) {
          .r5-page, .r5-command-shell {
            font-size: 15px;
          }
          .r5-panel {padding:.7rem;margin-bottom:.46rem}
        }
        @media (max-height: 1399px) {
          .r5-page, .r5-command-shell {
            font-size: 14px;
          }
          .r5-topbar {padding:.1rem 0 .45rem;margin-bottom:.38rem}
          .r5-title {font-size:1.18rem}
          .r5-panel {padding:.58rem;margin-bottom:.34rem}
          .r5-kpi-strip {margin-bottom:.28rem}
          .r5-tabs, .r5-action-bar, .r5-bottom-strip, .r5-toolbar {padding:.42rem;margin-top:.18rem}
        }
        </style>
        """
    )


def _panel(title: str, body: str) -> None:
    st.html(f"<div class='r5-panel'>{f'<div class=\"r5-panel-title\">{escape(title)}</div>' if title else ''}{body}</div>")


def _render_live_tabs(labels: list[str], *, key: str) -> str:
    return st.selectbox(
        "Page section",
        labels,
        key=key,
    )


def _render_workstation_secondary_tab(tab: str, *, current_market_id: str, city: str, question: str) -> None:
    panels = {
        "Observations": [["Latest Observation", "42.6 mm"], ["Source", "ECMWF API"], ["Freshness", "LIVE"], ["Quality", "B"]],
        "Models": [["Best Model", "ECMWF"], ["Alt Model", "GFS"], ["Model Edge", "+18%"], ["Skill", "0.78"]],
        "Signals": [["Alert", "RED"], ["Anomaly", "0.76"], ["Gate", "BLOCKED"], ["Next", "Review evidence"]],
        "Validation": [["Coverage", "72.3%"], ["Status", "DEGRADED"], ["Promotion", "not ready"], ["Reason", "coverage below 80%"]],
        "Evidence": [["Raw", "available"], ["Canonical", "available"], ["Policy", "rainfall_mm.v1"], ["Lineage", "linked"]],
        "Strategy": [["Mode", "manual advisory"], ["Dry-run", "guarded"], ["Live", "disabled"], ["Boundary", "gate first"]],
        "Notes": [["Market", city], ["Question", question], ["Context", current_market_id], ["Audit", "enabled"]],
    }
    rows = panels.get(tab, panels["Observations"])
    _panel(f"{tab} Detail", _html_table(["Field", "Value"], rows))
    action_cols = st.columns([1, 1, 4], gap="small")
    if action_cols[0].button("Review Evidence", key=f"wk_tab_evidence_{sanitize_text(tab)}_{sanitize_text(current_market_id)}", use_container_width=True):
        _navigate_page(source_page="workstation", target_page="evidence_raw", selected_market_id=current_market_id, entry_reason="review_evidence", entry_context={"tab": tab, "city": city, "question": question})
        st.rerun()
    if action_cols[1].button("Send to Command", key=f"wk_tab_command_{sanitize_text(tab)}_{sanitize_text(current_market_id)}", use_container_width=True):
        _navigate_page(source_page="workstation", target_page="command", selected_market_id=current_market_id, entry_reason="send_to_command", entry_context={"tab": tab, "city": city, "question": question})
        st.rerun()
    action_cols[2].caption(f"Active Workstation tab: {tab}. This tab changes visible content and preserves context.")


def _render_pipeline_secondary_tab(tab: str) -> None:
    if tab == "Scanner Health":
        rows = [["Discovery", "LIVE", "18s ago"], ["Evidence", "LIVE", "22s ago"], ["Family Scanner", "LIVE", "25s ago"], ["Alert Router", "LIVE", "10s ago"]]
    elif tab == "Data Sources":
        rows = [["ECMWF API", "LIVE", "1.36s"], ["NWS API", "LIVE", "1.98s"], ["BOM API", "WARN", "2.56s"], ["NOAA GFS", "LIVE", "1.82s"]]
    elif tab == "Jobs":
        rows = [["Parallel Jobs", "8", "running"], ["Failed Jobs", "0", "healthy"], ["Queued Jobs", "3", "pending"], ["Next Run", "12s", "scheduled"]]
    else:
        rows = [["14:32:11", "INFO", "Data ingestion restarted"], ["14:18:09", "WARN", "ECMWF latency high"], ["13:55:32", "INFO", "Backup complete"]]
    _panel(f"Pipeline / {tab}", _html_table(["Item", "Status", "Detail"], rows))


def _page_header(title: str, subtitle: str, live: str, right: str = "") -> str:
    right_html = f"<div class='r5-top-actions'><span>{escape(right)}</span></div>" if right else ""
    return f"""
    <div class="r5-topbar">
      <div><div class="r5-title">{escape(title)} <span>({escape(subtitle)})</span></div></div>
      <div style="display:flex;align-items:center;gap:.75rem"><span class="r5-pill r5-green">{escape(live)}</span>{right_html}</div>
    </div>
    """


def _metric(label: str, value: Any, tone: str) -> str:
    cls = f"r5-{tone}" if tone in {"green", "red", "amber"} else ""
    return f"<div class='r5-metric'><span>{escape(label)}</span><strong class='{cls}'>{escape(str(value))}</strong></div>"


def _kv(label: str, value: Any, tone: str = "neutral") -> str:
    cls = f"r5-{tone}" if tone in {"green", "red", "amber"} else ""
    return f"<div class='r5-kv'><span>{escape(label)}</span><strong class='{cls}'>{escape(_first_text(value, '-'))}</strong></div>"


def _html_table(headers: list[str], rows: list[list[Any]]) -> str:
    head = "".join(f"<th>{escape(str(item))}</th>" for item in headers)
    body = "".join("<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table class='r5-table'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _chart_shell(label: str) -> str:
    return f"<div class='r5-chart-shell'>{escape(label)}</div>"


def _metric_card(label: str, value: str, delta: str) -> str:
    return f"<div class='r5-metric-card'><span>{escape(label)}</span><strong>{escape(value)}</strong><em>{escape(delta)}</em><div class='r5-muted'>vs prev 1h</div></div>"


def _stat_tile(label: str, value: str, delta: str) -> str:
    return f"<div class='r5-stat-tile'><span>{escape(label)}</span><strong>{escape(value)}</strong><em>{escape(delta)}</em></div>"


def _donut_legend(items: list[tuple[str, str]]) -> str:
    return "<div class='r5-health-score'>◕<span>" + "<br>".join(f"{escape(k)} {escape(v)}" for k, v in items) + "</span></div>"


def _freshness_heatmap() -> str:
    rows = ["ECMWF API", "NWS API", "BOM API", "NOAA GFS", "Satellite Feed"]
    cells = []
    for index, row in enumerate(rows):
        cells.append(f"<div>{escape(row)}</div>")
        for col in range(8):
            tone = "g" if col > index else "a" if col + index < 7 else "r"
            cells.append(f"<div class='r5-cell {tone}'></div>")
    return "<div class='r5-freshness'>" + "".join(cells) + "</div>"


def _market_group_cards(rows: list[dict[str, str]], group: str, *, limit: int) -> str:
    filtered = [row for row in rows if row["group"] == group][:limit]
    if not filtered:
        return "<div class='r5-muted'>No markets in this group.</div>"
    tone = group.lower()
    cards = []
    for row in filtered:
        cards.append(
            f"""
            <div class="r5-group-card r5-group-card--{escape(tone)}">
              <em>{escape(row['scan_priority'])}</em>
              <strong>{escape(row['market'])}</strong>
              <span>{escape(row['signal'])}</span><br>
              <span>Resolver {escape(row['resolver'])} · Source {escape(row['source'])}</span>
            </div>
            """
        )
    return "<div class='r5-group-list'>" + "".join(cards) + "</div>"


def _event_chain_html() -> str:
    steps = [
        ("Signal", "ANOMALY 0.92", "amber"),
        ("Alert", "RED", "red"),
        ("Ack", "Pending", "amber"),
        ("Review", "Evidence", "amber"),
        ("Dry-run", "Ready", "green"),
        ("Gate Result", "BLOCKED", "red"),
    ]
    return "<div class='r5-chain'>" + "".join(f"<div class='r5-chain-step {tone}'><span>{escape(label)}</span><strong>{escape(value)}</strong></div>" for label, value, tone in steps) + "</div>"


def _lineage_html() -> str:
    steps = [
        ("Raw Source", "ECMWF API payload"),
        ("Normalized Snapshot", "ForecastSnapshot.v2"),
        ("Comparison Point", "comparison_143101"),
        ("Alert / Anomaly", "market_anomaly_event.v2"),
        ("Gate Context", "gate_stack_api.v1"),
    ]
    return "<div class='r5-lineage'>" + "".join(f"<div class='r5-lineage-step'><strong>{escape(label)}</strong> · {escape(value)}</div>" for label, value in steps) + "</div>"


def _gate_stack_html(items: list[tuple[str, str, str, str, str]]) -> str:
    chunks = []
    for label, status, summary, tone, detail in items:
        symbol = "✓" if tone == "green" else "!" if tone == "amber" else "×"
        detail_html = f"<div class='r5-gate-detail'>{detail}</div>" if detail else ""
        chunks.append(
            f"""
            <div class="r5-gate-item">
              <div class="r5-gate-dot {escape(tone)}">{escape(symbol)}</div>
              <div class="r5-gate-copy"><strong>{escape(label)}</strong><span>{escape(summary)}</span></div>
              <div class="r5-gate-badge {escape(tone)}">{escape(status)}</div>
              {detail_html}
            </div>
            """
        )
    return "<div class='r5-gate-stack'>" + "".join(chunks) + "</div>"


def _action_card(title: str, subtitle: str, icon: str, *, disabled: bool = False) -> str:
    cls = "r5-action-card disabled" if disabled else "r5-action-card"
    glyph = {"open": "□", "intent": "▣", "evidence": "◇", "play": "▷", "ack": "◎", "locked": "▣", "mute": "○"}.get(icon, "•")
    state_label = "LOCKED" if disabled else "READY"
    return (
        f"<div class='{cls}' title='Status card only. Use the buttons below to execute this action.'>"
        f"<div class='icon' aria-hidden='true'>{escape(glyph)}</div>"
        f"<div><strong>{escape(title)}</strong><span>{escape(subtitle)}</span></div>"
        f"<em>{state_label}</em>"
        "</div>"
    )


def _gateway_row(label: str, value: str, tone: str) -> str:
    cls = f"r5-{tone}" if tone in {"green", "red", "amber", "blue"} else ""
    return f"<div class='r5-gateway-row'><span>{escape(label)}</span><strong class='{cls}'>{escape(value)}</strong></div>"


def _render_forecast_chart() -> None:
    fig = go.Figure()
    days = [f"Apr {17+i}" for i in range(8)]
    series = {
        "Observed": [38, 58, 36, 82, 74, 92, 88, 96],
        "ECMWF": [42, 54, 44, 76, 91, 100, 82, 98],
        "GFS": [36, 48, 41, 62, 70, 84, 92, 90],
        "ICON": [40, 55, 38, 74, 92, 98, 84, 100],
        "NAM": [32, 50, 35, 70, 76, 72, 74, 83],
    }
    colors = ["#2f9bff", "#ff8b2b", "#55d052", "#ffad28", "#7c5cff"]
    for (name, vals), color in zip(series.items(), colors, strict=False):
        fig.add_trace(go.Scatter(x=days, y=vals, name=name, mode="lines+markers", line=dict(color=color, width=2)))
    fig.add_trace(go.Bar(x=days, y=[18, 26, 24, 32, 36, 28, 24, 22], name="Rain", marker_color="rgba(47,155,255,.45)"))
    _style_fig(fig, height=255)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _market_evidence_timeline_chart() -> go.Figure:
    days = [f"Apr {17+i}" for i in range(8)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=[50, 54, 49, 62, 70, 78, 74, 82], name="Market probability", mode="lines+markers", line=dict(color="#2f9bff", width=3)))
    fig.add_trace(go.Scatter(x=days, y=[38, 56, 42, 74, 92, 96, 83, 98], name="Forecast", mode="lines+markers", line=dict(color="#ffad28", width=2)))
    fig.add_trace(go.Scatter(x=days, y=[35, 60, 36, 82, 74, 92, 88, 96], name="Observation", mode="lines+markers", line=dict(color="#35d46f", width=2)))
    fig.add_trace(go.Scatter(x=days, y=[44, 44, 44, 44, 44, 44, 44, 44], name="Official threshold", mode="lines", line=dict(color="#d8e2ed", width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=["Apr 21", "Apr 24"], y=[96, 82], name="Alert markers", mode="markers+text", text=["ALERT", "GATE"], textposition="top center", marker=dict(color="#ff493f", size=13, symbol="diamond")))
    _style_fig(fig, height=310)
    fig.update_yaxes(title="Normalized evidence / probability")
    return fig


def _line_chart(names: list[str]) -> go.Figure:
    fig = go.Figure()
    days = [f"Apr {17+i}" for i in range(8)]
    colors = ["#2f9bff", "#ff7a24", "#aa72ff", "#35d46f"]
    for idx, name in enumerate(names):
        vals = [0.35 + idx * 0.08 + ((i + idx) % 4) * 0.045 for i in range(8)]
        fig.add_trace(go.Scatter(x=days, y=vals, mode="lines+markers", name=name, line=dict(color=colors[idx], width=2)))
    _style_fig(fig, height=245)
    return fig


def _bar_line_chart() -> go.Figure:
    fig = go.Figure()
    days = [f"Apr {17+i}" for i in range(8)]
    fig.add_trace(go.Bar(x=days, y=[18, 36, 22, 34, 92, 48, 62, 39], name="Observed", marker_color="rgba(47,155,255,.65)"))
    fig.add_trace(go.Scatter(x=days, y=[28, 42, 50, 84, 70, 52, 44, 58], name="Forecast P50", line=dict(color="#d8e2ed", width=2)))
    _style_fig(fig, height=245)
    return fig


def _stacked_bar_chart() -> go.Figure:
    fig = go.Figure()
    days = [f"Apr {17+i}" for i in range(8)]
    for name, color, vals in [
        ("Red", "#ff493f", [3, 5, 4, 6, 9, 8, 10, 12]),
        ("Amber", "#ffad28", [7, 8, 8, 9, 13, 12, 14, 16]),
        ("Info", "#2f9bff", [10, 11, 12, 10, 9, 12, 9, 8]),
    ]:
        fig.add_trace(go.Bar(x=days, y=vals, name=name, marker_color=color))
    fig.update_layout(barmode="stack")
    _style_fig(fig, height=245)
    return fig


def _hist_chart() -> go.Figure:
    fig = go.Figure(go.Bar(x=["0-20", "20-40", "40-60", "60-80", "80-100"], y=[5, 14, 28, 42, 39], marker_color="#2f9bff"))
    _style_fig(fig, height=245)
    return fig


def _validation_line_chart() -> go.Figure:
    fig = go.Figure(go.Scatter(x=[f"Apr {17+i}" for i in range(8)], y=[91, 92, 91, 93, 94, 94, 95, 95], mode="lines+markers", line=dict(color="#d64ff8", width=2)))
    _style_fig(fig, height=245)
    return fig


def _style_fig(fig: go.Figure, *, height: int) -> None:
    fig.update_layout(
        height=height,
        margin=dict(l=28, r=14, t=10, b=28),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#b9c6d3", size=11),
        legend=dict(orientation="h", y=1.15, x=0, font=dict(size=10)),
        xaxis=dict(gridcolor="rgba(116,151,184,.12)", zeroline=False),
        yaxis=dict(gridcolor="rgba(116,151,184,.12)", zeroline=False),
    )


def _market_rows(df: pd.DataFrame | None) -> list[dict[str, str]]:
    base = [
        ("New York, US", "Northeast", "82", "M", "0.74", "High", "Rainfall > 50mm", "0.92", "BLOCKED", "LIVE", "ALERT RED"),
        ("Houston, US", "South", "76", "M", "0.68", "High", "Temp > 30C", "0.76", "ALLOW", "LIVE", "ANOMALY"),
        ("London, UK", "Europe", "71", "M", "0.61", "Med", "Snowfall > 5cm", "0.65", "ALLOW", "LIVE", "NORMAL"),
        ("Berlin, DE", "Europe", "68", "H", "0.58", "Med", "Wind > 25km/h", "0.58", "ALLOW", "LIVE", "ANOMALY"),
        ("São Paulo, BR", "South America", "66", "H", "0.63", "High", "Rainfall > 80mm", "0.71", "BLOCKED", "LIVE", "ALERT AMB"),
        ("Mumbai, IN", "Asia", "58", "H", "0.55", "Med", "Temp > 35C", "0.61", "ALLOW", "STALE", "STALE"),
        ("Tokyo, JP", "Asia", "54", "H", "0.51", "High", "Wind > 30km/h", "0.49", "ALLOW", "LIVE", "NORMAL"),
        ("Sydney, AU", "Oceania", "50", "M", "0.48", "High", "Rainfall > 40mm", "0.47", "ALLOW", "LIVE", "NORMAL"),
        ("Singapore, SG", "Asia", "47", "H", "0.46", "Med", "Thunderstorm", "0.43", "ALLOW", "LIVE", "NORMAL"),
        ("Dubai, AE", "Middle East", "45", "H", "0.42", "Low", "Dust", "0.40", "ALLOW", "STALE", "STALE"),
    ]
    return [
        {
            "market_id": sanitize_text(item[0]),
            "market": item[0],
            "region": item[1],
            "opp": item[2],
            "diff": item[3],
            "conf": item[4],
            "liquidity": item[5],
            "signal": item[6],
            "anomaly": item[7],
            "gate": item[8],
            "fresh": item[9],
            "status": item[10],
        }
        for item in base
    ]


def _market_inventory_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    groups = ["FOCUS", "FOCUS", "WATCH", "WATCH", "AUTO", "AUTO", "AUTO", "AUTO", "HIDDEN", "HIDDEN"]
    watchlist = ["WATCHED", "WATCHED", "WATCHED", "WATCHED", "CANDIDATE", "CANDIDATE", "CANDIDATE", "CANDIDATE", "REMOVED", "HIDDEN"]
    focus = ["PINNED", "AUTO", "NO", "NO", "NO", "NO", "NO", "NO", "NO", "NO"]
    priorities = ["P1", "P1", "P1", "P2", "P2", "P2", "P3", "P3", "OFF", "OFF"]
    resolver = ["OK", "OK", "OK", "REVIEW", "OK", "OK", "OK", "OK", "DISABLED", "DISABLED"]
    source = ["LIVE", "LIVE", "LIVE", "DEGRADED", "LIVE", "STALE", "LIVE", "LIVE", "OFF", "OFF"]
    actions = ["View / Focus", "View / Focus", "View", "View", "Add Watch", "Add Watch", "Add Watch", "Add Watch", "Restore", "Restore"]
    inventory_map: dict[str, dict[str, str]] = {}
    focus_ids = {
        str(item)
        for item in st.session_state.get("r5_focus_market_ids", [])
        if str(item).strip()
    }
    removed_rows = [
        item for item in st.session_state.get("market_watchlist_removed", []) if isinstance(item, dict)
    ]
    removed_ids = {
        str(item.get("market_id") or item.get("market") or "").strip()
        for item in removed_rows
        if str(item.get("market_id") or item.get("market") or "").strip()
    }
    overrides = [
        item for item in st.session_state.get("market_watchlist_overrides", []) if isinstance(item, dict)
    ]

    def _merge_row(row: dict[str, str], *, idx: int | None = None) -> None:
        market_id = str(row.get("market_id") or sanitize_text(row.get("market") or "")).strip()
        if not market_id:
            return
        merged = {
            **row,
            "market_id": market_id,
            "group": row.get("group") or "AUTO",
            "watchlist": row.get("watchlist") or "CANDIDATE",
            "focus": row.get("focus") or "NO",
            "scan_priority": row.get("scan_priority") or "P2",
            "resolver": row.get("resolver") or "OK",
            "source": row.get("source") or "LIVE",
            "action_hint": row.get("action_hint") or "View",
        }
        if market_id in removed_ids:
            merged.update({"group": "HIDDEN", "watchlist": "REMOVED", "focus": "NO", "scan_priority": "OFF", "resolver": "DISABLED", "source": "OFF", "action_hint": "Restore"})
        elif market_id in focus_ids:
            merged.update({"group": "FOCUS", "watchlist": "WATCHED", "focus": "PINNED", "scan_priority": "P1", "action_hint": "View / Focus"})
        elif merged["watchlist"] in {"REMOVED", "HIDDEN"}:
            merged.update({"group": "HIDDEN", "scan_priority": "OFF", "resolver": "DISABLED", "source": "OFF", "action_hint": "Restore"})
        elif idx is not None and idx < len(groups):
            merged.update(
                {
                    "group": groups[idx],
                    "watchlist": watchlist[idx],
                    "focus": focus[idx],
                    "scan_priority": priorities[idx],
                    "resolver": resolver[idx],
                    "source": source[idx],
                    "action_hint": actions[idx],
                }
            )
        inventory_map[market_id] = merged

    for index, row in enumerate(rows):
        _merge_row(row, idx=index)

    for item in overrides:
        market_id = str(item.get("market_id") or item.get("market") or item.get("name") or "").strip()
        if not market_id:
            continue
        _merge_row(
            {
                "market_id": market_id,
                "market": str(item.get("market") or item.get("name") or item.get("market_name") or market_id),
                "region": str(item.get("region") or item.get("city") or item.get("market_family") or "Tracked"),
                "opp": str(item.get("opp") or item.get("opportunity_score") or item.get("score") or "-"),
                "diff": str(item.get("diff") or item.get("difficulty") or item.get("difficulty_label") or "-"),
                "conf": str(item.get("conf") or item.get("confidence") or item.get("resolver_confidence") or "0.50"),
                "liquidity": str(item.get("liquidity") or item.get("market_liquidity") or "High"),
                "signal": str(item.get("signal") or item.get("latest_signal") or item.get("question") or "Tracked Market"),
                "anomaly": str(item.get("anomaly") or item.get("latest_anomaly_score") or "0.0"),
                "gate": str(item.get("gate") or item.get("gate_status") or "ALLOW"),
                "fresh": str(item.get("fresh") or item.get("freshness_status") or "LIVE"),
                "status": str(item.get("status") or item.get("market_status") or "NORMAL"),
                "group": str(item.get("group") or "WATCH").upper(),
                "watchlist": str(item.get("watchlist") or "WATCHED").upper(),
                "focus": "PINNED" if market_id in focus_ids else str(item.get("focus") or "NO").upper(),
                "scan_priority": str(item.get("scan_priority") or "P2").upper(),
                "resolver": str(item.get("resolver") or "OK").upper(),
                "source": str(item.get("source") or "LIVE").upper(),
                "action_hint": str(item.get("action_hint") or "View"),
            }
        )

    for item in removed_rows:
        market_id = str(item.get("market_id") or item.get("market") or "").strip()
        if not market_id:
            continue
        _merge_row(
            {
                "market_id": market_id,
                "market": str(item.get("market") or market_id),
                "region": str(item.get("region") or "Hidden"),
                "opp": str(item.get("opp") or item.get("opportunity_score") or "-"),
                "diff": str(item.get("diff") or item.get("difficulty") or "OFF"),
                "conf": str(item.get("conf") or item.get("confidence") or "0.00"),
                "liquidity": str(item.get("liquidity") or "Low"),
                "signal": str(item.get("signal") or item.get("latest_signal") or "Hidden"),
                "anomaly": str(item.get("anomaly") or item.get("latest_anomaly_score") or "0.0"),
                "gate": str(item.get("gate") or "BLOCKED"),
                "fresh": str(item.get("fresh") or "OFF"),
                "status": "HIDDEN",
                "group": "HIDDEN",
                "watchlist": "REMOVED",
                "focus": "NO",
                "scan_priority": "OFF",
                "resolver": "DISABLED",
                "source": "OFF",
                "action_hint": "Restore",
            }
        )

    inventory = list(inventory_map.values())
    return sorted(inventory, key=lambda row: (row.get("group") != "FOCUS", row.get("group") != "WATCH", row.get("group") != "AUTO", row.get("market") or ""))


def _history_rows(history_df: pd.DataFrame | None) -> list[list[str]]:
    return [
        ["2026-04-24 14:41:01", "New York, US", "ANOMALY", "RED", "Rainfall > 50mm", "Anomaly Score: 0.92", "ECMWF API", "Validation coverage < 80%"],
        ["2026-04-24 14:30:12", "Houston, US", "ANOMALY", "AMBER", "Temp > 30C", "0.76", "NWS API", "-"],
        ["2026-04-24 13:38:55", "São Paulo, BR", "ALERT", "AMBER", "Rainfall > 80mm", "-", "ECMWF API", "Threshold exceeded"],
        ["2026-04-24 13:37:22", "London, UK", "NORMAL", "INFO", "Snowfall > 5cm", "0.45", "ECMWF API", "Back to normal"],
        ["2026-04-24 13:36:10", "New York, US", "GATE", "RED", "Gate Blocked", "-", "SYSTEM", "Validation coverage < 80%"],
        ["2026-04-24 13:33:01", "Berlin, DE", "ANOMALY", "AMBER", "Wind > 25km/h", "0.58", "ECMWF API", "-"],
        ["2026-04-24 13:33:49", "Miami, US", "ANOMALY", "INFO", "Rainfall > 30mm", "0.33", "NWS API", "-"],
        ["2026-04-24 13:32:18", "Tokyo, JP", "NORMAL", "INFO", "Wind > 30km/h", "0.28", "ECMWF API", "Below threshold"],
        ["2026-04-24 13:30:55", "Dubai, AE", "STALE", "INFO", "Dust", "-", "NOAA GFS", "Data stale > 1h"],
        ["2026-04-24 13:28:40", "Sydney, AU", "NORMAL", "INFO", "Rainfall > 40mm", "0.21", "BOM API", "-"],
    ]


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def sanitize_text(value: str) -> str:
    token = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value or "").strip())
    return token.strip("_") or "item"


def _write_ui_action_audit(action: str, *, market_id: str | None = None, page: str, detail: dict | None = None) -> None:
    path = OUTPUT_DIR / "ui_action_audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": "ui_action_event.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "page": page,
        "market_id": market_id or "",
        "detail": detail or {},
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _navigate_page(
    *,
    source_page: str,
    target_page: str,
    selected_market_id: str | None = None,
    selected_signal_id: str | None = None,
    selected_row_id: str | None = None,
    entry_reason: str = "navigate",
    entry_context: dict | None = None,
    upstream_refs: dict | None = None,
) -> dict:
    payload = {
        "schema_version": "page_context.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_page": source_page,
        "target_page": target_page,
        "selected_market_id": str(selected_market_id or "") or None,
        "selected_signal_id": str(selected_signal_id or "") or None,
        "selected_row_id": str(selected_row_id or "") or None,
        "entry_reason": entry_reason,
        "entry_context": entry_context if isinstance(entry_context, dict) else {},
        "upstream_refs": upstream_refs if isinstance(upstream_refs, dict) else {},
    }
    st.session_state["dashboard_page_context"] = payload
    st.session_state["dashboard_active_view"] = target_page
    try:
        PAGE_CONTEXT_JSON.parent.mkdir(parents=True, exist_ok=True)
        PAGE_CONTEXT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    _write_ui_action_audit(
        entry_reason,
        market_id=selected_market_id,
        page=source_page,
        detail={"target_page": target_page, **payload["entry_context"]},
    )
    return payload


def _load_ui_action_audit_rows(*, limit: int = 50) -> list[list[str]]:
    path = OUTPUT_DIR / "ui_action_audit.jsonl"
    if not path.exists():
        return []
    rows: list[list[str]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()[-limit:]
    except Exception:
        return []

    for raw in reversed(lines):
        try:
            item = json.loads(raw)
        except Exception:
            continue
        created_at = str(item.get("created_at") or "-")
        time_token = created_at.replace("T", " ").replace("Z", " UTC")
        detail = item.get("detail") if isinstance(item.get("detail"), dict) else {}
        market_label = str(item.get("market_id") or detail.get("market") or "-")
        page = str(item.get("page") or "ui")
        action = str(item.get("action") or "ui_action")
        detail_text = ", ".join(f"{key}={value}" for key, value in detail.items()) if detail else "-"
        rows.append(
            [
                time_token,
                market_label,
                "UI_ACTION",
                "INFO",
                action.replace("_", " ").title(),
                detail_text,
                page,
                "dashboard runtime action",
            ]
        )
    return rows


def _first_text(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() != "nan":
            return text
    return "-"


def _format_page_context_source(page_context: dict) -> str:
    source_page = _first_text(page_context.get("source_page"), "-")
    entry_reason = _first_text(page_context.get("entry_reason"), "-")
    if source_page == "-" and entry_reason == "-":
        return "Direct"
    return f"{source_page.replace('_', ' ').title()} > {entry_reason.replace('_', ' ').title()}"


def _number(value: Any, default: float) -> float:
    try:
        number = float(value)
        if isnan(number):
            return default
        return number
    except Exception:
        return default


def _score(value: Any, default: int) -> int:
    number = _number(value, default)
    return int(round(number * 100 if number <= 1 else number))


def _pct(value: Any, default: str) -> str:
    if value is None:
        return default
    number = _number(value, -1)
    if number < 0:
        return default
    return f"{number * 100:.1f}%" if number <= 1 else f"{number:.1f}%"


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "allow", "allowed"}
