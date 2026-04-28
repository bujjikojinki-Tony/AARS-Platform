from __future__ import annotations

import streamlit as st

from weather_dashboard.ui.compact_panel import (
    render_compact_note,
    render_kv_section,
    render_panel_title,
    sanitize_text,
)


def build_validation_summary(
    model_validation_report: dict | None,
    calibration_report: dict | None,
    backtest_report: dict | None,
    validation_freshness_status: dict | None = None,
    label_coverage_report: dict | None = None,
    latest_family_scan_report: dict | None = None,
    validation_summary: dict | None = None,
    coverage_summary: dict | None = None,
    promotion_support: dict | None = None,
    model_validation_compare: dict | None = None,
) -> dict:
    report = model_validation_report or {}
    metrics = report.get("validation_metrics") or {}
    resolver_quality = report.get("resolver_quality") or {}
    governance = report.get("governance_summary") or {}
    rollout = report.get("family_rollout_summary") or {}
    rollout_trend = report.get("family_rollout_trend_summary") or {}
    rollout_watchlist = report.get("family_rollout_watchlist") or {}
    assimilation = report.get("validation_assimilation_summary") or {}
    freshness = validation_freshness_status or {}
    coverage = label_coverage_report or {}
    phase30_validation = validation_summary or {}
    phase30_coverage = coverage_summary or {}
    phase30_promotion = promotion_support or {}
    phase30_compare = model_validation_compare or {}
    family_scan = latest_family_scan_report or {}
    family_scan_summary = _family_scan_summary(family_scan)
    promotion_state = report.get("promotion_state") or {}
    phase30_validation_status = str(phase30_validation.get("validation_status") or "").strip()
    calibration_curve = ((calibration_report or {}).get("model_probability") or {}).get(
        "reliability_curve"
    ) or []
    edge_deciles = report.get("edge_deciles") or []

    blockers: list[str] = []
    if str(freshness.get("status") or "").lower() not in {"healthy", "ok", "fresh"}:
        blockers.append(f"freshness:{freshness.get('status') or 'unknown'}")
    if str(coverage.get("status") or "").lower() not in {"healthy", "ok"}:
        blockers.append(f"coverage:{coverage.get('status') or 'unknown'}")
    if phase30_validation_status and phase30_validation_status not in {"strong", "moderate"}:
        blockers.append(f"phase30_validation:{phase30_validation_status}")
    if not report.get("approved_for_live", False):
        blockers.append("not_approved_for_live")
    if report.get("calibration_status") not in {"calibrated", "live_approved"}:
        blockers.append(f"calibration:{report.get('calibration_status') or 'unknown'}")
    if str(phase30_validation.get("promotion_readiness") or "").strip() == "not_ready":
        blockers.append("phase30_promotion:not_ready")

    return {
        "approved_for_live": bool(report.get("approved_for_live", False)),
        "deployment_mode": report.get("deployment_mode", "-"),
        "calibration_status": report.get("calibration_status", "-"),
        "sample_count": report.get("sample_count", "-"),
        "labeled_sample_count": report.get("labeled_sample_count", "-"),
        "freshness_status": freshness.get("status", "-"),
        "freshness_seconds": freshness.get("freshness_seconds", "-"),
        "coverage_status": coverage.get("status", "-"),
        "labeled_ratio": coverage.get("labeled_ratio", "-"),
        "minimum_labeled_rows": coverage.get("minimum_labeled_rows", "-"),
        "brier_score": metrics.get("brier_score", "-"),
        "calibration_error": metrics.get("calibration_error", "-"),
        "roi_backtest": metrics.get("roi_backtest", "-"),
        "hit_rate": metrics.get("hit_rate", "-"),
        "resolver_match_rate": resolver_quality.get("resolver_match_rate", "-"),
        "unmatched_count": resolver_quality.get("unmatched_count", "-"),
        "canonical_ratio": governance.get("canonical_ratio", "-"),
        "source_policy_coverage": governance.get("source_policy_coverage", "-"),
        "normalization_coverage": governance.get("normalization_coverage", "-"),
        "source_policy_refs": governance.get("source_policy_ref_counts", {}),
        "family_coverage_ratio": rollout.get("coverage_ratio", "-"),
        "family_ready_ratio": rollout.get("ready_ratio", "-"),
        "family_count": rollout.get("family_count", "-"),
        "ready_family_count": rollout.get("ready_family_count", "-"),
        "top_family": rollout.get("top_family", "-"),
        "top_drift_family": rollout.get("top_drift_family", "-"),
        "top_drift_value": rollout.get("top_drift_value", "-"),
        "drift_bucket_counts": rollout.get("drift_bucket_counts", {}),
        "family_rollout_summary": rollout,
        "family_rollout_trend_summary": rollout_trend,
        "family_rollout_watchlist": rollout_watchlist,
        "assimilation_status": assimilation.get("assimilation_status", "-"),
        "assimilation_summary": assimilation,
        "feature_store_ready": assimilation.get("feature_store_ready", "-"),
        "label_store_ready": assimilation.get("label_store_ready", "-"),
        "backtest_ready": assimilation.get("backtest_ready", "-"),
        "assimilation_primary_blocker": assimilation.get("primary_blocker", "-"),
        "assimilation_top_watchlist_family": assimilation.get("top_watchlist_family", "-"),
        "assimilation_top_watchlist_attention_level": assimilation.get("top_watchlist_attention_level", "-"),
        "assimilation_top_watchlist_reason": assimilation.get("top_watchlist_reason", "-"),
        "promotion_state": promotion_state.get("probability_mode", report.get("probability_mode", "-")),
        "promotion_reason": promotion_state.get("promotion_reason", report.get("promotion_reason", "-")),
        "demotion_reason": promotion_state.get("demotion_reason", report.get("demotion_reason", "-")),
        "backtest_trade_count": (backtest_report or {}).get("trade_count", "-"),
        "backtest_roi": (backtest_report or {}).get("roi", "-"),
        "trend_window_count": len(rollout_trend.get("trend_windows") or []),
        "coverage_movement": rollout_trend.get("coverage_movement", "-"),
        "ready_movement": rollout_trend.get("ready_movement", "-"),
        "drift_movement": rollout_trend.get("drift_movement", "-"),
        "watchlist_count": rollout_watchlist.get("watchlist_count", "-"),
        "stalled_family_count": rollout_watchlist.get("stalled_family_count", "-"),
        "drift_spike_family_count": rollout_watchlist.get("drift_spike_family_count", "-"),
        "expansion_backlog_count": rollout_watchlist.get("expansion_backlog_count", "-"),
        "top_watchlist_family": rollout_watchlist.get("top_watchlist_family", "-"),
        "top_watchlist_attention_level": rollout_watchlist.get("top_watchlist_attention_level", "-"),
        "top_watchlist_reason": rollout_watchlist.get("top_watchlist_reason", "-"),
        "top_watchlist_sample_count": rollout_watchlist.get("top_watchlist_sample_count", "-"),
        "calibration_curve_points": len(calibration_curve),
        "edge_decile_count": len(edge_deciles),
        "family_scan_status": family_scan_summary.get("family_scan_status", "-"),
        "family_scan_top_family": family_scan_summary.get("top_family", "-"),
        "family_scan_top_score": family_scan_summary.get("top_score", "-"),
        "family_scan_top_bucket": family_scan_summary.get("top_bucket", "-"),
        "family_scan_signal_summary": family_scan_summary.get("signal_summary", "-"),
        "family_scan_bucket_counts": family_scan_summary.get("bucket_counts", {}),
        "family_scan_generated_at": family_scan_summary.get("generated_at", "-"),
        "family_scan_primary_reason": family_scan_summary.get("primary_reason", "-"),
        "family_scan_report": family_scan,
        "validation_summary_v1": phase30_validation,
        "coverage_summary_v1": phase30_coverage,
        "promotion_support_v1": phase30_promotion,
        "model_validation_compare_v1": phase30_compare,
        "validation_summary_status": phase30_validation.get("validation_status", "-"),
        "validation_summary_age": phase30_validation.get("validation_age", "-"),
        "validation_summary_family_support_level": phase30_validation.get("family_support_level", "-"),
        "validation_summary_promotion_readiness": phase30_validation.get("promotion_readiness", "-"),
        "validation_summary_reasons": phase30_validation.get("reasons", []),
        "coverage_summary_label_coverage": phase30_coverage.get("label_coverage", coverage.get("labeled_ratio", "-")),
        "coverage_summary_source_coverage": phase30_coverage.get("source_coverage", "-"),
        "coverage_summary_normalization_consistency": phase30_coverage.get("normalization_consistency", "-"),
        "promotion_support_probability_mode": phase30_promotion.get("current_probability_mode", "-"),
        "promotion_support_readiness": phase30_promotion.get("promotion_readiness", "-"),
        "promotion_support_reason": phase30_promotion.get("promotion_reason", "-"),
        "promotion_support_demotion_reason": phase30_promotion.get("demotion_reason", "-"),
        "model_validation_compare_best_model": phase30_compare.get("selected_best_model", "-"),
        "model_validation_compare_best_source_stack": phase30_compare.get("selected_best_source_stack", []),
        "blockers": blockers,
    }


