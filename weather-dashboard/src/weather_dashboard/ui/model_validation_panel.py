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
) -> dict:
    report = model_validation_report or {}
    metrics = report.get("validation_metrics") or {}
    resolver_quality = report.get("resolver_quality") or {}
    freshness = validation_freshness_status or {}
    coverage = label_coverage_report or {}
    promotion_state = report.get("promotion_state") or {}
    calibration_curve = ((calibration_report or {}).get("model_probability") or {}).get(
        "reliability_curve"
    ) or []
    edge_deciles = report.get("edge_deciles") or []

    blockers: list[str] = []
    if str(freshness.get("status") or "").lower() not in {"healthy", "ok", "fresh"}:
        blockers.append(f"freshness:{freshness.get('status') or 'unknown'}")
    if str(coverage.get("status") or "").lower() not in {"healthy", "ok"}:
        blockers.append(f"coverage:{coverage.get('status') or 'unknown'}")
    if not report.get("approved_for_live", False):
        blockers.append("not_approved_for_live")
    if report.get("calibration_status") not in {"calibrated", "live_approved"}:
        blockers.append(f"calibration:{report.get('calibration_status') or 'unknown'}")

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
        "promotion_state": promotion_state.get("probability_mode", report.get("probability_mode", "-")),
        "promotion_reason": promotion_state.get("promotion_reason", report.get("promotion_reason", "-")),
        "demotion_reason": promotion_state.get("demotion_reason", report.get("demotion_reason", "-")),
        "backtest_trade_count": (backtest_report or {}).get("trade_count", "-"),
        "backtest_roi": (backtest_report or {}).get("roi", "-"),
        "calibration_curve_points": len(calibration_curve),
        "edge_decile_count": len(edge_deciles),
        "blockers": blockers,
    }


def render_model_validation_panel(
    model_validation_report: dict | None,
    calibration_report: dict | None,
    backtest_report: dict | None,
    validation_freshness_status: dict | None = None,
    label_coverage_report: dict | None = None,
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
            ],
            metric_label="Labeled Ratio",
            metric_value=summary["labeled_ratio"],
        )

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
