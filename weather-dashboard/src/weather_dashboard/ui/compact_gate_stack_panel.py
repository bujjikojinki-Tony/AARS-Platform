from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

from weather_dashboard.ui.data_alignment_panel import build_data_alignment_audit
from weather_dashboard.ui.execution_gate_panel import build_execution_gate_state
from weather_dashboard.ui.compact_panel import semantic_tone, semantic_value_html


def build_compact_gate_stack_summary(
    *,
    market_snapshot: dict | None,
    activated_market_snapshot: dict | None,
    forecast_snapshot: dict | None,
    resolver_rule: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
    validation_freshness_status: dict | None = None,
    label_coverage_report: dict | None = None,
    unified_status_report: dict | None = None,
    gate_stack_api_report: dict | None = None,
    bot_authorized: bool,
    whitelist_path: Path,
) -> dict:
    alignment = build_data_alignment_audit(
        selected_market_snapshot=market_snapshot,
        activated_market_snapshot=activated_market_snapshot,
        forecast_snapshot=forecast_snapshot,
        resolver_rule=resolver_rule,
        probability_state=probability_state,
        comparison_row=comparison_row,
    )
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
    alignment_ok = sum(1 for check in alignment["checks"] if check["level"] == "ok")
    alignment_total = len(alignment["checks"])
    resolver_gate = _build_resolver_gate_summary(resolver_rule)
    promotion_state = _extract_promotion_state(
        probability_state,
        unified_status_report,
        gate_stack_api_report,
    )
    external_gate_stack, gate_source = _resolve_external_gate_stack(
        unified_status_report=unified_status_report,
        gate_stack_api_report=gate_stack_api_report,
        selected_market_id=alignment["selected_market_id"],
    )
    probability_gate_status = "blocked" if gate["probability_mode"] != "live_approved" else "pass"
    freshness_gate_status = (
        "pass"
        if gate["validation_freshness_status"] == "healthy"
        and gate["label_coverage_status"] == "healthy"
        else "blocked"
    )
    authorization_gate_status = "pass" if not resolver_gate["reasons"] and probability_gate_status == "pass" and freshness_gate_status == "pass" else "blocked"
    execution_gate_status = "pass" if gate["gate_status"] == "READY" else "blocked"
    blockers = gate["blockers"]
    if isinstance(external_gate_stack, dict):
        resolver_gate = {
            "status": str(external_gate_stack.get("resolver_gate") or resolver_gate["status"]),
            "reasons": [
                str(item)
                for item in external_gate_stack.get("resolver_gate_reasons") or resolver_gate["reasons"]
            ],
        }
        probability_gate_status = str(external_gate_stack.get("probability_gate") or probability_gate_status)
        freshness_gate_status = str(external_gate_stack.get("freshness_gate") or freshness_gate_status)
        authorization_gate_status = str(
            external_gate_stack.get("authorization_gate") or authorization_gate_status
        )
        execution_gate_status = str(external_gate_stack.get("execution_gate") or execution_gate_status)
        blockers = [str(item) for item in external_gate_stack.get("block_reasons") or blockers]
    severity = _derive_severity_from_blockers(blockers)
    recommended_operator_action = _derive_recommended_action(blockers)
    if isinstance(gate_stack_api_report, dict):
        selected_market_id = str(alignment["selected_market_id"] or "")
        view = _resolve_gate_stack_api_market_view(
            gate_stack_api_report=gate_stack_api_report,
            selected_market_id=selected_market_id,
        )
        source_payload = view if isinstance(view, dict) else gate_stack_api_report
        severity = str(source_payload.get("severity") or severity)
        recommended_operator_action = str(
            source_payload.get("recommended_operator_action") or recommended_operator_action
        )
    return {
        "selected_market_id": alignment["selected_market_id"],
        "ready_for_bot": alignment["ready_for_bot"],
        "alignment_ok": alignment_ok,
        "alignment_total": alignment_total,
        "resolver_gate": resolver_gate["status"],
        "resolver_gate_reasons": resolver_gate["reasons"],
        "probability_gate": probability_gate_status,
        "freshness_gate": freshness_gate_status,
        "authorization_gate": authorization_gate_status,
        "execution_gate": execution_gate_status,
        "probability_mode": gate["probability_mode"],
        "execution_constraint": gate["execution_constraint"],
        "promotion_state": str(
            promotion_state.get("probability_mode")
            or gate.get("probability_mode")
            or "-"
        ),
        "promotion_reason": str(
            promotion_state.get("promotion_reason")
            or gate.get("promotion_reason")
            or "-"
        ),
        "demotion_reason": str(
            promotion_state.get("demotion_reason")
            or gate.get("demotion_reason")
            or "-"
        ),
        "validation_freshness_status": gate["validation_freshness_status"],
        "label_coverage_status": gate["label_coverage_status"],
        "autonomous_execution_eligible": gate["autonomous_execution_eligible"],
        "gate_status": gate["gate_status"],
        "blockers": blockers,
        "gate_source": gate_source,
        "severity": severity,
        "recommended_operator_action": recommended_operator_action,
        "checks": alignment["checks"],
    }


