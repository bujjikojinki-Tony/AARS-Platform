from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from weather_comparison_engine.governance.page_context import normalize_page_context
from weather_comparison_engine.settings import BUY_SELL_DECISION_POLICY_JSON


def build_market_workstation_view(
    *,
    selected_market_id: str | None,
    top_parameter_view: dict | None,
    page_context: dict | None = None,
    resolver_rule: dict | None = None,
    comparison_row: dict | None = None,
    gate_summary: dict | None = None,
    opportunity_context: dict | None = None,
    validation_summary: dict | None = None,
    forecast_snapshot: dict | None = None,
    observation_snapshot: dict | None = None,
    evidence_history_rows: list[dict] | None = None,
    latest_alert: dict | None = None,
    latest_anomaly: dict | None = None,
    latest_ops: dict | None = None,
    latest_family_scan_report: dict | None = None,
    opportunity_policy_bundle: dict | None = None,
    now: datetime | None = None,
) -> dict:
    """Build the page-level workstation contract without creating new facts."""
    now = now or datetime.now(timezone.utc)
    page_context = normalize_page_context(
        page_context,
        source_page=str((page_context or {}).get("source_page") or "unknown"),
        target_page=str((page_context or {}).get("target_page") or "workstation"),
        selected_market_id=str(selected_market_id or (page_context or {}).get("selected_market_id") or ""),
        selected_row_id=str((page_context or {}).get("selected_row_id") or ""),
        entry_reason=str((page_context or {}).get("entry_reason") or "open_workstation"),
        entry_context=(page_context or {}).get("entry_context") if isinstance(page_context, dict) else {},
        upstream_refs={
            "top_parameter_ref": str((top_parameter_view or {}).get("generated_at") or "-"),
        },
        now=now,
    )
    top_parameter_view = top_parameter_view if isinstance(top_parameter_view, dict) else {}
    resolver_rule = resolver_rule if isinstance(resolver_rule, dict) else {}
    comparison_row = comparison_row if isinstance(comparison_row, dict) else {}
    gate_summary = gate_summary if isinstance(gate_summary, dict) else {}
    opportunity_context = opportunity_context if isinstance(opportunity_context, dict) else {}
    validation_summary = validation_summary if isinstance(validation_summary, dict) else {}
    forecast_snapshot = forecast_snapshot if isinstance(forecast_snapshot, dict) else {}
    observation_snapshot = observation_snapshot if isinstance(observation_snapshot, dict) else {}
    evidence_history_rows = evidence_history_rows if isinstance(evidence_history_rows, list) else []
    latest_alert = latest_alert if isinstance(latest_alert, dict) else {}
    latest_anomaly = latest_anomaly if isinstance(latest_anomaly, dict) else {}
    latest_ops = latest_ops if isinstance(latest_ops, dict) else {}
    latest_family_scan_report = latest_family_scan_report if isinstance(latest_family_scan_report, dict) else {}
    opportunity_policy_bundle = opportunity_policy_bundle if isinstance(opportunity_policy_bundle, dict) else {}

    market_id = str(
        selected_market_id
        or top_parameter_view.get("market_id")
        or comparison_row.get("market_id")
        or resolver_rule.get("market_id")
        or ""
    )

    return {
        "schema_version": "market_workstation_view.v1",
        "generated_at": now.isoformat(),
        "selected_market_id": market_id,
        "page_context": page_context,
        "top_parameter_view": top_parameter_view,
        "rule_source_model_panel": _build_rule_source_model_panel(
            top_parameter_view=top_parameter_view,
            resolver_rule=resolver_rule,
            opportunity_context=opportunity_context,
        ),
        "evidence_timeline": _build_evidence_timeline(
            history_rows=evidence_history_rows,
            top_parameter_view=top_parameter_view,
            forecast_snapshot=forecast_snapshot,
            observation_snapshot=observation_snapshot,
            comparison_row=comparison_row,
            gate_summary=gate_summary,
            latest_alert=latest_alert,
            latest_anomaly=latest_anomaly,
            latest_ops=latest_ops,
        ),
        "validation_compare_panel": _build_validation_compare_panel(validation_summary, comparison_row),
        "buy_sell_decision_panel": _build_buy_sell_decision_panel(
            top_parameter_view=top_parameter_view,
            validation_summary=validation_summary,
            gate_summary=gate_summary,
            opportunity_context=opportunity_context,
            opportunity_policy_bundle=opportunity_policy_bundle,
        ),
        "opportunity_linkage_panel": _build_opportunity_linkage_panel(opportunity_context),
        "family_anomaly_summary": _build_family_anomaly_summary(
            latest_family_scan_report=latest_family_scan_report,
            latest_anomaly=latest_anomaly,
            opportunity_context=opportunity_context,
        ),
        "entry_context": _build_entry_context(opportunity_context, page_context=page_context),
        "gate_advisory_panel": _build_gate_advisory_panel(gate_summary, comparison_row, latest_alert, latest_anomaly),
        "latest_alert": latest_alert,
        "latest_anomaly": latest_anomaly,
        "latest_gate": gate_summary,
        "latest_ops": latest_ops,
        "upstream_refs": _build_upstream_refs(
            market_id=market_id,
            top_parameter_view=top_parameter_view,
            resolver_rule=resolver_rule,
            comparison_row=comparison_row,
            gate_summary=gate_summary,
        ),
    }