def _family_scan_summary(report: dict) -> dict:
    if not isinstance(report, dict) or not report:
        return {
            "family_scan_status": "-",
            "top_family": "-",
            "top_score": "-",
            "top_bucket": "-",
            "signal_summary": "-",
            "bucket_counts": {},
            "generated_at": "-",
            "primary_reason": "-",
        }

    if str(report.get("schema_version") or "").strip() == "family_anomaly_summary.v1":
        top_score = report.get("high_intervention_like_count")
        return {
            "family_scan_status": str(report.get("schema_version") or "-"),
            "top_family": str(report.get("market_family") or "-"),
            "top_score": top_score if top_score is not None else "-",
            "top_bucket": _family_scan_bucket(top_score),
            "signal_summary": str(report.get("family_risk_summary") or report.get("signal_summary") or "-"),
            "bucket_counts": report.get("anomaly_bucket_counts") or {},
            "generated_at": report.get("generated_at") or "-",
            "primary_reason": str(report.get("family_risk_summary") or report.get("primary_reason") or "-"),
        }

    family_summaries = [
        item for item in (report.get("family_summaries") or []) if isinstance(item, dict)
    ]
    ranked = sorted(
        family_summaries,
        key=lambda item: float(item.get("max_intervention_like_score") or 0.0),
        reverse=True,
    )
    top_family = ranked[0] if ranked else {}
    return {
        "family_scan_status": str(report.get("input_mode") or report.get("schema_version") or "-"),
        "top_family": str(top_family.get("market_family") or "-"),
        "top_score": top_family.get("max_intervention_like_score", "-"),
        "top_bucket": _family_scan_bucket(top_family.get("max_intervention_like_score")),
        "signal_summary": _family_scan_signal_summary(report.get("signal_summary")),
        "bucket_counts": report.get("anomaly_bucket_counts") or {},
        "generated_at": report.get("generated_at") or "-",
        "primary_reason": str(top_family.get("signal_summary") or report.get("signal_summary") or "-"),
    }


