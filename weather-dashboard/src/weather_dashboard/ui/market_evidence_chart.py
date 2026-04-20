from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from weather_dashboard.ui.operator_messages import NO_HISTORICAL_EVIDENCE


PRICE_SERIES_COLUMNS = [
    "market_probability",
    "yes_price",
    "model_probability",
    "fair_value",
]
VALUE_SERIES_COLUMNS = [
    "model_value",
    "official_value",
]
PREVIEW_COLUMNS = [
    "timestamp",
    "market_probability",
    "model_probability",
    "fair_value",
    "model_value",
    "official_value",
    "comparison_status",
    "action_hint",
    "outcome",
    "is_labeled",
]


def build_market_evidence_context(
    training_samples_df: pd.DataFrame | None,
    selected_market_id: str | None,
    audit_events: list[dict] | None = None,
) -> dict[str, Any]:
    if not selected_market_id or training_samples_df is None or training_samples_df.empty:
        return {
            "selected_market_id": selected_market_id,
            "sample_count": 0,
            "labeled_rows": 0,
            "latest_market_probability": None,
            "latest_model_probability": None,
            "latest_model_value": None,
            "latest_official_value": None,
            "price_chart_df": pd.DataFrame(),
            "value_chart_df": pd.DataFrame(),
            "preview_df": pd.DataFrame(),
            "approval_markers": [],
        }

    if "market_id" not in training_samples_df.columns:
        return {
            "selected_market_id": selected_market_id,
            "sample_count": 0,
            "labeled_rows": 0,
            "latest_market_probability": None,
            "latest_model_probability": None,
            "latest_model_value": None,
            "latest_official_value": None,
            "price_chart_df": pd.DataFrame(),
            "value_chart_df": pd.DataFrame(),
            "preview_df": pd.DataFrame(),
            "approval_markers": [],
        }

    working = training_samples_df[
        training_samples_df["market_id"].astype(str) == str(selected_market_id)
    ].copy()
    if working.empty:
        return {
            "selected_market_id": selected_market_id,
            "sample_count": 0,
            "labeled_rows": 0,
            "latest_market_probability": None,
            "latest_model_probability": None,
            "latest_model_value": None,
            "latest_official_value": None,
            "price_chart_df": pd.DataFrame(),
            "value_chart_df": pd.DataFrame(),
            "preview_df": pd.DataFrame(),
            "approval_markers": _build_approval_markers(audit_events or [], selected_market_id),
        }

    working["timestamp"] = pd.to_datetime(working.get("timestamp"), errors="coerce", utc=True)
    working = working.dropna(subset=["timestamp"]).sort_values("timestamp")
    if working.empty:
        return {
            "selected_market_id": selected_market_id,
            "sample_count": 0,
            "labeled_rows": 0,
            "latest_market_probability": None,
            "latest_model_probability": None,
            "latest_model_value": None,
            "latest_official_value": None,
            "price_chart_df": pd.DataFrame(),
            "value_chart_df": pd.DataFrame(),
            "preview_df": pd.DataFrame(),
            "approval_markers": _build_approval_markers(audit_events or [], selected_market_id),
        }

    latest = working.iloc[-1]
    labeled_rows = _count_labeled_rows(working)

    return {
        "selected_market_id": selected_market_id,
        "sample_count": int(len(working)),
        "labeled_rows": labeled_rows,
        "latest_market_probability": latest.get("market_probability"),
        "latest_model_probability": latest.get("model_probability"),
        "latest_model_value": latest.get("model_value"),
        "latest_official_value": latest.get("official_value"),
        "price_chart_df": _build_chart_df(working, PRICE_SERIES_COLUMNS),
        "value_chart_df": _build_chart_df(working, VALUE_SERIES_COLUMNS),
        "preview_df": _build_preview_df(working),
        "approval_markers": _build_approval_markers(audit_events or [], selected_market_id),
    }