def _load_buy_sell_decision_policy(opportunity_policy_bundle: dict[str, Any]) -> dict[str, Any]:
    policy = opportunity_policy_bundle.get("buy_sell_decision_policy") if isinstance(opportunity_policy_bundle, dict) else {}
    if isinstance(policy, dict) and policy:
        return policy
    path = Path(BUY_SELL_DECISION_POLICY_JSON)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _build_buy_sell_decision_panel(
    *,
    top_parameter_view: dict[str, Any],
    validation_summary: dict[str, Any],
    gate_summary: dict[str, Any],
    opportunity_context: dict[str, Any],
    opportunity_policy_bundle: dict[str, Any],
) -> dict[str, Any]:
    policy = _load_buy_sell_decision_policy(opportunity_policy_bundle)
    polymarket = top_parameter_view.get("polymarket") if isinstance(top_parameter_view.get("polymarket"), dict) else {}
    decision = top_parameter_view.get("decision") if isinstance(top_parameter_view.get("decision"), dict) else {}
    source_contract = top_parameter_view.get("source_contract") if isinstance(top_parameter_view.get("source_contract"), dict) else {}

    market_probability = _to_float(polymarket.get("market_implied_probability"))
    yes_price = _to_float(polymarket.get("yes_price"))
    no_price = _to_float(polymarket.get("no_price"))
    fair_value = _to_float(decision.get("fair_value"))
    edge = _to_float(decision.get("edge"))
    probability_mode = str(decision.get("probability_mode") or "-")
    freshness_status = str(source_contract.get("freshness_status") or validation_summary.get("freshness_status") or "-")
    source_precision_score = _to_float(opportunity_context.get("source_precision_score"))
    validation_coverage = _to_float(
        validation_summary.get("labeled_ratio")
        or validation_summary.get("label_coverage")
        or validation_summary.get("coverage_ratio")
    )
    can_execute = gate_summary.get("can_execute")
    execution_constraint = str(decision.get("execution_constraint") or gate_summary.get("execution_constraint") or "-")
    primary_block_reason = str(
        gate_summary.get("primary_block_reason")
        or decision.get("primary_block_reason")
        or "-"
    )

    allowed_freshness = set((policy.get("preconditions") or {}).get("allowed_freshness_statuses") or [])
    blocked_freshness = set((policy.get("preconditions") or {}).get("blocked_freshness_statuses") or [])
    min_source_precision = _to_float((policy.get("preconditions") or {}).get("min_source_precision_score")) or 0.7
    min_validation_coverage = _to_float((policy.get("preconditions") or {}).get("min_validation_coverage")) or 0.8
    yes_edge_min = _to_float((policy.get("thresholds") or {}).get("research_yes_edge_min")) or 0.05
    no_edge_max = _to_float((policy.get("thresholds") or {}).get("research_no_edge_max")) or -0.05
    no_trade_abs_edge_max = _to_float((policy.get("thresholds") or {}).get("no_trade_abs_edge_max")) or 0.03

    missing_probability_inputs = any(
        value is None for value in (market_probability, fair_value, edge)
    ) or probability_mode in {"", "-", "unknown"}
    if missing_probability_inputs:
        outcome = "refresh_inputs"
        reason = "Market implied probability, fair value, or edge is missing."
    elif freshness_status in blocked_freshness:
        outcome = "refresh_inputs"
        reason = f"Freshness status is {freshness_status}."
    elif validation_coverage is not None and validation_coverage < min_validation_coverage:
        outcome = "review_evidence"
        reason = f"Validation coverage {validation_coverage:.2f} is below {min_validation_coverage:.2f}."
    elif source_precision_score is not None and source_precision_score < min_source_precision:
        outcome = "review_evidence"
        reason = f"Source precision score {source_precision_score:.2f} is below {min_source_precision:.2f}."
    elif freshness_status not in allowed_freshness and freshness_status not in {"-", ""}:
        outcome = "review_evidence"
        reason = f"Freshness status {freshness_status} requires evidence review."
    elif edge is not None and abs(edge) <= no_trade_abs_edge_max:
        outcome = "watch_only"
        reason = f"Edge {edge:.4f} is within no-trade band."
    elif edge is not None and edge >= yes_edge_min:
        outcome = "research_buy_yes"
        reason = "Fair value is above market implied probability."
    elif edge is not None and edge <= no_edge_max:
        outcome = "research_buy_no"
        reason = "Fair value is below market implied probability."
    else:
        outcome = "watch_only"
        reason = "Edge does not pass directional thresholds."

    return {
        "schema_version": "buy_sell_decision_panel.v1",
        "policy_ref": str(policy.get("policy_id") or "buy_sell_decision_policy.v1"),
        "decision_outcome": outcome,
        "decision_reason": reason,
        "market_implied_probability": market_probability,
        "yes_price": yes_price if yes_price is not None else "-",
        "no_price": no_price if no_price is not None else "-",
        "fair_value": fair_value if fair_value is not None else "-",
        "edge": edge if edge is not None else "-",
        "probability_mode": probability_mode,
        "freshness_status": freshness_status,
        "source_precision_score": source_precision_score if source_precision_score is not None else "-",
        "validation_coverage": validation_coverage if validation_coverage is not None else "-",
        "source_match_grade": str(source_contract.get("source_match_grade") or "-"),
        "can_execute": can_execute,
        "primary_block_reason": primary_block_reason,
        "execution_constraint": execution_constraint,
        "execution_boundary": "gate_stack_api.v1_only",
        "notes": [
            "This panel provides research direction only.",
            "Execution permission remains owned by gate_stack_api.v1.",
        ],
    }


