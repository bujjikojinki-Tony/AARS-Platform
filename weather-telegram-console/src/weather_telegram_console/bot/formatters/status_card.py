from __future__ import annotations

from weather_telegram_console.bot.formatters.top_parameter_view_card import (
    format_top_parameter_view_card,
)
from weather_telegram_console.bot.formatters.telegram_text import md_line


def format_status_card(report: dict) -> str:
    current_market = report.get("current_market") or {}
    monitoring = report.get("monitoring") or {}
    probability = report.get("probability") or {}
    probability_contract = probability.get("probability_contract") or {}
    promotion_state = _extract_promotion_state(report, probability, probability_contract)
    execution = report.get("execution") or {}
    operator = report.get("operator") or {}
    source_policy = report.get("source_policy") or {}
    validation = report.get("validation") or {}
    family_rollout = report.get("family_rollout_summary") or (report.get("validation") or {}).get("family_rollout_summary") or {}
    family_rollout_trend = report.get("family_rollout_trend_summary") or validation.get("family_rollout_trend_summary") or {}
    family_rollout_watchlist = report.get("family_rollout_watchlist") or validation.get("family_rollout_watchlist") or {}
    validation_assimilation = report.get("validation_assimilation_summary") or validation.get("validation_assimilation_summary") or {}
    family_anomaly = report.get("family_anomaly_summary") or validation.get("family_anomaly_summary") or {}
    operator_summary = _build_operator_summary(report)
    mode_badge = operator.get("mode_badge") or {}
    gate_stack = report.get("gate_stack") or {}
    workers = monitoring.get("workers") or []
    worker_summary = ", ".join(
        f"{worker.get('label', 'worker')}={worker.get('status', '-')}"
        for worker in workers[:6]
        if isinstance(worker, dict)
    ) or "-"
    block_reasons = ", ".join(str(item) for item in report.get("block_reasons") or []) or "-"
    top_parameter_view = report.get("top_parameter_view")

    return (
        "*AARS Unified Status*\n"
        f"{md_line('Overall', report.get('overall_status'))}\n"
        f"{md_line('Generated At', report.get('generated_at'))}\n\n"
        f"{format_top_parameter_view_card(top_parameter_view)}\n\n"
        "*Operator Summary*\n"
        f"{md_line('Summary', operator_summary.get('summary_line'))}\n"
        f"{md_line('Focus Market', operator_summary.get('current_focus'))}\n"
        f"{md_line('Focus Family', operator_summary.get('current_family'))}\n"
        f"{md_line('Gate Status', operator_summary.get('gate_status'))}\n"
        f"{md_line('Next Step', operator_summary.get('next_step'))}\n"
        f"{md_line('Primary Reason', operator_summary.get('primary_reason'))}\n\n"
        "*Family Rollout*\n"
        f"{md_line('Family Coverage', family_rollout.get('coverage_ratio'))}\n"
        f"{md_line('Family Ready', family_rollout.get('ready_ratio'))}\n"
        f"{md_line('Top Family', family_rollout.get('top_family'))}\n"
        f"{md_line('Drift Family', family_rollout.get('top_drift_family'))}\n"
        f"{md_line('Drift Value', family_rollout.get('top_drift_value'))}\n\n"
        "*Family Rollout Trend*\n"
        f"{md_line('Trend Windows', len(family_rollout_trend.get('trend_windows') or []))}\n"
        f"{md_line('Coverage Movement', family_rollout_trend.get('coverage_movement'))}\n"
        f"{md_line('Ready Movement', family_rollout_trend.get('ready_movement'))}\n"
        f"{md_line('Drift Movement', family_rollout_trend.get('drift_movement'))}\n\n"
        "*Family Rollout Watchlist*\n"
        f"{md_line('Watchlist Count', family_rollout_watchlist.get('watchlist_count'))}\n"
        f"{md_line('Stalled Families', family_rollout_watchlist.get('stalled_family_count'))}\n"
        f"{md_line('Drift Spike Families', family_rollout_watchlist.get('drift_spike_family_count'))}\n"
        f"{md_line('Expansion Backlog', family_rollout_watchlist.get('expansion_backlog_count'))}\n"
        f"{md_line('Top Watchlist Family', family_rollout_watchlist.get('top_watchlist_family'))}\n"
        f"{md_line('Top Attention', family_rollout_watchlist.get('top_watchlist_attention_level'))}\n"
        f"{md_line('Top Reason', family_rollout_watchlist.get('top_watchlist_reason'))}\n\n"
        "*Advanced Anomaly*\n"
        f"{md_line('Family Scan Status', family_anomaly.get('family_scan_status'))}\n"
        f"{md_line('Top Family', family_anomaly.get('top_family'))}\n"
        f"{md_line('Top Score', family_anomaly.get('top_score'))}\n"
        f"{md_line('Top Bucket', family_anomaly.get('top_bucket'))}\n"
        f"{md_line('Signal Summary', family_anomaly.get('signal_summary'))}\n"
        f"{md_line('Bucket Counts', family_anomaly.get('bucket_counts'))}\n"
        f"{md_line('Generated At', family_anomaly.get('generated_at'))}\n\n"
        "*Monitoring*\n"
        f"{md_line('Overall', monitoring.get('overall_status'))}\n"
        f"{md_line('Workers', monitoring.get('worker_count'))}\n"
        f"{md_line('Counts', monitoring.get('counts', {}))}\n"
        f"{md_line('Worker Summary', worker_summary)}\n\n"
        "*Source Policy*\n"
        f"{md_line('Overall', source_policy.get('overall_status'))}\n"
        f"{md_line('Fresh', source_policy.get('fresh_count'))}\n"
        f"{md_line('Stale', source_policy.get('stale_count'))}\n"
        f"{md_line('Unavailable', source_policy.get('unavailable_count'))}\n"
        f"{md_line('Priority Counts', source_policy.get('priority_counts'))}\n"
        f"{md_line('Problem Sources', _summarize_policy_issues(source_policy.get('problem_sources') or []))}\n\n"
        "*Validation*\n"
        f"{md_line('Freshness', validation.get('freshness_status'))}\n"
        f"{md_line('Coverage', validation.get('label_coverage_status'))}\n"
        f"{md_line('Samples', validation.get('validation_sample_count'))}\n"
        f"{md_line('Labeled', validation.get('validation_labeled_sample_count'))}\n"
        f"{md_line('Calibration', validation.get('calibration_status'))}\n"
        f"{md_line('Source Coverage', validation.get('source_coverage'))}\n"
        f"{md_line('Normalization Coverage', validation.get('normalization_coverage'))}\n"
        f"{md_line('Assimilation Status', validation_assimilation.get('assimilation_status'))}\n"
        f"{md_line('Feature Store Ready', validation_assimilation.get('feature_store_ready'))}\n"
        f"{md_line('Label Store Ready', validation_assimilation.get('label_store_ready'))}\n"
        f"{md_line('Backtest Ready', validation_assimilation.get('backtest_ready'))}\n"
        f"{md_line('Assimilation Watchlist', validation_assimilation.get('top_watchlist_family'))}\n"
        f"{md_line('Assimilation Reason', validation_assimilation.get('top_watchlist_reason'))}\n"
        f"{md_line('Family Coverage', family_rollout.get('coverage_ratio'))}\n"
        f"{md_line('Family Ready', family_rollout.get('ready_ratio'))}\n"
        f"{md_line('Rollout Top Family', family_rollout.get('top_family'))}\n"
        f"{md_line('Rollout Drift Family', family_rollout.get('top_drift_family'))}\n"
        f"{md_line('Blockers', validation.get('coverage_blockers') or validation.get('blockers'))}\n\n"
        "*Probability Contract*\n"
        f"{md_line('Contract', probability.get('contract_version') or probability_contract.get('contract_version'))}\n"
        f"{md_line('Mode', probability.get('probability_mode'))}\n"
        f"{md_line('Execution Constraint', probability.get('execution_constraint'))}\n"
        f"{md_line('Calibration', probability.get('calibration_status'))}\n"
        f"{md_line('Adj Edge', probability.get('confidence_adjusted_edge'))}\n\n"
        "*Promotion State*\n"
        f"{md_line('State', promotion_state.get('probability_mode'))}\n"
        f"{md_line('Base Mode', promotion_state.get('base_probability_mode'))}\n"
        f"{md_line('Constraint', promotion_state.get('execution_constraint'))}\n"
        f"{md_line('Reason', promotion_state.get('promotion_reason'))}\n"
        f"{md_line('Demotion', promotion_state.get('demotion_reason'))}\n"
        f"{md_line('Approved For Live', promotion_state.get('approved_for_live'))}\n\n"
        "*Execution*\n"
        f"{md_line('Status', execution.get('status'))}\n"
        f"{md_line('Ready For Live', execution.get('ready_for_live'))}\n"
        f"{md_line('Decision', execution.get('decision'))}\n"
        f"{md_line('Blocking Count', execution.get('blocking_count'))}\n\n"
        "*Operator*\n"
        f"{md_line('BOT Can Move', operator.get('can_bot_trade'))}\n"
        f"{md_line('Human Action Required', operator.get('human_action_required'))}\n"
        f"{md_line('Execution Mode', operator.get('execution_mode'))}\n"
        f"{md_line('Operator Mode', operator.get('operator_mode'))}\n"
        f"{md_line('Mode Badge', mode_badge.get('label'))}\n\n"
        "*Gate Stack*\n"
        f"{md_line('Data Gate', gate_stack.get('data_gate'))}\n"
        f"{md_line('Resolver Gate', gate_stack.get('resolver_gate'))}\n"
        f"{md_line('Probability Gate', gate_stack.get('probability_gate'))}\n"
        f"{md_line('Freshness Gate', gate_stack.get('freshness_gate'))}\n"
        f"{md_line('Authorization Gate', gate_stack.get('authorization_gate'))}\n"
        f"{md_line('Execution Gate', gate_stack.get('execution_gate'))}\n\n"
        f"{md_line('Block Reasons', block_reasons)}"
    )


