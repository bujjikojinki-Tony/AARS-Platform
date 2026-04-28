from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from weather_dashboard.ui.compact_panel import (
    default_market_evidence_curve_legend_items,
    default_state_legend_items,
    render_chart_legend_card,
    render_live_banner,
    render_compact_note,
    render_legend_card,
    render_kv_section,
    render_stat_strip,
    render_panel_title,
    sanitize_text,
    with_data_quality,
)


def find_opportunity_context(
    board: dict | None,
    *,
    market_id: str | None,
    city: str | None = None,
    market_family: str | None = None,
) -> dict:
    rows = (board or {}).get("rows") or []
    market_id_text = str(market_id or "").strip()
    for row in rows:
        if not isinstance(row, dict):
            continue
        market_ids = (row.get("upstream_refs") or {}).get("market_ids") or []
        if market_id_text and market_id_text in {str(item) for item in market_ids}:
            return row

    city_text = str(city or "").strip().lower()
    family_text = str(market_family or "").strip().lower()
    if not city_text or not family_text:
        return {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if (
            str(row.get("city") or "").strip().lower() == city_text
            and str(row.get("market_family") or "").strip().lower() == family_text
        ):
            return row
    return {}


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
    now: datetime | None = None,
) -> dict:
    """Build a dashboard-side workstation view without creating new market facts."""
    now = now or datetime.now(timezone.utc)
    top_parameter_view = top_parameter_view if isinstance(top_parameter_view, dict) else {}
    page_context = page_context if isinstance(page_context, dict) else {}
    resolver_rule = resolver_rule if isinstance(resolver_rule, dict) else {}
    comparison_row = comparison_row if isinstance(comparison_row, dict) else {}
    gate_summary = gate_summary if isinstance(gate_summary, dict) else {}
    opportunity_context = opportunity_context if isinstance(opportunity_context, dict) else {}
    validation_summary = validation_summary if isinstance(validation_summary, dict) else {}
    forecast_snapshot = forecast_snapshot if isinstance(forecast_snapshot, dict) else {}
    observation_snapshot = observation_snapshot if isinstance(observation_snapshot, dict) else {}
    evidence_history_rows = evidence_history_rows if isinstance(evidence_history_rows, list) else []
    latest_alert = (
        latest_alert
        if isinstance(latest_alert, dict) and latest_alert
        else _latest_alert_from_opportunity(opportunity_context)
    )
    latest_anomaly = (
        latest_anomaly
        if isinstance(latest_anomaly, dict) and latest_anomaly
        else _latest_anomaly_from_opportunity(opportunity_context)
    )
    latest_ops = latest_ops if isinstance(latest_ops, dict) else {}
    latest_family_scan_report = latest_family_scan_report if isinstance(latest_family_scan_report, dict) else {}

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
        ),
        "opportunity_linkage_panel": _build_opportunity_linkage_panel(opportunity_context),
        "entry_context": _build_entry_context(opportunity_context),
        "family_anomaly_summary": _build_family_anomaly_summary(
            latest_family_scan_report=latest_family_scan_report,
            latest_anomaly=latest_anomaly,
            opportunity_context=opportunity_context,
        ),
        "gate_advisory_panel": _build_gate_advisory_panel(
            gate_summary=gate_summary,
            comparison_row=comparison_row,
            latest_alert=latest_alert,
            latest_anomaly=latest_anomaly,
        ),
        "latest_alert": latest_alert,
        "latest_anomaly": latest_anomaly,
        "latest_gate": gate_summary,
        "latest_ops": latest_ops,
        "opportunity_context": opportunity_context,
        "upstream_refs": {
            "market_id": market_id,
            "top_parameter_view_version": top_parameter_view.get("schema_version") or "-",
            "resolver_ref": resolver_rule.get("rule_id") or resolver_rule.get("market_id") or market_id,
            "comparison_ref": comparison_row.get("timestamp") or comparison_row.get("market_snapshot_ref") or "-",
            "gate_ref": gate_summary.get("gate_source") or "gate_stack_api.v1",
            "opportunity_row_id": opportunity_context.get("row_id") or "-",
        },
    }