def _build_rule_source_model_panel(
    *,
    top_parameter_view: dict,
    resolver_rule: dict,
    opportunity_context: dict,
) -> dict:
    source_contract = top_parameter_view.get("source_contract") if isinstance(top_parameter_view.get("source_contract"), dict) else {}
    normalization = top_parameter_view.get("normalization") if isinstance(top_parameter_view.get("normalization"), dict) else {}
    return {
        "market_rule": {
            "market_family": top_parameter_view.get("market_family") or resolver_rule.get("market_family"),
            "variable_name": top_parameter_view.get("variable_name") or resolver_rule.get("variable_name"),
            "location_name": top_parameter_view.get("location_name") or resolver_rule.get("location_name"),
            "station_id": (top_parameter_view.get("weather") or {}).get("station_id") if isinstance(top_parameter_view.get("weather"), dict) else resolver_rule.get("station_id"),
            "target_date": top_parameter_view.get("target_date") or resolver_rule.get("target_date"),
            "band_scheme": resolver_rule.get("band_scheme") or source_contract.get("band_scheme") or "-",
        },
        "source_contract": {
            "required_sources": source_contract.get("required_sources") or resolver_rule.get("required_sources") or [],
            "settlement_source_type": source_contract.get("settlement_source_type") or resolver_rule.get("settlement_source_type") or "-",
            "official_vs_proxy_source": source_contract.get("official_vs_proxy_source") or resolver_rule.get("official_vs_proxy_source") or "-",
            "source_match_grade": source_contract.get("source_match_grade") or resolver_rule.get("source_match_grade") or "-",
            "official_source_url": source_contract.get("official_source_url") or resolver_rule.get("official_source_url") or "-",
            "resolver_confidence": resolver_rule.get("resolver_confidence") or "-",
        },
        "best_model": {
            "best_model": opportunity_context.get("best_model") or "-",
            "best_source_stack": opportunity_context.get("best_source_stack") or [],
            "best_model_reason": opportunity_context.get("best_model_reason") or "-",
        },
        "measurement_policy": {
            "canonical_unit": top_parameter_view.get("canonical_unit") or normalization.get("canonical_unit") or "-",
            "precision_policy_ref": source_contract.get("precision_policy_ref") or normalization.get("precision_policy_ref") or "-",
            "rounding_policy_ref": source_contract.get("rounding_policy_ref") or normalization.get("rounding_policy_ref") or "-",
            "band_mapping_policy_ref": source_contract.get("band_mapping_policy_ref") or normalization.get("band_mapping_policy_ref") or "-",
        },
        "difficulty": {
            "difficulty_score": opportunity_context.get("difficulty_score"),
            "difficulty_label": opportunity_context.get("difficulty_label"),
            "difficulty_components": opportunity_context.get("difficulty_components") or {},
        },
    }