def render_compact_gate_stack_panel(summary: dict) -> None:
    _render_gate_stack_styles()
    checks_html = "".join(
        (
            f"<span class='compact-gate-chip compact-gate-chip--{escape(check['level'])}'>"
            f"{escape(check['name'])}: {escape(check['status'])}"
            "</span>"
        )
        for check in summary["checks"]
    )
    blocker_count = len(summary["blockers"])
    blockers = (
        f"{summary['blockers'][0]} +{blocker_count - 1}"
        if blocker_count > 1
        else (summary["blockers"][0] if blocker_count == 1 else "-")
    )
    primary_blocker = summary["blockers"][0] if summary["blockers"] else "none"
    can_execute = "yes" if summary.get("gate_status") == "READY" else "no"
    gate_tone = semantic_tone("gate_status", summary.get("gate_status"))
    st.markdown(
        f"""
        <section class="compact-gate-stack">
          <div class="compact-gate-stack__top">
            <div>
              <div class="compact-gate-stack__eyebrow">Compact Gate Stack</div>
            <div class="compact-gate-stack__title">{escape(str(summary['selected_market_id'] or '-'))}</div>
            </div>
            <div class="compact-gate-stack__status compact-gate-stack__status--{escape(summary['gate_status'].lower())} compact-gate-stack__status--{escape(gate_tone)}">
              {escape(summary['gate_status'])}
            </div>
          </div>
          <div class="compact-gate-stack__metrics">
            <div><span>Can Execute</span><strong>{semantic_value_html("Can Execute", can_execute)}</strong></div>
            <div><span>Primary Blocker</span><strong>{semantic_value_html("Primary Blocker", str(primary_blocker))}</strong></div>
            <div><span>Constraint</span><strong>{semantic_value_html("Execution Constraint", summary['execution_constraint'])}</strong></div>
            <div><span>Action</span><strong>{semantic_value_html("Next Action", summary.get('recommended_operator_action', 'hold_execution_and_review'))}</strong></div>
          </div>
          <div class="compact-gate-stack__blockers"><span>Promotion State</span><strong>{semantic_value_html("Promotion State", summary.get('promotion_state', '-'))}</strong></div>
          <div class="compact-gate-stack__blockers"><span>Promotion Reason</span><strong>{semantic_value_html("Promotion Reason", summary.get('promotion_reason', '-'))}</strong></div>
          <div class="compact-gate-stack__blockers"><span>Demotion Reason</span><strong>{semantic_value_html("Demotion Reason", summary.get('demotion_reason', '-'))}</strong></div>
          <div class="compact-gate-stack__blockers"><span>Blockers</span><strong>{semantic_value_html("Blockers", blockers)}</strong></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    detail_key = f"compact_gate_stack_details_{str(summary.get('selected_market_id') or 'none')}"
    if st.checkbox("Show gate internals", value=False, key=detail_key):
        st.markdown(
            f"""
            <section class="compact-gate-stack">
              <div class="compact-gate-stack__metrics">
                <div><span>Alignment</span><strong>{semantic_value_html("Alignment", f"{summary['alignment_ok']} / {summary['alignment_total']}")}</strong></div>
                <div><span>Ready For BOT</span><strong>{semantic_value_html("Ready For BOT", summary['ready_for_bot'])}</strong></div>
                <div><span>Probability</span><strong>{semantic_value_html("Probability Mode", summary['probability_mode'])}</strong></div>
                <div><span>Promotion State</span><strong>{semantic_value_html("Promotion State", summary.get('promotion_state', '-'))}</strong></div>
                <div><span>Promotion Reason</span><strong>{semantic_value_html("Promotion Reason", summary.get('promotion_reason', '-'))}</strong></div>
                <div><span>Demotion Reason</span><strong>{semantic_value_html("Demotion Reason", summary.get('demotion_reason', '-'))}</strong></div>
                <div><span>Probability Gate</span><strong>{semantic_value_html("Probability Gate", summary.get('probability_gate', '-'))}</strong></div>
                <div><span>Resolver Gate</span><strong>{semantic_value_html("Resolver Gate", summary.get('resolver_gate', 'pass'))}</strong></div>
                <div><span>Freshness Gate</span><strong>{semantic_value_html("Freshness Gate", summary.get('freshness_gate', '-'))}</strong></div>
                <div><span>Authorization Gate</span><strong>{semantic_value_html("Authorization Gate", summary.get('authorization_gate', '-'))}</strong></div>
                <div><span>Validation</span><strong>{semantic_value_html("Validation Freshness", summary['validation_freshness_status'])}</strong></div>
                <div><span>Coverage</span><strong>{semantic_value_html("Coverage", summary['label_coverage_status'])}</strong></div>
                <div><span>Execution Gate</span><strong>{semantic_value_html("Execution Gate", summary.get('execution_gate', '-'))}</strong></div>
                <div><span>Autonomous Eligible</span><strong>{semantic_value_html("Autonomous Eligible", summary['autonomous_execution_eligible'])}</strong></div>
                <div><span>Gate Source</span><strong>{semantic_value_html("Gate Source", summary.get('gate_source', 'local_fallback'))}</strong></div>
              </div>
              <div class="compact-gate-stack__chips">{checks_html}</div>
            </section>
            """,
            unsafe_allow_html=True,
        )


def _render_gate_stack_styles() -> None:
    st.markdown(
        """
        <style>
        .compact-gate-stack {
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 12px;
            background: rgba(12, 15, 20, 0.98);
            padding: 0.42rem 0.48rem;
            margin: 0.28rem 0;
            box-shadow: none;
        }
        .compact-gate-stack__top {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 0.4rem;
            align-items: center;
        }
        .compact-gate-stack__eyebrow,
        .compact-gate-stack__metrics span,
        .compact-gate-stack__blockers span {
            color: #9aa3ad;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.60rem;
            font-weight: 900;
            letter-spacing: 0.09em;
            text-transform: uppercase;
        }
        .compact-gate-stack__title {
            color: #f7fbff;
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 1.05rem;
            font-weight: 950;
            line-height: 1.08;
        }
        .compact-gate-stack__status {
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 999px;
            background: rgba(255,255,255,0.05);
            color: #f7fbff;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.62rem;
            font-weight: 950;
            padding: 0.18rem 0.46rem;
        }
        .compact-gate-stack__status--ready,
        .compact-gate-stack__status--dry_run_intent_ready {
            border-color: rgba(15, 159, 113, 0.28);
            background: rgba(15, 159, 113, 0.10);
            color: #8fe2b0;
        }
        .compact-gate-stack__status--blocked {
            border-color: rgba(217, 109, 103, 0.30);
            background: rgba(217, 109, 103, 0.10);
            color: #e5a09d;
        }
        .compact-gate-stack__metrics {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.28rem;
            margin-top: 0.34rem;
        }
        .compact-gate-stack__metrics div,
        .compact-gate-stack__blockers {
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 10px;
            background: rgba(255,255,255,0.05);
            padding: 0.26rem 0.32rem;
        }
        .compact-gate-stack__metrics strong,
        .compact-gate-stack__blockers strong {
            display: block;
            margin-top: 0.08rem;
            color: #f7fbff;
            font-size: 0.70rem;
            line-height: 1.14;
            overflow-wrap: anywhere;
        }
        .compact-gate-stack__blockers {
            margin-top: 0.30rem;
        }
        .compact-gate-stack__chips {
            display: flex;
            flex-wrap: wrap;
            gap: 0.22rem;
            margin-top: 0.34rem;
        }
        .compact-gate-chip {
            display: inline-flex;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 999px;
            background: rgba(255,255,255,0.05);
            padding: 0.12rem 0.34rem;
            color: #f7fbff;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.60rem;
        }
        .compact-gate-chip--ok {
            border-color: rgba(15, 159, 113, 0.28);
            background: rgba(15, 159, 113, 0.10);
            color: #8fe2b0;
        }
        .compact-gate-chip--warn {
            border-color: rgba(215, 171, 87, 0.28);
            background: rgba(215, 171, 87, 0.10);
            color: #e6c67c;
        }
        .compact-gate-chip--block {
            border-color: rgba(217, 109, 103, 0.28);
            background: rgba(217, 109, 103, 0.10);
            color: #e5a09d;
        }
        @media (max-width: 1100px) {
            .compact-gate-stack__metrics {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _build_resolver_gate_summary(resolver_rule: dict | None) -> dict:
    rule = resolver_rule or {}
    status = str(rule.get("resolver_status") or rule.get("rule_status") or "").strip().lower()
    confidence = float(rule.get("resolver_confidence") or 0.0)
    source_grade = str(rule.get("source_match_grade") or "").strip().lower()

    reasons: list[str] = []
    if status != "matched":
        reasons.append("resolver_not_matched")
    if confidence < 0.7:
        reasons.append("resolver_confidence_low")
    if source_grade in {"", "unmatched", "family_only"}:
        reasons.append("resolver_source_not_exact")

    return {"status": "blocked" if reasons else "pass", "reasons": reasons}


def _resolve_external_gate_stack(
    *,
    unified_status_report: dict | None,
    gate_stack_api_report: dict | None,
    selected_market_id: str | None,
) -> tuple[dict | None, str]:
    gate_api = gate_stack_api_report or {}
    if isinstance(gate_api, dict) and str(gate_api.get("schema_version") or "") == "gate_stack_api.v1":
        view = _resolve_gate_stack_api_market_view(
            gate_stack_api_report=gate_api,
            selected_market_id=str(selected_market_id or ""),
        )
        if isinstance(view, dict):
            return view, "api"
        gate_stack = gate_api.get("gate_stack")
        if isinstance(gate_stack, dict):
            return gate_stack, "api"

    report = unified_status_report or {}
    if isinstance(report, dict):
        current_market = report.get("current_market") or {}
        current_market_id = str(current_market.get("market_id") or "")
        if selected_market_id and current_market_id == str(selected_market_id):
            gate_stack = report.get("gate_stack")
            if isinstance(gate_stack, dict):
                return gate_stack, "unified_fallback"

    return None, "local_fallback"


def _resolve_gate_stack_api_market_view(*, gate_stack_api_report: dict, selected_market_id: str) -> dict | None:
    if not selected_market_id:
        return None
    views = gate_stack_api_report.get("market_gate_views")
    if not isinstance(views, list):
        return None
    for view in views:
        if not isinstance(view, dict):
            continue
        if str(view.get("market_id") or "") == selected_market_id:
            return view
    return None


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


def _derive_severity_from_blockers(blockers: list[str]) -> str:
    if not blockers:
        return "low"
    if any(token in {"stale_worker", "monitoring_not_healthy", "validation_freshness_unhealthy", "label_coverage_unhealthy"} for token in blockers):
        return "high"
    return "medium"


def _derive_recommended_action(blockers: list[str]) -> str:
    if not blockers:
        return "allow_live_execution"
    first = str(blockers[0])
    if first in {"resolver_not_matched", "resolver_confidence_low", "resolver_source_not_exact"}:
        return "review_resolver_contract"
    if first in {"stale_worker", "monitoring_not_healthy", "validation_freshness_unhealthy", "label_coverage_unhealthy"}:
        return "refresh_pipeline_inputs"
    if first in {"probability_not_live_approved", "execution_constraint_not_live_allowed", "calibration_not_calibrated"}:
        return "manual_advisory_only"
    if first in {"execution_not_ready", "execution_not_live_ready"}:
        return "check_gateway_readiness"
    return "hold_execution_and_review"