def render_market_evidence_chart(
    training_samples_df: pd.DataFrame | None,
    selected_market_id: str | None,
    audit_events: list[dict] | None = None,
) -> None:
    st.subheader("Market Evidence Chart")
    st.caption(
        "Single-market evidence timeline combining market pricing, model probability, settlement value, "
        "and manual approval events."
    )

    if not selected_market_id:
        st.info("Select a market to inspect evidence history.")
        return

    context = build_market_evidence_context(training_samples_df, selected_market_id, audit_events)
    if context["sample_count"] == 0:
        st.info(NO_HISTORICAL_EVIDENCE)
        return

    metric_cols = st.columns(5)
    metric_cols[0].metric("Samples", context["sample_count"])
    metric_cols[1].metric("Labeled", context["labeled_rows"])
    metric_cols[2].metric("Market Prob", _format_metric(context["latest_market_probability"]))
    metric_cols[3].metric("Model Prob", _format_metric(context["latest_model_probability"]))
    metric_cols[4].metric("Official Value", _format_metric(context["latest_official_value"]))

    chart_col1, chart_col2 = st.columns([1, 1])
    with chart_col1:
        st.markdown("**Pricing / Probability**")
        if context["price_chart_df"].empty:
            st.info("No probability or pricing series available yet.")
        else:
            st.line_chart(context["price_chart_df"], use_container_width=True)
    with chart_col2:
        st.markdown("**Forecast / Settlement Value**")
        if context["value_chart_df"].empty:
            st.info("No forecast or official settlement value series available yet.")
        else:
            st.line_chart(context["value_chart_df"], use_container_width=True)

    approval_markers = context["approval_markers"]
    if approval_markers:
        st.markdown("**Approval / Advisory Markers**")
        st.dataframe(pd.DataFrame(approval_markers), use_container_width=True, hide_index=True)
    else:
        st.caption("No manual advisory or operator acknowledgement markers recorded for this market yet.")

    with st.expander("Evidence Rows", expanded=False):
        st.dataframe(context["preview_df"], use_container_width=True, hide_index=True)


def _build_chart_df(working: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    present = [column for column in columns if column in working.columns]
    if not present:
        return pd.DataFrame()

    chart_df = working[["timestamp", *present]].copy()
    for column in present:
        chart_df[column] = pd.to_numeric(chart_df[column], errors="coerce")
    chart_df = chart_df.dropna(how="all", subset=present)
    if chart_df.empty:
        return pd.DataFrame()
    return chart_df.set_index("timestamp")


def _build_preview_df(working: pd.DataFrame) -> pd.DataFrame:
    present = [column for column in PREVIEW_COLUMNS if column in working.columns]
    preview = working[present].copy()
    if "timestamp" in preview.columns:
        preview["timestamp"] = preview["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S%z")
    return preview.sort_values("timestamp", ascending=False)


def _count_labeled_rows(working: pd.DataFrame) -> int:
    if "is_labeled" not in working.columns:
        return 0
    return int(working["is_labeled"].apply(_to_bool).sum())


def _build_approval_markers(audit_events: list[dict], selected_market_id: str | None) -> list[dict]:
    markers: list[dict] = []
    for event in audit_events:
        if str(event.get("market_id") or "") != str(selected_market_id or ""):
            continue
        payload = event.get("payload") or {}
        manual_ticket = payload.get("manual_trade_ticket") or {}
        markers.append(
            {
                "created_at": event.get("created_at"),
                "event_type": event.get("event_type"),
                "decision": payload.get("decision") or payload.get("approval_status") or "-",
                "gate_status": payload.get("gate_status") or "-",
                "comparison_status": payload.get("comparison_status") or "-",
                "price": manual_ticket.get("price"),
                "size": manual_ticket.get("size"),
            }
        )
    markers.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return markers


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _format_metric(value: Any) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return f"{value:.4f}"
    return str(value)