def _build_validation_compare_panel(validation_summary: dict, comparison_row: dict) -> dict:
    promotion_state = validation_summary.get("promotion_state") or validation_summary.get("probability_mode") or "-"
    blockers = validation_summary.get("blockers") if isinstance(validation_summary.get("blockers"), list) else []
    return {
        "schema_version": "validation_compare_panel.v1",
        "best_model": validation_summary.get("best_model") or comparison_row.get("best_model") or "-",
        "label_coverage": validation_summary.get("labeled_ratio")
        or validation_summary.get("label_coverage")
        or validation_summary.get("coverage_ratio")
        or "-",
        "coverage_status": validation_summary.get("coverage_status") or "-",
        "validation_freshness": validation_summary.get("freshness_status") or "-",
        "freshness_seconds": validation_summary.get("freshness_seconds") or "-",
        "comparison_status": comparison_row.get("comparison_status") or "-",
        "fair_value": comparison_row.get("fair_value") or "-",
        "edge": comparison_row.get("confidence_adjusted_gap") or comparison_row.get("confidence_adjusted_edge") or "-",
        "calibration_status": validation_summary.get("calibration_status") or "-",
        "deployment_mode": validation_summary.get("deployment_mode") or "-",
        "approved_for_live": validation_summary.get("approved_for_live"),
        "sample_count": validation_summary.get("sample_count") or "-",
        "labeled_sample_count": validation_summary.get("labeled_sample_count") or "-",
        "brier_score": validation_summary.get("brier_score") or "-",
        "calibration_error": validation_summary.get("calibration_error") or "-",
        "hit_rate": validation_summary.get("hit_rate") or "-",
        "promotion_state": promotion_state,
        "promotion_reason": validation_summary.get("promotion_reason") or "-",
        "demotion_reason": validation_summary.get("demotion_reason") or "-",
        "primary_blocker": blockers[0] if blockers else "none",
        "canonical_ratio": validation_summary.get("canonical_ratio") or "-",
        "source_policy_coverage": validation_summary.get("source_policy_coverage") or "-",
        "normalization_coverage": validation_summary.get("normalization_coverage") or "-",
        "family_coverage_ratio": validation_summary.get("family_coverage_ratio") or "-",
        "family_ready_ratio": validation_summary.get("family_ready_ratio") or "-",
        "top_watchlist_family": validation_summary.get("top_watchlist_family") or "-",
        "top_watchlist_reason": validation_summary.get("top_watchlist_reason") or "-",
    }