def render_market_workstation_page(view: dict | None) -> None:
    refresh_tick = st_autorefresh(interval=20_000, key="market_workstation_autorefresh")
    render_live_banner(
        "Single Market Workstation",
        "One selected-market context for rules, source/model confidence, evidence, validation, and gate review.",
        live_hint="Auto-refresh 20s",
        live_meta=f"Tick {refresh_tick}",
    )
    legend_left, legend_right = st.columns(2, gap="small")
    with legend_left:
        render_legend_card(
            "Status Legend",
            subtitle="Shared runtime state meanings used across workstation, monitor, and signals.",
            items=default_state_legend_items(),
        )
    with legend_right:
        render_chart_legend_card(
            "Evidence Curve Legend",
            subtitle="Line and marker meanings for evidence, compare, and gate review.",
            items=default_market_evidence_curve_legend_items(),
        )
    if not view:
        render_compact_note(
            "No selected market context is available yet. Select a market from Opportunity Board or Markets.",
            tone="warning",
        )
        return

    render_stat_strip(
        [
            ("Contract", view.get("schema_version")),
            ("Selected Market", view.get("selected_market_id")),
            ("Generated At", view.get("generated_at")),
            ("Top Parameter", (view.get("top_parameter_view") or {}).get("schema_version")),
            ("Opportunity Row", (view.get("upstream_refs") or {}).get("opportunity_row_id")),
        ],
        title="Workstation Context",
    )
    page_context = view.get("page_context") if isinstance(view.get("page_context"), dict) else {}
    if page_context:
        render_kv_section(
            "Page Context",
            [
                ("Source Page", page_context.get("source_page")),
                ("Target Page", page_context.get("target_page")),
                ("Entry Reason", page_context.get("entry_reason")),
                ("Selected Market", page_context.get("selected_market_id")),
            ],
        )
    render_kv_section(
        "Execution Boundary",
        [
            ("Boundary", (view.get("gate_advisory_panel") or {}).get("dry_run_area", {}).get("execution_boundary")),
        ],
        metric_label="Role",
        metric_value="review_only",
    )

    left_col, center_col, right_col = st.columns([0.92, 1.12, 0.96])
    with left_col:
        _render_rule_source_model_panel(view.get("rule_source_model_panel") or {})
    with center_col:
        _render_evidence_timeline(view.get("evidence_timeline") or {})
    with right_col:
        _render_gate_advisory_panel(view.get("gate_advisory_panel") or {})

    bottom_left, bottom_right = st.columns([1.08, 0.92])
    with bottom_left:
        _render_validation_compare_panel(view.get("validation_compare_panel") or {})
    with bottom_right:
        _render_buy_sell_decision_panel(view.get("buy_sell_decision_panel") or {})
        _render_family_anomaly_summary(view.get("family_anomaly_summary") or {})
        _render_opportunity_linkage_panel(view.get("opportunity_linkage_panel") or {})