def _extract_promotion_state(*payloads: dict | None) -> dict:
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        candidate = payload.get("promotion_state")
        if isinstance(candidate, dict):
            return candidate
        nested_probability = payload.get("probability")
        if isinstance(nested_probability, dict):
            candidate = nested_probability.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
        nested_validation = payload.get("validation")
        if isinstance(nested_validation, dict):
            candidate = nested_validation.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
    return {}


def _summarize_policy_issues(sources: list[dict]) -> str:
    if not sources:
        return "-"
    parts = []
    for source in sources[:3]:
        if not isinstance(source, dict):
            continue
        parts.append(
            f"{source.get('source_name', '-')}:"
            f"{source.get('freshness_status', '-')}/"
            f"{source.get('status_reason', '-')}"
        )
    return " | ".join(parts) or "-"


def _build_operator_summary(report: dict) -> dict:
    current_market = report.get("current_market") or {}
    probability = report.get("probability") or {}
    gate_stack = report.get("gate_stack") or {}
    execution = report.get("execution") or {}
    validation = report.get("validation") or {}
    family_rollout = report.get("family_rollout_summary") or validation.get("family_rollout_summary") or {}
    family_rollout_trend = report.get("family_rollout_trend_summary") or validation.get("family_rollout_trend_summary") or {}
    family_rollout_watchlist = report.get("family_rollout_watchlist") or validation.get("family_rollout_watchlist") or {}

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
    summary_line = _build_summary_line(gate_status=gate_status, reason=reason)
    action = str(
        report.get("recommended_operator_action")
        or gate_stack.get("recommended_operator_action")
        or _build_next_step(gate_status=gate_status, severity=str(report.get("gate_severity") or "unknown"))
    )
    return {
        "schema_version": "operator_summary.v1",
        "current_focus": str(current_market.get("market_id") or "-"),
        "current_family": str(current_market.get("market_family") or "-"),
        "family_coverage": family_rollout.get("coverage_ratio"),
        "family_ready": family_rollout.get("ready_ratio"),
        "family_top_family": str(family_rollout.get("top_family") or "-"),
        "family_top_drift_family": str(family_rollout.get("top_drift_family") or "-"),
        "family_trend_windows": len(family_rollout_trend.get("trend_windows") or []),
        "family_trend_coverage_movement": family_rollout_trend.get("coverage_movement"),
        "family_trend_ready_movement": family_rollout_trend.get("ready_movement"),
        "family_trend_drift_movement": family_rollout_trend.get("drift_movement"),
        "family_watchlist_count": family_rollout_watchlist.get("watchlist_count"),
        "family_watchlist_top_family": family_rollout_watchlist.get("top_watchlist_family"),
        "family_watchlist_top_attention": family_rollout_watchlist.get("top_watchlist_attention_level"),
        "family_watchlist_top_reason": family_rollout_watchlist.get("top_watchlist_reason"),
        "gate_status": gate_status,
        "recommended_operator_action": action,
        "primary_reason": reason,
        "summary_line": summary_line,
        "next_step": _build_next_step(gate_status=gate_status, severity=str(report.get("gate_severity") or "unknown")),
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