def _to_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_opportunity_linkage_panel(opportunity_context: dict) -> dict:
    refs = opportunity_context.get("upstream_refs") if isinstance(opportunity_context.get("upstream_refs"), dict) else {}
    return {
        "schema_version": "opportunity_workstation_linkage.v1",
        "row_id": opportunity_context.get("row_id") or "-",
        "city": opportunity_context.get("city") or "-",
        "market_family": opportunity_context.get("market_family") or "-",
        "opportunity_score": opportunity_context.get("opportunity_score"),
        "opportunity_rank": opportunity_context.get("opportunity_rank"),
        "difficulty_score": opportunity_context.get("difficulty_score"),
        "difficulty_label": opportunity_context.get("difficulty_label"),
        "recommended_action": opportunity_context.get("recommended_action") or "-",
        "best_model": opportunity_context.get("best_model") or "-",
        "best_source_stack": opportunity_context.get("best_source_stack") or [],
        "opportunity_reason": opportunity_context.get("opportunity_reason") or "-",
        "difficulty_reason": opportunity_context.get("difficulty_reason") or "-",
        "market_refs": refs.get("market_ids") or [],
        "alert_refs": refs.get("alert_refs") or [],
        "anomaly_refs": refs.get("anomaly_refs") or [],
    }


def _build_family_anomaly_summary(
    *,
    latest_family_scan_report: dict,
    latest_anomaly: dict,
    opportunity_context: dict,
) -> dict:
    family_summaries = [item for item in (latest_family_scan_report.get("family_summaries") or []) if isinstance(item, dict)]
    ranked = sorted(
        family_summaries,
        key=lambda item: float(item.get("max_intervention_like_score") or 0.0),
        reverse=True,
    )
    top_family = ranked[0] if ranked else {}
    signal_summary = latest_family_scan_report.get("signal_summary") or {}
    return {
        "schema_version": "family_anomaly_summary.v1",
        "status": str(latest_family_scan_report.get("input_mode") or latest_family_scan_report.get("schema_version") or "-"),
        "top_family": str(top_family.get("market_family") or latest_anomaly.get("market_family") or opportunity_context.get("market_family") or "-"),
        "top_score": top_family.get("max_intervention_like_score") or latest_anomaly.get("anomaly_score") or "-",
        "top_bucket": _bucket_for_score(top_family.get("max_intervention_like_score") or latest_anomaly.get("anomaly_score")),
        "signal_summary": _format_signal_summary(signal_summary),
        "bucket_counts": latest_family_scan_report.get("anomaly_bucket_counts") or {},
        "generated_at": latest_family_scan_report.get("generated_at") or latest_anomaly.get("generated_at") or "-",
    }


def _build_entry_context(opportunity_context: dict, *, page_context: dict[str, Any]) -> dict:
    opportunity_page_context = (
        opportunity_context.get("page_context") if isinstance(opportunity_context.get("page_context"), dict) else {}
    )
    merged_page_context = {**opportunity_page_context, **(page_context if isinstance(page_context, dict) else {})}
    source_page = str(merged_page_context.get("source_page") or "")
    if source_page in {"", "-", "unknown"} and opportunity_context:
        source_page = "opportunity_board"
    target_page = str(merged_page_context.get("target_page") or "")
    if target_page in {"", "-", "unknown"}:
        target_page = "workstation"
    return {
        "schema_version": "entry_context.v1",
        "source_page": source_page or "-",
        "target_page": target_page,
        "row_id": opportunity_context.get("row_id") or "-",
        "selected_market_id": str(merged_page_context.get("selected_market_id") or opportunity_context.get("market_id") or "-"),
        "opportunity_score": opportunity_context.get("opportunity_score"),
        "difficulty_score": opportunity_context.get("difficulty_score"),
        "recommended_action": opportunity_context.get("recommended_action") or "-",
        "best_model": opportunity_context.get("best_model") or "-",
        "best_source_stack": opportunity_context.get("best_source_stack") or [],
        "entry_reason": str(merged_page_context.get("entry_reason") or "open_workstation"),
        "page_context": merged_page_context,
    }