def _build_rule_source_model_panel(
    *,
    top_parameter_view: dict,
    resolver_rule: dict,
    opportunity_context: dict,
) -> dict:
    source_contract = top_parameter_view.get("source_contract")
    source_contract = source_contract if isinstance(source_contract, dict) else {}
    normalization = top_parameter_view.get("normalization")
    normalization = normalization if isinstance(normalization, dict) else {}
    weather = top_parameter_view.get("weather")
    weather = weather if isinstance(weather, dict) else {}

    return {
        "market_rule": {
            "market_family": top_parameter_view.get("market_family") or resolver_rule.get("market_family"),
            "variable_name": top_parameter_view.get("variable_name") or resolver_rule.get("variable_name"),
            "location_name": top_parameter_view.get("location_name") or resolver_rule.get("location_name"),
            "station_id": weather.get("station_id") or resolver_rule.get("station_id"),
            "target_date": top_parameter_view.get("target_date") or resolver_rule.get("target_date"),
            "band_scheme": resolver_rule.get("band_scheme") or source_contract.get("band_scheme") or "-",
        },
        "source_contract": {
            "required_sources": source_contract.get("required_sources") or resolver_rule.get("required_sources") or [],
            "settlement_source_type": source_contract.get("settlement_source_type") or resolver_rule.get("settlement_source_type") or "-",
            "official_vs_proxy_source": source_contract.get("official_vs_proxy_source") or resolver_rule.get("official_vs_proxy_source") or "-",
            "source_match_grade": source_contract.get("source_match_grade") or resolver_rule.get("source_match_grade") or "-",
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
            "difficulty_reason": opportunity_context.get("difficulty_reason"),
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
        "fair_value": comparison_row.get("fair_value") or comparison_row.get("model_probability") or "-",
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
        "validation_summary_status": validation_summary.get("validation_summary_status") or "-",
        "validation_summary_age": validation_summary.get("validation_summary_age") or "-",
        "validation_summary_family_support_level": validation_summary.get("validation_summary_family_support_level") or "-",
        "validation_summary_promotion_readiness": validation_summary.get("validation_summary_promotion_readiness") or "-",
        "coverage_summary_label_coverage": validation_summary.get("coverage_summary_label_coverage") or "-",
        "coverage_summary_source_coverage": validation_summary.get("coverage_summary_source_coverage") or "-",
        "coverage_summary_normalization_consistency": validation_summary.get("coverage_summary_normalization_consistency") or "-",
        "promotion_support_probability_mode": validation_summary.get("promotion_support_probability_mode") or "-",
        "promotion_support_readiness": validation_summary.get("promotion_support_readiness") or "-",
        "promotion_support_reason": validation_summary.get("promotion_support_reason") or "-",
        "model_validation_compare_best_model": validation_summary.get("model_validation_compare_best_model") or "-",
        "model_validation_compare_best_source_stack": validation_summary.get("model_validation_compare_best_source_stack") or [],
    }


def _build_buy_sell_decision_panel(
    *,
    top_parameter_view: dict,
    validation_summary: dict,
    gate_summary: dict,
    opportunity_context: dict,
) -> dict:
    polymarket = top_parameter_view.get("polymarket")
    polymarket = polymarket if isinstance(polymarket, dict) else {}
    decision = top_parameter_view.get("decision")
    decision = decision if isinstance(decision, dict) else {}
    source_contract = top_parameter_view.get("source_contract")
    source_contract = source_contract if isinstance(source_contract, dict) else {}

    market_probability = _parse_score(polymarket.get("market_implied_probability"))
    fair_value = _parse_score(decision.get("fair_value"))
    edge = _parse_score(decision.get("edge"))
    probability_mode = sanitize_text(decision.get("probability_mode") or "-")
    freshness_status = sanitize_text(source_contract.get("freshness_status") or validation_summary.get("freshness_status") or "-").lower()
    source_precision_score = _parse_score(opportunity_context.get("source_precision_score"))
    validation_coverage = _parse_score(
        validation_summary.get("labeled_ratio")
        or validation_summary.get("label_coverage")
        or validation_summary.get("coverage_ratio")
    )
    can_execute = gate_summary.get("can_execute")
    primary_block_reason = sanitize_text(gate_summary.get("primary_block_reason") or decision.get("primary_block_reason") or "-")

    if any(value is None for value in (market_probability, fair_value, edge)) or probability_mode in {"-", "unknown"}:
        outcome = "refresh_inputs"
        reason = "Market implied probability, fair value, or edge is missing."
    elif freshness_status in {"blocked", "unavailable"}:
        outcome = "refresh_inputs"
        reason = f"Freshness status is {freshness_status}."
    elif validation_coverage is not None and validation_coverage < 0.8:
        outcome = "review_evidence"
        reason = f"Validation coverage {validation_coverage:.2f} is below 0.80."
    elif source_precision_score is not None and source_precision_score < 0.7:
        outcome = "review_evidence"
        reason = f"Source precision score {source_precision_score:.2f} is below 0.70."
    elif edge is not None and abs(edge) <= 0.03:
        outcome = "watch_only"
        reason = f"Edge {edge:.4f} is within no-trade band."
    elif edge is not None and edge >= 0.05:
        outcome = "research_buy_yes"
        reason = "Fair value is above market implied probability."
    elif edge is not None and edge <= -0.05:
        outcome = "research_buy_no"
        reason = "Fair value is below market implied probability."
    else:
        outcome = "watch_only"
        reason = "Edge does not pass directional thresholds."

    return {
        "schema_version": "buy_sell_decision_panel.v1",
        "decision_outcome": outcome,
        "decision_reason": reason,
        "market_implied_probability": market_probability if market_probability is not None else "-",
        "fair_value": fair_value if fair_value is not None else "-",
        "edge": edge if edge is not None else "-",
        "probability_mode": probability_mode,
        "freshness_status": freshness_status,
        "source_precision_score": source_precision_score if source_precision_score is not None else "-",
        "validation_coverage": validation_coverage if validation_coverage is not None else "-",
        "can_execute": can_execute,
        "primary_block_reason": primary_block_reason,
        "execution_boundary": "gate_stack_api.v1_only",
    }


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


def _build_entry_context(opportunity_context: dict) -> dict:
    return {
        "schema_version": "entry_context.v1",
        "source_page": "opportunity_board" if opportunity_context else "-",
        "row_id": opportunity_context.get("row_id") or "-",
        "opportunity_score": opportunity_context.get("opportunity_score"),
        "difficulty_score": opportunity_context.get("difficulty_score"),
        "recommended_action": opportunity_context.get("recommended_action") or "-",
        "best_model": opportunity_context.get("best_model") or "-",
        "best_source_stack": opportunity_context.get("best_source_stack") or [],
    }


def _render_family_anomaly_summary(summary: dict) -> None:
    if not summary:
        render_compact_note("No family anomaly summary available yet.")
        return
    render_kv_section(
        "Advanced Anomaly",
        [
            ("Status", summary.get("status")),
            ("Top Family", summary.get("top_family")),
            ("Top Score", summary.get("top_score")),
            ("Top Bucket", summary.get("top_bucket")),
            ("Signal Summary", summary.get("signal_summary")),
            ("Bucket Counts", summary.get("bucket_counts")),
        ],
        metric_label="Generated At",
        metric_value=summary.get("generated_at"),
    )


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
    polymarket = top_parameter_view.get("polymarket")
    polymarket = polymarket if isinstance(polymarket, dict) else {}
    weather = top_parameter_view.get("weather")
    weather = weather if isinstance(weather, dict) else {}
    forecast = top_parameter_view.get("forecast")
    forecast = forecast if isinstance(forecast, dict) else {}
    source_contract = top_parameter_view.get("source_contract")
    source_contract = source_contract if isinstance(source_contract, dict) else {}

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
    *,
    gate_summary: dict,
    comparison_row: dict,
    latest_alert: dict,
    latest_anomaly: dict,
) -> dict:
    blockers = [str(item) for item in gate_summary.get("blockers") or []]
    gate_status = str(gate_summary.get("gate_status") or "").upper()
    return {
        "gate_summary": {
            "data_gate": gate_summary.get("data_gate") or "-",
            "resolver_gate": gate_summary.get("resolver_gate") or "-",
            "probability_gate": gate_summary.get("probability_gate") or "-",
            "freshness_gate": gate_summary.get("freshness_gate") or "-",
            "authorization_gate": gate_summary.get("authorization_gate") or "-",
            "execution_gate": gate_summary.get("execution_gate") or "-",
            "can_execute": "yes" if gate_status == "READY" else "no",
            "primary_block_reason": blockers[0] if blockers else "none",
        },
        "advisory_summary": {
            "recommended_operator_action": gate_summary.get("recommended_operator_action") or comparison_row.get("action_hint") or "hold_execution_and_review",
            "advisory_reason": blockers[0] if blockers else comparison_row.get("comparison_reason") or "-",
            "latest_alert_summary": latest_alert.get("primary_reason") or latest_alert.get("severity") or "-",
            "latest_anomaly_summary": latest_anomaly.get("primary_reason") or latest_anomaly.get("anomaly_score") or "-",
        },
        "dry_run_area": {
            "simulate_review": "available",
            "create_dry_run_intent": "available_when_gate_context_ready",
            "execution_boundary": "gate_stack_api.v1_only",
        },
    }


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