def _family_scan_bucket(score: object) -> str:
    try:
        value = float(score or 0.0)
    except (TypeError, ValueError):
        value = 0.0
    if value >= 0.8:
        return "high"
    if value >= 0.5:
        return "medium"
    return "low"


def _family_scan_signal_summary(summary: object) -> str:
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


def render_model_validation_panel(
    model_validation_report: dict | None,
    calibration_report: dict | None,
    backtest_report: dict | None,
    validation_freshness_status: dict | None = None,
    label_coverage_report: dict | None = None,
    latest_family_scan_report: dict | None = None,
    validation_summary: dict | None = None,
    coverage_summary: dict | None = None,
    promotion_support: dict | None = None,
    model_validation_compare: dict | None = None,
) -> None:
    render_panel_title(
        "Model Validation",
        "Promotion readiness first; calibration tables and raw reports stay behind diagnostics.",
    )

    if not model_validation_report:
        st.info(
            "No model validation report found yet. "
            "Run weather-comparison-engine/scripts/run_model_validation.py."
        )
        return

    summary = build_validation_summary(
        model_validation_report,
        calibration_report,
        backtest_report,
        validation_freshness_status,
        label_coverage_report,
        latest_family_scan_report,
        validation_summary,
        coverage_summary,
        promotion_support,
        model_validation_compare,
    )
    render_compact_note(
        model_validation_report.get(
            "note",
            "Validation reports are for offline analysis only and do not authorize BOT execution.",
        ),
        tone="warning",
    )

    _render_validation_cards(summary)

    quality_col1, quality_col2 = st.columns([1, 1])
    with quality_col1:
        render_kv_section(
            "Promotion Readiness",
            [
                ("Promotion State", summary["promotion_state"]),
                ("Promotion Reason", summary["promotion_reason"]),
                ("Demotion Reason", summary["demotion_reason"]),
                ("Approved For Live", summary["approved_for_live"]),
                ("Deployment Mode", summary["deployment_mode"]),
                ("Calibration Status", summary["calibration_status"]),
                ("Primary Blocker", summary["blockers"][0] if summary["blockers"] else "none"),
            ],
            metric_label="Can Promote",
            metric_value="yes" if summary["promotion_state"] == "live_approved" and not summary["blockers"] else "no",
        )
    with quality_col2:
        render_kv_section(
            "Validation Inputs",
            [
                ("Samples", summary["sample_count"]),
                ("Labeled", summary["labeled_sample_count"]),
                ("Coverage", summary["coverage_status"]),
                ("Freshness", summary["freshness_status"]),
                ("Canonical Ratio", summary["canonical_ratio"]),
                ("Source Coverage", summary["source_policy_coverage"]),
                ("Normalization Coverage", summary["normalization_coverage"]),
                ("Phase30 Validation", summary["validation_summary_status"]),
                ("Phase30 Promotion", summary["validation_summary_promotion_readiness"]),
            ],
            metric_label="Labeled Ratio",
            metric_value=summary["labeled_ratio"],
        )

    assimilation_col1, assimilation_col2 = st.columns([1, 1])
    with assimilation_col1:
        render_kv_section(
            "Validation Assimilation",
            [
                ("Assimilation Status", summary["assimilation_status"]),
                ("Feature Store Ready", summary["feature_store_ready"]),
                ("Label Store Ready", summary["label_store_ready"]),
                ("Backtest Ready", summary["backtest_ready"]),
                ("Primary Blocker", summary["assimilation_primary_blocker"]),
                ("Top Family", summary["assimilation_top_watchlist_family"]),
                ("Validation Age", summary["validation_summary_age"]),
                ("Family Support", summary["validation_summary_family_support_level"]),
                ("Model Compare Best", summary["model_validation_compare_best_model"]),
            ],
            metric_label="Assimilation",
            metric_value=summary["assimilation_status"],
        )
    with assimilation_col2:
        render_kv_section(
            "Assimilation Watchlist",
            [
                ("Top Attention", summary["assimilation_top_watchlist_attention_level"]),
                ("Top Reason", summary["assimilation_top_watchlist_reason"]),
                ("Family Count", summary.get("family_count", "-")),
                ("Ready Families", summary.get("ready_family_count", "-")),
                ("Coverage Ratio", summary.get("family_coverage_ratio", "-")),
                ("Ready Ratio", summary.get("family_ready_ratio", "-")),
                ("Coverage Summary", summary["coverage_summary_label_coverage"]),
                ("Promotion Support", summary["promotion_support_readiness"]),
            ],
            metric_label="Watchlist Count",
            metric_value=summary.get("watchlist_count", "-"),
        )

    family_scan_report = summary.get("family_scan_report") or {}
    family_scan_rows = family_scan_report.get("family_summaries") or []
    family_scan_summary_col1, family_scan_summary_col2 = st.columns([1, 1])
    with family_scan_summary_col1:
        render_kv_section(
            "Family Anomaly Scan",
            [
                ("Scan Status", summary["family_scan_status"]),
                ("Top Family", summary["family_scan_top_family"]),
                ("Top Score", summary["family_scan_top_score"]),
                ("Top Bucket", summary["family_scan_top_bucket"]),
                ("Signal Summary", summary["family_scan_signal_summary"]),
                ("Bucket Counts", summary["family_scan_bucket_counts"]),
            ],
            metric_label="Generated At",
            metric_value=summary["family_scan_generated_at"],
        )
    with family_scan_summary_col2:
        if family_scan_rows:
            st.markdown("**Family Scan Breakdown**")
            rows = [
                {
                    "family": item.get("market_family"),
                    "market_count": item.get("market_count"),
                    "avg_intervention_like": item.get("average_intervention_like_score"),
                    "max_intervention_like": item.get("max_intervention_like_score"),
                    "outlier_count": item.get("outlier_count"),
                    "signal_summary": item.get("signal_summary"),
                }
                for item in family_scan_rows
                if isinstance(item, dict)
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No family anomaly scan available yet.")

    rollout = summary["family_rollout_summary"] or {}
    rollout_trend = summary["family_rollout_trend_summary"] or {}
    rollout_watchlist = summary["family_rollout_watchlist"] or {}
    rollout_col1, rollout_col2 = st.columns([1, 1])
    with rollout_col1:
        render_kv_section(
            "Family Rollout",
            [
                ("Families", summary["family_count"]),
                ("Ready Families", summary["ready_family_count"]),
                ("Coverage Ratio", summary["family_coverage_ratio"]),
                ("Ready Ratio", summary["family_ready_ratio"]),
                ("Top Family", summary["top_family"]),
                ("Top Drift Family", summary["top_drift_family"]),
                ("Top Drift", summary["top_drift_value"]),
            ],
            metric_label="Drift Buckets",
            metric_value=summary["drift_bucket_counts"],
        )
    with rollout_col2:
        if rollout.get("family_summaries"):
            st.markdown("**Family Rollout Breakdown**")
            rows = [
                {
                    "family": item.get("market_family"),
                    "sample_count": item.get("sample_count"),
                    "coverage_status": item.get("coverage_status"),
                    "calibration_error": item.get("calibration_error"),
                    "drift_from_global": item.get("drift_from_global"),
                    "drift_bucket": item.get("drift_bucket"),
                }
                for item in rollout.get("family_summaries") or []
                if isinstance(item, dict)
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No family rollout breakdown available yet.")

    trend_col1, trend_col2 = st.columns([1, 1])
    with trend_col1:
        render_kv_section(
            "Family Rollout Trend",
            [
                ("Trend Windows", summary["trend_window_count"]),
                ("Coverage Movement", summary["coverage_movement"]),
                ("Ready Movement", summary["ready_movement"]),
                ("Drift Movement", summary["drift_movement"]),
            ],
            metric_label="Trend Count",
            metric_value=summary["trend_window_count"],
        )
    with trend_col2:
        trend_windows = rollout_trend.get("trend_windows") or []
        if trend_windows:
            st.markdown("**Trend Windows**")
            rows = [
                {
                    "window": item.get("window_label"),
                    "sample_count": item.get("sample_count"),
                    "coverage_ratio": item.get("coverage_ratio"),
                    "ready_ratio": item.get("ready_ratio"),
                    "top_family": item.get("top_family"),
                    "top_drift_family": item.get("top_drift_family"),
                    "top_drift_value": item.get("top_drift_value"),
                }
                for item in trend_windows
                if isinstance(item, dict)
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No family rollout trend available yet.")

    watchlist_col1, watchlist_col2 = st.columns([1, 1])
    with watchlist_col1:
        render_kv_section(
            "Family Rollout Watchlist",
            [
                ("Watchlist Count", summary["watchlist_count"]),
                ("Stalled Families", summary["stalled_family_count"]),
                ("Drift Spike Families", summary["drift_spike_family_count"]),
                ("Expansion Backlog", summary["expansion_backlog_count"]),
                ("Top Watchlist Family", summary["top_watchlist_family"]),
                ("Top Attention", summary["top_watchlist_attention_level"]),
                ("Top Reason", summary["top_watchlist_reason"]),
            ],
            metric_label="Watchlist Count",
            metric_value=summary["watchlist_count"],
        )
    with watchlist_col2:
        watchlist_rows = rollout_watchlist.get("watchlist") or []
        if watchlist_rows:
            st.markdown("**Watchlist Families**")
            rows = [
                {
                    "rank": item.get("watchlist_rank"),
                    "family": item.get("market_family"),
                    "attention": item.get("attention_level"),
                    "coverage": item.get("coverage_status"),
                    "drift_bucket": item.get("drift_bucket"),
                    "sample_count": item.get("sample_count"),
                    "suggested_action": item.get("suggested_action"),
                }
                for item in watchlist_rows
                if isinstance(item, dict)
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No family rollout watchlist available yet.")

    if not st.checkbox(
        "Show validation diagnostics: calibration, family breakdown, backtest, resolver and raw reports",
        value=False,
        key="validation_show_diagnostics",
    ):
        return

    _render_validation_diagnostics(
        model_validation_report=model_validation_report,
        calibration_report=calibration_report,
        backtest_report=backtest_report,
        validation_freshness_status=validation_freshness_status,
        label_coverage_report=label_coverage_report,
    )


def _render_validation_diagnostics(
    *,
    model_validation_report: dict,
    calibration_report: dict | None,
    backtest_report: dict | None,
    validation_freshness_status: dict | None,
    label_coverage_report: dict | None,
) -> None:
    metrics = model_validation_report.get("validation_metrics") or {}
    col1, col2 = st.columns([1, 1])
    with col1:
        render_kv_section(
            "Validation Summary",
            [
                ("Model ID", model_validation_report.get("model_id", "-")),
                ("Model Type", model_validation_report.get("model_type", "-")),
                ("Calibration Status", model_validation_report.get("calibration_status", "-")),
                ("Approved For Live", model_validation_report.get("approved_for_live", "-")),
                ("Data Range", model_validation_report.get("training_data_range", "-")),
                ("Log Loss", metrics.get("log_loss", "-")),
                ("Calibration Error", metrics.get("calibration_error", "-")),
                ("Hit Rate", metrics.get("hit_rate", "-")),
                ("Max Drawdown", metrics.get("max_drawdown", "-")),
            ],
            metric_label="Market Baseline Brier",
            metric_value=metrics.get("market_baseline_brier_score", "-"),
        )
    with col2:
        family_validation = model_validation_report.get("family_validation") or {}
        if family_validation:
            st.markdown("**Family Validation**")
            rows = [{"family": family, **payload} for family, payload in family_validation.items()]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No family validation breakdown available yet.")

    lower1, lower2 = st.columns([1, 1])
    with lower1:
        model_curve = ((calibration_report or {}).get("model_probability") or {}).get(
            "reliability_curve"
        ) or []
        if model_curve:
            st.markdown("**Calibration Curve**")
            st.dataframe(model_curve, use_container_width=True, hide_index=True)
        else:
            st.info("No calibration curve available yet.")
    with lower2:
        if backtest_report:
            render_kv_section(
                "Backtest Summary",
                [
                    ("Trade Count", backtest_report.get("trade_count", "-")),
                    ("Turnover", backtest_report.get("turnover", "-")),
                    ("Total PnL", backtest_report.get("total_pnl", "-")),
                    ("ROI", backtest_report.get("roi", "-")),
                    ("Hit Rate", backtest_report.get("hit_rate", "-")),
                    ("Avg Edge Captured", backtest_report.get("avg_edge_captured", "-")),
                    ("Max Drawdown", backtest_report.get("max_drawdown", "-")),
                    ("Edge Threshold", backtest_report.get("edge_threshold", "-")),
                ],
                metric_label="Trades",
                metric_value=backtest_report.get("trade_count", "-"),
            )
            family_breakdown = backtest_report.get("family_breakdown") or {}
            if family_breakdown:
                st.markdown("**Backtest Family Breakdown**")
                rows = [{"family": family, **payload} for family, payload in family_breakdown.items()]
                st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No backtest report available yet.")

    extra1, extra2 = st.columns([1, 1])
    with extra1:
        resolver_quality = model_validation_report.get("resolver_quality") or {}
        if resolver_quality:
            render_kv_section(
                "Resolver Quality",
                [
                    ("Matched Count", resolver_quality.get("matched_count", "-")),
                    ("Unmatched Count", resolver_quality.get("unmatched_count", "-")),
                    ("Resolver Match Rate", resolver_quality.get("resolver_match_rate", "-")),
                    ("Unmatched Market Rate", resolver_quality.get("unmatched_market_rate", "-")),
                ],
                metric_label="Samples",
                metric_value=resolver_quality.get("sample_count", "-"),
            )
            status_counts = resolver_quality.get("resolver_status_counts") or {}
            if status_counts:
                st.markdown("**Resolver Status Counts**")
                st.dataframe(
                    [{"status": status, "count": count} for status, count in status_counts.items()],
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.info("No resolver quality summary available yet.")
    with extra2:
        edge_deciles = model_validation_report.get("edge_deciles") or []
        if edge_deciles:
            st.markdown("**Edge Deciles**")
            st.dataframe(edge_deciles, use_container_width=True, hide_index=True)
        else:
            st.info("No edge decile breakdown available yet.")

    raw_tab1, raw_tab2, raw_tab3, raw_tab4 = st.tabs(
        ["Raw Model", "Raw Calibration", "Raw Backtest", "Raw Quality"]
    )
    with raw_tab1:
        st.json(model_validation_report)
    with raw_tab2:
        st.json(calibration_report or {})
    with raw_tab3:
        st.json(backtest_report or {})
    with raw_tab4:
        st.json(
            {
                "validation_freshness_status": validation_freshness_status or {},
                "label_coverage_report": label_coverage_report or {},
            }
        )


def _render_validation_cards(summary: dict) -> None:
    blockers = summary["blockers"]
    card_payloads = [
        {
            "title": "Promotion",
            "value": "LIVE OK" if summary["approved_for_live"] and not blockers else "BLOCKED",
            "rows": [
                ("Mode", summary["deployment_mode"]),
                ("Calibration", summary["calibration_status"]),
                ("Blocker", blockers[0] if blockers else "none"),
            ],
        },
        {
            "title": "Coverage",
            "value": str(summary["coverage_status"]),
            "rows": [
                ("Labeled", str(summary["labeled_sample_count"])),
                ("Ratio", str(summary["labeled_ratio"])),
                ("Min Rows", str(summary["minimum_labeled_rows"])),
            ],
        },
        {
            "title": "Freshness",
            "value": str(summary["freshness_status"]),
            "rows": [
                ("Age", str(summary["freshness_seconds"])),
                ("Samples", str(summary["sample_count"])),
                ("Curve Pts", str(summary["calibration_curve_points"])),
            ],
        },
        {
            "title": "Model Quality",
            "value": f"Brier {summary['brier_score']}",
            "rows": [
                ("Cal Error", str(summary["calibration_error"])),
                ("Hit Rate", str(summary["hit_rate"])),
                ("ROI", str(summary["roi_backtest"])),
            ],
        },
        {
            "title": "Resolver",
            "value": str(summary["resolver_match_rate"]),
            "rows": [
                ("Unmatched", str(summary["unmatched_count"])),
                ("Trades", str(summary["backtest_trade_count"])),
                ("BT ROI", str(summary["backtest_roi"])),
            ],
        },
    ]
    cols = st.columns(len(card_payloads))
    for col, card in zip(cols, card_payloads):
        with col:
            with st.container(border=True):
                st.caption(sanitize_text(str(card["title"]).upper()))
                st.metric("Status", sanitize_text(card["value"]))
                for label, value in card["rows"]:
                    st.markdown(f"**{sanitize_text(label)}:** `{sanitize_text(value)}`")


def _validation_tone(value: object) -> str:
    text = str(value or "").lower()
    if text in {"healthy", "ok", "fresh", "pass"}:
        return "ok"
    if text in {"blocked", "stale", "fail", "failed"}:
        return "block"
    if text in {"warning", "degraded", "warm"}:
        return "warn"
    return "neutral"
