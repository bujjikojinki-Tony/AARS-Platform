from __future__ import annotations

import streamlit as st

from weather_dashboard.ui.compact_panel import (
    render_compact_note,
    render_kv_section,
    render_panel_title,
    sanitize_text,
)


def build_resolver_status_summary(rule: dict | None) -> dict | None:
    if not isinstance(rule, dict):
        return None

    status = str(rule.get("resolver_status") or "-")
    source_match_grade = str(rule.get("source_match_grade") or "-")
    source_policy = str(rule.get("official_vs_proxy_source") or "-")
    note = None

    if status != "matched":
        note = (
            "Resolver has identified the market family and required data source, "
            "but this market is not fully matched to an executable weather rule yet."
        )
    elif source_match_grade in {"family_only", "unmatched"} or source_policy == "fallback":
        note = (
            "Resolver is only partially aligned with the settlement source. "
            "Review the official source contract before trusting the comparison."
        )

    return {
        "status": status,
        "note": note,
        "items": [
            ("Market ID", rule.get("market_id", "-")),
            ("Question", rule.get("market_question", "-")),
            ("Status", status),
            ("Reason", rule.get("resolver_reason", "-")),
            ("Resolver", rule.get("resolver_name", "-")),
            ("Confidence", rule.get("resolver_confidence", "-")),
            ("Family", rule.get("market_family", "-")),
            ("Resolution Scope", rule.get("resolution_scope", "-")),
            ("Pipeline Supported", rule.get("supported_by_current_pipeline", "-")),
            ("Required Source", rule.get("required_data_source", "-")),
            ("Required Inputs", ", ".join(rule.get("required_sources") or []) or "-"),
            ("Band Scheme", rule.get("band_scheme", "-")),
            ("Settlement Type", rule.get("settlement_source_type", "-")),
            ("Source Policy", source_policy),
            ("Source Match", source_match_grade),
            ("Location", rule.get("location_name", "-")),
            ("Station", rule.get("station_name", "-")),
            ("Station ID", rule.get("station_id", "-")),
            ("Target Date", rule.get("target_date", "-")),
            ("Variable", rule.get("variable_name", "-")),
            ("Unit", rule.get("unit", "-")),
            ("Expected Band", rule.get("expected_band", "-")),
        ],
        "source_note": rule.get("source_note"),
        "official_source_url": rule.get("official_source_url"),
    }


def render_resolver_status_panel(
    resolver_report: dict | None,
    selected_market_id: str | None,
) -> None:
    render_panel_title("Resolver Status")

    if not resolver_report:
        st.info("No resolver report found yet. Run weather-rules-research/scripts/run_resolver_once.py.")
        return

    rule = _find_rule(resolver_report, selected_market_id)
    if rule is None:
        render_compact_note(
            "Resolver report was loaded, but no rule entry matched the selected market.",
            tone="warning",
        )
        st.caption(
            f"Report generated at {resolver_report.get('generated_at', '-')}; "
            f"tracked={resolver_report.get('tracked_markets', '-')}, "
            f"matched={resolver_report.get('matched', '-')}, "
            f"unmatched={resolver_report.get('unmatched', '-')}"
        )
        family_counts = resolver_report.get("family_counts") or {}
        if family_counts:
            st.caption(
                "Family coverage: "
                + ", ".join(f"{family}={count}" for family, count in sorted(family_counts.items()))
            )
        return

    status = str(rule.get("resolver_status") or "-")
    summary = build_resolver_status_summary(rule)
    tone = "info" if status == "matched" else "warning"
    if summary and summary["note"]:
        render_compact_note(summary["note"], tone=tone)

    render_kv_section("Resolved Market Rule", summary["items"] if summary else [], metric_label="Resolver Status", metric_value=status)

    if summary and summary["source_note"]:
        st.caption(f"Source note: {sanitize_text(summary['source_note'])}")
    if summary and summary["official_source_url"]:
        st.markdown(
            f"**Official Source URL:** [{sanitize_text(summary['official_source_url'])}]({sanitize_text(summary['official_source_url'])})"
        )

    with st.expander("Raw Resolver Rule", expanded=False):
        st.json(rule)

    family_counts = resolver_report.get("family_counts") or {}
    matched_family_counts = resolver_report.get("matched_family_counts") or {}
    unmatched_family_counts = resolver_report.get("unmatched_family_counts") or {}
    source_match_grade_counts = resolver_report.get("source_match_grade_counts") or {}
    source_policy_counts = resolver_report.get("source_policy_counts") or {}
    if family_counts:
        with st.expander("Resolver Coverage By Family", expanded=False):
            st.json(
                {
                    "tracked_markets": resolver_report.get("tracked_markets"),
                    "matched": resolver_report.get("matched"),
                    "unmatched": resolver_report.get("unmatched"),
                    "family_counts": family_counts,
                    "matched_family_counts": matched_family_counts,
                    "unmatched_family_counts": unmatched_family_counts,
                    "source_match_grade_counts": source_match_grade_counts,
                    "source_policy_counts": source_policy_counts,
                }
            )


def _find_rule(resolver_report: dict, market_id: str | None) -> dict | None:
    rules = resolver_report.get("rules") or []
    if not isinstance(rules, list):
        return None
    if market_id:
        for rule in rules:
            if isinstance(rule, dict) and str(rule.get("market_id") or "") == str(market_id):
                return rule
    return None