def _format_signal_summary(summary: object) -> str:
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


def _latest_alert_from_opportunity(row: dict) -> dict:
    severity = row.get("latest_alert_severity")
    if not severity:
        return {}
    return {
        "severity": severity,
        "primary_reason": row.get("opportunity_reason") or row.get("recommended_action"),
    }


def _latest_anomaly_from_opportunity(row: dict) -> dict:
    score = row.get("latest_anomaly_score")
    if score in (None, ""):
        return {}
    return {
        "anomaly_score": score,
        "primary_reason": row.get("difficulty_reason") or row.get("recommended_action"),
    }


def load_latest_market_alert(directory: Path, market_id: str | None) -> dict:
    market_id_text = str(market_id or "").strip()
    if not directory.exists():
        return {}
    candidates = sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        if not market_id_text or str(payload.get("market_id") or "") == market_id_text:
            return payload
    return {}


def load_latest_market_anomaly(directory: Path, market_id: str | None) -> dict:
    market_id_text = str(market_id or "").strip()
    if not directory.exists():
        return {}
    candidates = sorted(directory.glob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except Exception:
            continue
        for line in reversed(lines):
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            if not market_id_text or str(payload.get("market_id") or "") == market_id_text:
                return payload
    return {}


def _render_rule_source_model_panel(panel: dict) -> None:
    source_contract = panel.get("source_contract") or {}
    source_match_grade = str(source_contract.get("source_match_grade") or "").lower()
    resolver_confidence = _parse_score(source_contract.get("resolver_confidence"))
    render_kv_section(
        "Rule / Source",
        [
            ("Family", (panel.get("market_rule") or {}).get("market_family")),
            ("Variable", (panel.get("market_rule") or {}).get("variable_name")),
            ("Location", (panel.get("market_rule") or {}).get("location_name")),
            ("Station", (panel.get("market_rule") or {}).get("station_id")),
            ("Target Date", (panel.get("market_rule") or {}).get("target_date")),
            ("Band Scheme", (panel.get("market_rule") or {}).get("band_scheme")),
            (
                "Source Match",
                with_data_quality(source_contract.get("source_match_grade"), "bad")
                if source_match_grade not in {"exact_station", "aligned"}
                else source_contract.get("source_match_grade"),
            ),
            ("Official / Proxy", (panel.get("source_contract") or {}).get("official_vs_proxy_source")),
            (
                "Resolver Confidence",
                with_data_quality(source_contract.get("resolver_confidence"), "bad")
                if resolver_confidence is not None and resolver_confidence < 0.65
                else source_contract.get("resolver_confidence"),
            ),
        ],
        metric_label="Difficulty",
        metric_value=(panel.get("difficulty") or {}).get("difficulty_label"),
    )
    render_kv_section(
        "Best Model / Policy",
        [
            ("Best Model", (panel.get("best_model") or {}).get("best_model")),
            ("Source Stack", _format_list((panel.get("best_model") or {}).get("best_source_stack"))),
            ("Reason", (panel.get("best_model") or {}).get("best_model_reason")),
            ("Canonical Unit", (panel.get("measurement_policy") or {}).get("canonical_unit")),
            ("Precision Policy", (panel.get("measurement_policy") or {}).get("precision_policy_ref")),
            ("Rounding Policy", (panel.get("measurement_policy") or {}).get("rounding_policy_ref")),
            ("Band Mapping", (panel.get("measurement_policy") or {}).get("band_mapping_policy_ref")),
        ],
        metric_label="Difficulty Score",
        metric_value=(panel.get("difficulty") or {}).get("difficulty_score"),
    )


def _render_evidence_timeline(timeline: dict) -> None:
    tracks = timeline.get("tracks") if isinstance(timeline.get("tracks"), dict) else {}
    market_track = tracks.get("market_probability") or {}
    forecast_track = tracks.get("forecast") or {}
    observation_track = tracks.get("observation") or {}
    event_track = tracks.get("events") or {}
    latest_market = market_track.get("latest") or {}
    latest_forecast = forecast_track.get("latest") or {}
    latest_observation = observation_track.get("latest") or {}
    render_kv_section(
        "Evidence Timeline",
        [
            ("Status", timeline.get("status")),
            ("Input Mode", timeline.get("input_mode")),
            ("Market Points", market_track.get("point_count")),
            ("Latest Probability", latest_market.get("market_probability")),
            ("Latest Compare", latest_market.get("comparison_status")),
            ("Forecast", with_data_quality(_format_value_with_unit(latest_forecast), "bad") if _is_missing_point(latest_forecast) else _format_value_with_unit(latest_forecast)),
            ("Model Band", latest_forecast.get("model_band")),
            ("Observation", with_data_quality(_format_value_with_unit(latest_observation), "bad") if _is_missing_point(latest_observation) else _format_value_with_unit(latest_observation)),
            ("Observation Band", latest_observation.get("observation_band")),
            ("Markers", timeline.get("marker_count")),
        ],
        metric_label="Timeline",
        metric_value=timeline.get("schema_version"),
    )
    markers = event_track.get("markers") or []
    if markers:
        for marker in markers[:4]:
            render_kv_section(
                f"Marker: {sanitize_text(marker.get('type'))}",
                [
                    ("Timestamp", marker.get("timestamp")),
                    ("Status / Severity", marker.get("severity") or marker.get("status") or marker.get("score")),
                    ("Reason", marker.get("reason")),
                ],
            )
    else:
        render_compact_note("No alert / anomaly / gate / ops markers are available for this market yet.")


def _render_gate_advisory_panel(panel: dict) -> None:
    gate = panel.get("gate_summary") or {}
    advisory = panel.get("advisory_summary") or {}
    dry_run = panel.get("dry_run_area") or {}
    render_kv_section(
        "Gate",
        [
            ("Data Gate", gate.get("data_gate")),
            ("Resolver Gate", gate.get("resolver_gate")),
            ("Probability Gate", gate.get("probability_gate")),
            ("Freshness Gate", gate.get("freshness_gate")),
            ("Authorization Gate", gate.get("authorization_gate")),
            ("Execution Gate", gate.get("execution_gate")),
            ("Can Execute", gate.get("can_execute")),
            ("Primary Block", gate.get("primary_block_reason")),
        ],
        metric_label="Boundary",
        metric_value=dry_run.get("execution_boundary"),
    )
    render_kv_section(
        "Advisory / Dry-run",
        [
            ("Operator Action", advisory.get("recommended_operator_action")),
            ("Reason", advisory.get("advisory_reason")),
            ("Latest Alert", advisory.get("latest_alert_summary")),
            ("Latest Anomaly", advisory.get("latest_anomaly_summary")),
            ("Simulate Review", dry_run.get("simulate_review")),
            ("Dry-run Intent", dry_run.get("create_dry_run_intent")),
        ],
    )


def _render_validation_compare_panel(panel: dict) -> None:
    readiness_col, governance_col = st.columns([1, 1])
    with readiness_col:
        render_kv_section(
            "Validation / Compare",
            [
                ("Comparison Status", panel.get("comparison_status")),
                ("Fair Value", panel.get("fair_value")),
                ("Edge", panel.get("edge")),
                ("Promotion State", panel.get("promotion_state")),
                ("Promotion Reason", panel.get("promotion_reason")),
                ("Demotion Reason", panel.get("demotion_reason")),
                ("Primary Blocker", panel.get("primary_blocker")),
            ],
            metric_label="Role",
            metric_value="review_context_only",
        )
    with governance_col:
        render_kv_section(
            "Validation Coverage",
            [
                ("Freshness", panel.get("validation_freshness")),
                ("Freshness Seconds", panel.get("freshness_seconds")),
                ("Coverage Status", panel.get("coverage_status")),
                ("Label Coverage", with_data_quality(panel.get("label_coverage"), "bad") if _is_low_coverage(panel.get("label_coverage")) else panel.get("label_coverage")),
                ("Samples", panel.get("sample_count")),
                ("Labeled Samples", panel.get("labeled_sample_count")),
                ("Calibration", panel.get("calibration_status")),
                ("Deployment", panel.get("deployment_mode")),
                ("Approved For Live", panel.get("approved_for_live")),
                ("Canonical Ratio", panel.get("canonical_ratio")),
                ("Source Policy Coverage", panel.get("source_policy_coverage")),
                ("Normalization Coverage", panel.get("normalization_coverage")),
                ("Family Coverage", panel.get("family_coverage_ratio")),
                ("Family Ready", panel.get("family_ready_ratio")),
                ("Top Watchlist Family", panel.get("top_watchlist_family")),
                ("Top Watchlist Reason", panel.get("top_watchlist_reason")),
                ("Validation Summary", panel.get("validation_summary_status")),
                ("Validation Age", panel.get("validation_summary_age")),
                ("Family Support", panel.get("validation_summary_family_support_level")),
                ("Promotion Readiness", panel.get("validation_summary_promotion_readiness")),
                ("Coverage Summary", panel.get("coverage_summary_label_coverage")),
                ("Promotion Support", panel.get("promotion_support_readiness")),
                ("Best Model Compare", panel.get("model_validation_compare_best_model")),
            ],
            metric_label="Schema",
            metric_value=panel.get("schema_version"),
        )


def _render_buy_sell_decision_panel(panel: dict) -> None:
    if not panel:
        return
    render_kv_section(
        "Buy / Sell Research Direction",
        [
            ("Decision", panel.get("decision_outcome")),
            ("Reason", panel.get("decision_reason")),
            ("Market Probability", panel.get("market_implied_probability")),
            ("Fair Value", panel.get("fair_value")),
            ("Edge", panel.get("edge")),
            ("Probability Mode", panel.get("probability_mode")),
            ("Freshness", panel.get("freshness_status")),
            ("Source Precision", panel.get("source_precision_score")),
            ("Validation Coverage", panel.get("validation_coverage")),
            ("Can Execute", panel.get("can_execute")),
            ("Primary Block", panel.get("primary_block_reason")),
        ],
        metric_label="Boundary",
        metric_value=panel.get("execution_boundary"),
    )


def _render_opportunity_linkage_panel(panel: dict) -> None:
    render_kv_section(
        "Opportunity Entry Context",
        [
            ("Row", panel.get("row_id")),
            ("City", panel.get("city")),
            ("Family", panel.get("market_family")),
            ("Opportunity Score", panel.get("opportunity_score")),
            ("Rank", panel.get("opportunity_rank")),
            ("Difficulty", panel.get("difficulty_label")),
            ("Difficulty Score", panel.get("difficulty_score")),
            ("Action", panel.get("recommended_action")),
            ("Best Model", panel.get("best_model")),
            ("Source Stack", _format_list(panel.get("best_source_stack"))),
            ("Opportunity Reason", panel.get("opportunity_reason")),
            ("Difficulty Reason", panel.get("difficulty_reason")),
            ("Market Refs", _format_list(panel.get("market_refs"))),
            ("Alert Refs", _format_list(panel.get("alert_refs"))),
            ("Anomaly Refs", _format_list(panel.get("anomaly_refs"))),
        ],
        metric_label="Linkage",
        metric_value=panel.get("schema_version"),
    )


def _format_list(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(sanitize_text(item) for item in value) or "-"
    return sanitize_text(value)


def _format_value_with_unit(point: dict) -> str:
    value = point.get("display_value")
    if value in (None, "", "-"):
        value = point.get("canonical_value")
    unit = point.get("canonical_unit")
    text = sanitize_text(value)
    if unit in (None, "", "-"):
        return text
    return f"{text} {sanitize_text(unit)}"


def _parse_score(value: object) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_missing_point(point: dict) -> bool:
    return not any(point.get(key) not in (None, "", "-") for key in ("display_value", "canonical_value"))


def _is_low_coverage(value: object) -> bool:
    score = _parse_score(value)
    return score is None or score < 0.7


def _has_value(point: dict) -> bool:
    return any(value not in (None, "", "-") for value in point.values())


def _first_item(value: object) -> object:
    if isinstance(value, list) and value:
        return value[0]
    return None
