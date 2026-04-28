from __future__ import annotations

from html import escape

import streamlit as st

from weather_dashboard.ui.compact_panel import sanitize_text


def build_unified_status_strip_summary(report: dict | None) -> dict | None:
    if not report:
        return None
    current_market = report.get("current_market") or {}
    probability = report.get("probability") or {}
    promotion_state = probability.get("promotion_state") or report.get("promotion_state") or {}
    validation = report.get("validation") or {}
    family_rollout = validation.get("family_rollout_summary") or report.get("family_rollout_summary") or {}
    execution = report.get("execution") or {}
    operator = report.get("operator") or {}
    source_policy = report.get("source_policy") or {}
    operator_summary = _build_operator_summary(report)
    return {
        "overall_status": str(report.get("overall_status") or "unknown"),
        "market_id": str(current_market.get("market_id") or "-"),
        "comparison_status": str(current_market.get("comparison_status") or "-"),
        "probability_mode": str(probability.get("probability_mode") or "-"),
        "execution_constraint": str(probability.get("execution_constraint") or "-"),
        "promotion_state": str(promotion_state.get("probability_mode") or probability.get("probability_mode") or "-"),
        "promotion_reason": str(
            promotion_state.get("promotion_reason")
            or probability.get("promotion_reason")
            or "-"
        ),
        "demotion_reason": str(
            promotion_state.get("demotion_reason")
            or probability.get("demotion_reason")
            or "-"
        ),
        "validation_freshness": str(validation.get("freshness_status") or "-"),
        "label_coverage": str(validation.get("label_coverage_status") or "-"),
        "family_coverage_ratio": _format_ratio(family_rollout.get("coverage_ratio")),
        "family_ready_ratio": _format_ratio(family_rollout.get("ready_ratio")),
        "family_top_family": str(family_rollout.get("top_family") or "-"),
        "family_top_drift_family": str(family_rollout.get("top_drift_family") or "-"),
        "source_policy": str(source_policy.get("overall_status") or "-"),
        "execution_status": str(execution.get("status") or "-"),
        "can_bot_trade": bool(operator.get("can_bot_trade", False)),
        "operator_mode": str(operator.get("operator_mode") or "-"),
        "mode_badge_label": str((operator.get("mode_badge") or {}).get("label") or "-"),
        "block_reasons": [str(item) for item in report.get("block_reasons") or []],
        "operator_summary_line": operator_summary.get("summary_line"),
        "operator_next_step": operator_summary.get("next_step"),
        "operator_focus": operator_summary.get("current_focus"),
    }