def _format_signal_summary(summary: dict) -> str:
    if not isinstance(summary, dict) or not summary:
        return "-"
    return (
        f"pv={summary.get('price_velocity_high_count', 0)} "
        f"edge={summary.get('edge_dislocation_high_count', 0)} "
        f"mismatch={summary.get('evidence_mismatch_count', 0)} "
        f"stress={summary.get('microstructure_stress_high_count', 0)} "
        f"peer={summary.get('peer_outlier_count', 0)} "
        f"high={summary.get('intervention_like_high_count', 0)}"
    )


def _bucket_for_score(score: object) -> str:
    try:
        value = float(score or 0.0)
    except (TypeError, ValueError):
        value = 0.0
    if value >= 0.8:
        return "high"
    if value >= 0.5:
        return "medium"
    return "low"


def _build_evidence_timeline(
    *,
    history_rows: list[dict],
    top_parameter_view: dict,
    forecast_snapshot: dict,
    observation_snapshot: dict,
    comparison_row: dict,
    gate_summary: dict,
    latest_alert: dict,
    latest_anomaly: dict,
    latest_ops: dict,
) -> dict:
    polymarket = top_parameter_view.get("polymarket") if isinstance(top_parameter_view.get("polymarket"), dict) else {}
    weather = top_parameter_view.get("weather") if isinstance(top_parameter_view.get("weather"), dict) else {}
    forecast = top_parameter_view.get("forecast") if isinstance(top_parameter_view.get("forecast"), dict) else {}
    source_contract = top_parameter_view.get("source_contract") if isinstance(top_parameter_view.get("source_contract"), dict) else {}

    market_points = [
        {
            "timestamp": row.get("timestamp"),
            "market_probability": row.get("market_probability") or row.get("market_implied_probability"),
            "comparison_status": row.get("comparison_status"),
            "confidence_adjusted_edge": row.get("confidence_adjusted_edge") or row.get("confidence_adjusted_gap"),
        }
        for row in history_rows[-5:]
        if isinstance(row, dict)
    ]
    if not market_points:
        market_points = [
            {
                "timestamp": comparison_row.get("timestamp") or top_parameter_view.get("generated_at"),
                "market_probability": polymarket.get("market_implied_probability"),
                "comparison_status": comparison_row.get("comparison_status"),
                "confidence_adjusted_edge": comparison_row.get("confidence_adjusted_edge")
                or comparison_row.get("confidence_adjusted_gap"),
            }
        ]

    forecast_point = {
        "timestamp": forecast_snapshot.get("forecast_timestamp")
        or forecast_snapshot.get("timestamp")
        or forecast.get("forecast_timestamp"),
        "display_value": forecast_snapshot.get("display_value")
        or forecast_snapshot.get("forecast_display_value")
        or forecast.get("display_value")
        or forecast.get("forecast_value"),
        "canonical_value": forecast_snapshot.get("canonical_value") or forecast.get("canonical_value"),
        "canonical_unit": forecast_snapshot.get("canonical_unit") or top_parameter_view.get("canonical_unit"),
        "model_band": forecast_snapshot.get("model_band") or forecast.get("model_band"),
    }
    observation_point = {
        "timestamp": observation_snapshot.get("observed_at")
        or observation_snapshot.get("observed_valid_time")
        or weather.get("observed_at"),
        "display_value": observation_snapshot.get("display_value")
        or observation_snapshot.get("observation_display_value")
        or weather.get("display_value")
        or weather.get("observation_value"),
        "canonical_value": observation_snapshot.get("canonical_value") or weather.get("canonical_value"),
        "canonical_unit": observation_snapshot.get("canonical_unit") or top_parameter_view.get("canonical_unit"),
        "observation_band": observation_snapshot.get("observation_band") or weather.get("observation_band"),
        "source_match_grade": source_contract.get("source_match_grade"),
    }
    markers = _build_event_markers(
        latest_alert=latest_alert,
        latest_anomaly=latest_anomaly,
        gate_summary=gate_summary,
        latest_ops=latest_ops,
    )
    return {
        "schema_version": "evidence_timeline.v1",
        "input_mode": "canonical_only",
        "status": "ready",
        "tracks": {
            "market_probability": {"point_count": len(market_points), "latest": market_points[-1] if market_points else {}},
            "forecast": {"point_count": 1 if _has_value(forecast_point) else 0, "latest": forecast_point},
            "observation": {"point_count": 1 if _has_value(observation_point) else 0, "latest": observation_point},
            "events": {"marker_count": len(markers), "markers": markers},
        },
        "marker_count": len(markers),
        "history_point_count": len(market_points),
    }