def render_unified_status_strip(report: dict | None) -> None:
    summary = build_unified_status_strip_summary(report)
    if not summary:
        return

    blockers = ", ".join(summary["block_reasons"][:4]) if summary["block_reasons"] else "none"
    st.markdown(
        f"""
        <section class="unified-status-strip">
          <div class="unified-status-strip__title">
            <span class="eyebrow">Unified Status Model</span>
            <strong>Overall {escape(sanitize_text(summary['overall_status']))}</strong>
          </div>
          <div class="unified-status-strip__metrics">
            <div><span>Market</span><strong>{escape(sanitize_text(summary['market_id']))}</strong></div>
            <div><span>Comparison</span><strong>{escape(sanitize_text(summary['comparison_status']))}</strong></div>
            <div><span>Probability</span><strong>{escape(sanitize_text(summary['probability_mode']))}</strong></div>
            <div><span>Constraint</span><strong>{escape(sanitize_text(summary['execution_constraint']))}</strong></div>
            <div><span>Promotion State</span><strong>{escape(sanitize_text(summary['promotion_state']))}</strong></div>
            <div><span>Promotion Reason</span><strong>{escape(sanitize_text(summary['promotion_reason']))}</strong></div>
            <div><span>Demotion Reason</span><strong>{escape(sanitize_text(summary['demotion_reason']))}</strong></div>
            <div><span>Operator</span><strong>{escape(sanitize_text(summary['operator_summary_line']))}</strong></div>
            <div><span>Next Step</span><strong>{escape(sanitize_text(summary['operator_next_step']))}</strong></div>
            <div><span>Validation</span><strong>{escape(sanitize_text(summary['validation_freshness']))}</strong></div>
            <div><span>Coverage</span><strong>{escape(sanitize_text(summary['label_coverage']))}</strong></div>
            <div><span>Family Coverage</span><strong>{escape(sanitize_text(summary['family_coverage_ratio']))}</strong></div>
            <div><span>Family Ready</span><strong>{escape(sanitize_text(summary['family_ready_ratio']))}</strong></div>
            <div><span>Top Family</span><strong>{escape(sanitize_text(summary['family_top_family']))}</strong></div>
            <div><span>Drift Family</span><strong>{escape(sanitize_text(summary['family_top_drift_family']))}</strong></div>
            <div><span>Source Policy</span><strong>{escape(sanitize_text(summary['source_policy']))}</strong></div>
            <div><span>Gateway</span><strong>{escape(sanitize_text(summary['execution_status']))}</strong></div>
            <div><span>Mode</span><strong>{escape(sanitize_text(summary['mode_badge_label']))}</strong></div>
            <div><span>BOT Can Move</span><strong>{escape(str(summary['can_bot_trade']))}</strong></div>
          </div>
          <div class="unified-status-strip__operator">
            <span>Focus</span>
            <strong>{escape(sanitize_text(summary['operator_focus']))}</strong>
            <span style="margin-left: 0.75rem;">Family</span>
            <strong>{escape(sanitize_text(summary['family_top_family']))}</strong>
          </div>
          <div class="unified-status-strip__blockers">
            <span>Block Reasons</span>
            <strong>{escape(sanitize_text(blockers))}</strong>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _build_operator_summary(report: dict) -> dict:
    current_market = report.get("current_market") or {}
    probability = report.get("probability") or {}
    gate_stack = report.get("gate_stack") or {}
    execution = report.get("execution") or {}
    validation = report.get("validation") or {}
    family_rollout = validation.get("family_rollout_summary") or report.get("family_rollout_summary") or {}

    gate_status = str(
        gate_stack.get("execution_gate")
        or execution.get("status")
        or report.get("gate_severity")
        or "unknown"
    )
    reason = _first_non_empty_text(
        gate_stack.get("primary_block_reason"),
        report.get("primary_block_reason"),
        report.get("block_reasons"),
        probability.get("demotion_reason"),
        validation.get("freshness_status"),
        current_market.get("comparison_status"),
    )
    return {
        "summary_line": _build_summary_line(gate_status=gate_status, reason=reason),
        "next_step": _build_next_step(gate_status=gate_status, severity=str(report.get("gate_severity") or "unknown")),
        "current_focus": str(current_market.get("market_id") or "-"),
        "family_focus": str(family_rollout.get("top_family") or "-"),
    }


def _build_summary_line(*, gate_status: str, reason: object) -> str:
    reason_text = _first_non_empty_text(reason, "-")
    if str(gate_status).lower() == "blocked":
        return f"Gate blocked; review {reason_text}"
    if str(gate_status).lower() in {"warning", "stale"}:
        return f"Gate degraded; review {reason_text}"
    return f"Stable; {reason_text}"


def _build_next_step(*, gate_status: str, severity: str) -> str:
    if str(gate_status).lower() == "blocked":
        return "review_gate_block"
    if str(severity).lower() in {"red", "critical"}:
        return "review_market_alert"
    if str(severity).lower() in {"amber", "high"}:
        return "review_market_status"
    return "action"


def _first_non_empty_text(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list) and value:
            first = value[0]
            if isinstance(first, str) and first.strip():
                return first.strip()
        if isinstance(value, dict) and value:
            for key in ("primary_reason", "reason", "value", "status", "message"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
    return "-"


def _format_ratio(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.0%}"
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "-"