def _build_event_markers(
    *,
    latest_alert: dict,
    latest_anomaly: dict,
    gate_summary: dict,
    latest_ops: dict,
) -> list[dict]:
    markers: list[dict] = []
    if latest_alert:
        markers.append(
            {
                "type": "market_alert",
                "severity": latest_alert.get("severity"),
                "reason": latest_alert.get("primary_reason"),
                "timestamp": latest_alert.get("generated_at"),
            }
        )
    if latest_anomaly:
        markers.append(
            {
                "type": "family_anomaly",
                "score": latest_anomaly.get("anomaly_score"),
                "reason": latest_anomaly.get("primary_reason"),
                "timestamp": latest_anomaly.get("generated_at"),
            }
        )
    if gate_summary:
        markers.append(
            {
                "type": "gate",
                "status": gate_summary.get("gate_status") or gate_summary.get("execution_gate"),
                "reason": _first_item(gate_summary.get("blockers")) or gate_summary.get("primary_block_reason"),
                "timestamp": gate_summary.get("generated_at") or gate_summary.get("gate_generated_at"),
            }
        )
    if latest_ops:
        markers.append(
            {
                "type": "ops",
                "status": latest_ops.get("severity") or latest_ops.get("status"),
                "reason": latest_ops.get("reason") or latest_ops.get("primary_reason"),
                "timestamp": latest_ops.get("generated_at") or latest_ops.get("timestamp"),
            }
        )
    return markers


def _build_gate_advisory_panel(
    gate_summary: dict,
    comparison_row: dict,
    latest_alert: dict | None,
    latest_anomaly: dict | None,
) -> dict:
    blockers = [str(item) for item in gate_summary.get("blockers") or []]
    return {
        "gate_summary": {
            "data_gate": gate_summary.get("data_gate") or "-",
            "resolver_gate": gate_summary.get("resolver_gate") or "-",
            "probability_gate": gate_summary.get("probability_gate") or "-",
            "freshness_gate": gate_summary.get("freshness_gate") or "-",
            "authorization_gate": gate_summary.get("authorization_gate") or "-",
            "execution_gate": gate_summary.get("execution_gate") or "-",
            "can_execute": "yes" if str(gate_summary.get("gate_status") or "").upper() == "READY" else "no",
            "primary_block_reason": blockers[0] if blockers else "none",
        },
        "advisory_summary": {
            "recommended_operator_action": gate_summary.get("recommended_operator_action") or comparison_row.get("action_hint") or "hold_execution_and_review",
            "advisory_reason": blockers[0] if blockers else comparison_row.get("comparison_reason") or "-",
            "latest_alert_summary": (latest_alert or {}).get("primary_reason") or (latest_alert or {}).get("severity") or "-",
            "latest_anomaly_summary": (latest_anomaly or {}).get("primary_reason") or (latest_anomaly or {}).get("anomaly_score") or "-",
        },
        "dry_run_area": {
            "simulate_review": "available",
            "create_dry_run_intent": "available_when_gate_context_ready",
            "execution_boundary": "gate_stack_api.v1_only",
        },
    }


def _build_upstream_refs(
    *,
    market_id: str,
    top_parameter_view: dict,
    resolver_rule: dict,
    comparison_row: dict,
    gate_summary: dict,
) -> dict:
    return {
        "market_id": market_id,
        "top_parameter_view_version": top_parameter_view.get("schema_version") or "-",
        "resolver_ref": resolver_rule.get("rule_id") or resolver_rule.get("market_id") or market_id,
        "comparison_ref": comparison_row.get("timestamp") or comparison_row.get("market_snapshot_ref") or "-",
        "gate_ref": gate_summary.get("gate_source") or "gate_stack_api.v1",
    }


def _has_value(point: dict) -> bool:
    return any(value not in (None, "", "-") for value in point.values())


def _first_item(value: object) -> object:
    if isinstance(value, list) and value:
        return value[0]
    return None
