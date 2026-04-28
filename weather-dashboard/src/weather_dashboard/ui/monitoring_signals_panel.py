from __future__ import annotations

import json
from collections.abc import Callable
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from textwrap import dedent

import pandas as pd
try:
    import plotly.graph_objects as go
except Exception:  # pragma: no cover - exercised in lean local test environments
    go = None

from weather_dashboard.settings import (
    EVIDENCE_SCAN_SNAPSHOT_JSON,
    FAMILY_SCAN_REPORTS_DIR,
    GATE_STACK_API_JSON,
    MARKET_ALERT_EVENTS_DIR,
    MARKET_ANOMALY_EVENTS_DIR,
    MARKET_UNIVERSE_SNAPSHOT_JSON,
    SCAN_QUEUE_STATUS_JSON,
    SCANNER_STATUS_JSON,
    SOURCE_POLICY_STATUS_JSON,
    UNIFIED_STATUS_JSON,
)
from weather_dashboard.ui.compact_panel import (
    default_signal_trend_legend_items,
    default_state_legend_items,
    render_chart_legend_card,
    render_compact_note,
    render_legend_card,
)


def render_monitoring_signals_panel(
    *,
    on_open_market: Callable[[str, dict], None] | None = None,
    on_send_to_command: Callable[[str, dict], None] | None = None,
) -> None:
    import streamlit as st
    from streamlit_autorefresh import st_autorefresh

    refresh_tick = st_autorefresh(interval=20_000, key="monitoring_signals_autorefresh")
    _render_theme()

    scanner_status = _load_json_file(SCANNER_STATUS_JSON)
    queue_status = _load_json_file(SCAN_QUEUE_STATUS_JSON)
    source_policy = _load_json_file(SOURCE_POLICY_STATUS_JSON)
    gate_stack = _load_json_file(GATE_STACK_API_JSON)
    unified_status = _load_json_file(UNIFIED_STATUS_JSON)
    market_universe = _load_json_file(MARKET_UNIVERSE_SNAPSHOT_JSON)
    evidence_scan = _load_json_file(EVIDENCE_SCAN_SNAPSHOT_JSON)
    family_report = _load_latest_json(FAMILY_SCAN_REPORTS_DIR)

    signal_rows = _collect_signal_rows(
        scanner_status=scanner_status,
        queue_status=queue_status,
        source_policy=source_policy,
        gate_stack=gate_stack,
        unified_status=unified_status,
        family_report=family_report,
    )

    if not signal_rows:
        render_compact_note("No monitoring signals found yet.", tone="warning")
        return

    st.html(
        f"""
        <div class="signals-header">
          <div class="signals-header__title-wrap">
            <div class="signals-header__title">MONITORING SIGNALS</div>
            <div class="signals-header__subtitle">Real-time Alerts, Approval Signals, and Pipeline Events</div>
            <div class="signals-live-pill">LIVE</div>
          </div>
          <div class="signals-header__meta">Auto Refresh <strong>20s</strong> · Tick {refresh_tick}</div>
        </div>
        """
    )

    signal_section = st.selectbox(
        "Signal section",
        ["Active Signals", "Alert Queue", "Anomaly Feed", "System Signals", "Signal History"],
        key="signals_active_section",
    )
    section_rows = _apply_signal_section(signal_rows, signal_section)

    severity_options = ["All"] + _sorted_unique([row["severity_label"] for row in section_rows])
    type_options = ["All"] + _sorted_unique([row["type_label"] for row in section_rows])
    market_options = ["All"] + _sorted_unique([row["market_label"] for row in section_rows])
    family_options = ["All"] + _sorted_unique([row["family_label"] for row in section_rows if row["family_label"] != "-"])

    legend_left, legend_right = st.columns(2, gap="small")
    with legend_left:
        render_legend_card(
            "Signal Legend",
            subtitle="Shared meaning across alert, anomaly, system, and recovery states.",
            items=default_state_legend_items(),
        )
    with legend_right:
        render_chart_legend_card(
            "Trend Legend",
            subtitle="Line and bucket meaning used by the live trend and severity charts.",
            items=default_signal_trend_legend_items(),
        )

    filter_cols = st.columns([0.15, 0.15, 0.22, 0.18, 0.30])
    with filter_cols[0]:
        severity_filter = st.selectbox("Severity", severity_options, key="signals_filter_severity")
    with filter_cols[1]:
        type_filter = st.selectbox("Type", type_options, key="signals_filter_type")
    with filter_cols[2]:
        market_filter = st.selectbox("Market", market_options, key="signals_filter_market")
    with filter_cols[3]:
        family_filter = st.selectbox("Family", family_options, key="signals_filter_family")
    with filter_cols[4]:
        search_text = st.text_input(
            "Search",
            value=st.session_state.get("signals_filter_search", ""),
            key="signals_filter_search",
            placeholder="Search market, city, source, question...",
        )

    filtered_rows = _apply_filters(
        section_rows,
        severity_filter=severity_filter,
        type_filter=type_filter,
        market_filter=market_filter,
        family_filter=family_filter,
        search_text=search_text,
    )
    latest_signal = filtered_rows[0] if filtered_rows else (section_rows[0] if section_rows else signal_rows[0])

    st.html(_render_signal_table(filtered_rows))

    lower_left, lower_mid, lower_right = st.columns([1.15, 0.9, 0.75], gap="medium")
    trend_df = _build_trend_df(signal_rows)
    with lower_left:
        _render_chart_panel_title("SIGNAL TREND", "Last 60 minutes")
        trend_figure = _build_trend_figure(trend_df)
        if trend_figure is None:
            render_compact_note("Signal trend chart unavailable because Plotly is not installed. Table and actions remain available.", tone="warning")
        else:
            st.plotly_chart(trend_figure, use_container_width=True, config={"displayModeBar": False})
    with lower_mid:
        _render_chart_panel_title("SEVERITY DISTRIBUTION", "Current filtered set")
        distribution_figure = _build_distribution_figure(filtered_rows)
        if distribution_figure is None:
            render_compact_note("Severity chart unavailable because Plotly is not installed.", tone="warning")
        else:
            st.plotly_chart(distribution_figure, use_container_width=True, config={"displayModeBar": False})
    with lower_right:
        _render_latest_signal_detail(latest_signal)

    signal_market_id = str(latest_signal.get("market_id") or "")
    if signal_market_id:
        action_cols = st.columns([1.1, 1.1, 4.8], gap="small")
        if action_cols[0].button(
            "Open Workstation",
            key=f"signals_open_market_{signal_market_id}",
            use_container_width=True,
        ):
            if on_open_market is not None:
                on_open_market(signal_market_id, latest_signal)
            st.rerun()
        if action_cols[1].button(
            "Send to Command",
            key=f"signals_send_command_{signal_market_id}",
            use_container_width=True,
        ):
            if on_send_to_command is not None:
                on_send_to_command(signal_market_id, latest_signal)
            st.rerun()
        action_cols[2].caption(
            f"Selected signal market: {signal_market_id} · Type: {latest_signal.get('type_label', '-')} · Severity: {latest_signal.get('severity_label', '-')}"
        )

    with st.expander("Signal Context / Raw Status", expanded=False):
        context_cols = st.columns(3, gap="medium")
        with context_cols[0]:
            st.json(
                {
                    "scanner_status": scanner_status,
                    "queue_status": queue_status,
                    "market_universe": {
                        "schema_version": market_universe.get("schema_version"),
                        "market_count": market_universe.get("market_count"),
                    },
                    "evidence_scan": {
                        "schema_version": evidence_scan.get("schema_version"),
                        "market_count": evidence_scan.get("market_count"),
                        "fresh_count": evidence_scan.get("fresh_count"),
                        "stale_count": evidence_scan.get("stale_count"),
                    },
                },
                expanded=False,
            )
        with context_cols[1]:
            st.json(
                {
                    "source_policy_status": source_policy.get("overall_status"),
                    "source_counts": source_policy.get("counts"),
                    "gate_overall_status": gate_stack.get("overall_status"),
                    "gate_block_reasons": gate_stack.get("block_reasons"),
                },
                expanded=False,
            )
        with context_cols[2]:
            st.json(
                {
                    "family_report": {
                        "schema_version": family_report.get("schema_version"),
                        "market_count": family_report.get("market_count"),
                        "family_count": family_report.get("family_count"),
                        "signal_summary": family_report.get("signal_summary"),
                    },
                    "current_market": unified_status.get("current_market"),
                },
                expanded=False,
            )


def _render_theme() -> None:
    import streamlit as st

    st.html(
        dedent(
            """
            <style>
            :root {
              --signals-bg: #071019;
              --signals-surface: #0d1823;
              --signals-surface-2: #101f2c;
              --signals-border: rgba(116, 151, 184, 0.18);
              --signals-border-strong: rgba(72, 166, 255, 0.36);
              --signals-text: #f2f7fb;
              --signals-text-soft: #b9c6d3;
              --signals-text-dim: #7f93a7;
              --signals-blue: #2f9bff;
              --signals-green: #30d17d;
              --signals-amber: #ffb23f;
              --signals-red: #ff5b57;
              --signals-yellow: #ffd34d;
              --signals-magenta: #d64ff8;
            }
            .signals-header {
              display:flex;
              justify-content:space-between;
              align-items:flex-start;
              gap:1rem;
              padding:0.25rem 0 0.7rem 0;
            }
            .signals-header__title-wrap {
              display:flex;
              align-items:center;
              gap:0.75rem;
              flex-wrap:wrap;
            }
            .signals-header__title {
              color:var(--signals-text);
              font-size:1.38rem;
              font-weight:900;
              letter-spacing:0.04em;
            }
            .signals-header__subtitle {
              color:var(--signals-text-dim);
              font-size:0.88rem;
            }
            .signals-live-pill {
              border:1px solid rgba(48, 209, 125, 0.28);
              background:rgba(48, 209, 125, 0.14);
              color:var(--signals-green);
              border-radius:0.45rem;
              padding:0.18rem 0.45rem;
              font-size:0.72rem;
              font-weight:800;
              letter-spacing:0.08em;
            }
            .signals-header__meta {
              color:var(--signals-text-soft);
              font-size:0.8rem;
              padding-top:0.25rem;
            }
            .signals-table {
              border:1px solid var(--signals-border);
              background:rgba(8, 16, 25, 0.98);
              border-radius:0.9rem;
              overflow:hidden;
              margin-top:0.3rem;
              margin-bottom:0.95rem;
            }
            .signals-table__header,
            .signals-table__row {
              display:grid;
              grid-template-columns: 0.9fr 0.95fr 0.95fr 1.9fr 2.0fr 0.8fr 0.95fr 0.95fr 1.0fr;
              gap:0;
              align-items:center;
            }
            .signals-table__header {
              background:rgba(11, 22, 33, 1);
              border-bottom:1px solid var(--signals-border);
            }
            .signals-table__header div {
              color:var(--signals-text-dim);
              font-size:0.72rem;
              font-weight:800;
              letter-spacing:0.08em;
              text-transform:uppercase;
              padding:0.78rem 0.72rem;
            }
            .signals-table__row {
              border-bottom:1px solid rgba(116, 151, 184, 0.12);
            }
            .signals-table__row:last-child {
              border-bottom:none;
            }
            .signals-table__row div {
              color:var(--signals-text-soft);
              font-size:0.82rem;
              padding:0.76rem 0.72rem;
              line-height:1.32;
            }
            .signals-market {
              color:var(--signals-text) !important;
              font-weight:800;
            }
            .signals-summary {
              color:#d5e2ed !important;
            }
            .signals-value {
              font-variant-numeric:tabular-nums;
              color:var(--signals-text) !important;
              font-weight:800;
            }
            .signals-badge {
              display:inline-flex;
              align-items:center;
              justify-content:center;
              min-width:3rem;
              border-radius:999px;
              padding:0.18rem 0.48rem;
              font-size:0.68rem;
              font-weight:900;
              letter-spacing:0.08em;
              text-transform:uppercase;
              border:1px solid transparent;
            }
            .signals-badge--red {
              color:var(--signals-red);
              background:rgba(255, 91, 87, 0.12);
              border-color:rgba(255, 91, 87, 0.28);
            }
            .signals-badge--amber {
              color:var(--signals-amber);
              background:rgba(255, 178, 63, 0.12);
              border-color:rgba(255, 178, 63, 0.26);
            }
            .signals-badge--blue {
              color:var(--signals-blue);
              background:rgba(47, 155, 255, 0.12);
              border-color:rgba(47, 155, 255, 0.26);
            }
            .signals-badge--green {
              color:var(--signals-green);
              background:rgba(48, 209, 125, 0.12);
              border-color:rgba(48, 209, 125, 0.26);
            }
            .signals-badge--yellow {
              color:var(--signals-yellow);
              background:rgba(255, 211, 77, 0.10);
              border-color:rgba(255, 211, 77, 0.24);
            }
            .signals-badge--magenta {
              color:var(--signals-magenta);
              background:rgba(214, 79, 248, 0.12);
              border-color:rgba(214, 79, 248, 0.24);
            }
            .signals-selected-action {
              display:inline-flex;
              align-items:center;
              border-radius:0.38rem;
              border:1px solid rgba(47, 155, 255, 0.22);
              color:#c9e4ff;
              background:rgba(47, 155, 255, 0.10);
              font-size:0.72rem;
              font-weight:800;
              padding:0.26rem 0.48rem;
              white-space:nowrap;
            }
            .signals-panel-title {
              display:flex;
              justify-content:space-between;
              align-items:baseline;
              margin:0.35rem 0 0.45rem 0;
            }
            .signals-panel-title__main {
              color:var(--signals-blue);
              font-size:0.9rem;
              font-weight:900;
              letter-spacing:0.04em;
            }
            .signals-panel-title__sub {
              color:var(--signals-text-dim);
              font-size:0.72rem;
            }
            .signals-detail {
              border:1px solid var(--signals-border);
              background:rgba(8, 16, 25, 0.98);
              border-radius:0.9rem;
              padding:0.95rem;
              min-height:24rem;
            }
            .signals-detail__top {
              display:flex;
              align-items:center;
              gap:0.55rem;
              margin-bottom:0.75rem;
              flex-wrap:wrap;
            }
            .signals-detail__time {
              color:var(--signals-text-dim);
              font-size:0.76rem;
            }
            .signals-detail__market {
              color:var(--signals-text);
              font-size:1.2rem;
              font-weight:900;
              line-height:1.24;
              margin-bottom:0.15rem;
            }
            .signals-detail__question {
              color:#dbe7f2;
              font-size:0.92rem;
              margin-bottom:0.85rem;
            }
            .signals-detail__kv {
              display:grid;
              grid-template-columns: 1fr 1fr;
              gap:0.7rem 0.9rem;
              margin-bottom:1rem;
            }
            .signals-detail__item {
              border:1px solid rgba(116, 151, 184, 0.14);
              background:rgba(12, 21, 31, 0.98);
              border-radius:0.6rem;
              padding:0.7rem 0.75rem;
            }
            .signals-detail__label {
              color:var(--signals-text-dim);
              font-size:0.68rem;
              font-weight:800;
              letter-spacing:0.08em;
              text-transform:uppercase;
              margin-bottom:0.22rem;
            }
            .signals-detail__value {
              color:var(--signals-text);
              font-size:0.98rem;
              font-weight:850;
              line-height:1.26;
            }
            .signals-detail__button {
              display:block;
              width:100%;
              text-align:center;
              color:var(--signals-text);
              text-decoration:none;
              font-weight:800;
              border:1px solid rgba(47, 155, 255, 0.35);
              background:rgba(47, 155, 255, 0.14);
              border-radius:0.55rem;
              padding:0.72rem 0.9rem;
            }
            </style>
            """
        )
    )


def _render_signal_table(rows: list[dict]) -> str:
    if not rows:
        return """
        <div class="signals-table">
          <div class="signals-table__header">
            <div>Time (UTC)</div><div>Severity</div><div>Type</div><div>Market / Question</div><div>Signal Summary</div><div>Value</div><div>Source</div><div>Status</div><div>Live Actions</div>
          </div>
          <div class="signals-table__row">
            <div>-</div><div>-</div><div>-</div><div class="signals-market">No matching signals</div><div class="signals-summary">Adjust filters to widen the view.</div><div class="signals-value">-</div><div>-</div><div>-</div><div><span class="signals-selected-action">Use panel</span></div>
          </div>
        </div>
        """
    header = """
    <div class="signals-table__header">
      <div>Time (UTC)</div><div>Severity</div><div>Type</div><div>Market / Question</div><div>Signal Summary</div><div>Value</div><div>Source</div><div>Status</div><div>Live Actions</div>
    </div>
    """
    body = []
    for row in rows[:50]:
        body.append(
            f"""
            <div class="signals-table__row">
              <div>{escape(row["time_utc"])}</div>
              <div>{_badge(row["severity_label"], _severity_tone(row["severity"]))}</div>
              <div>{_badge(row["type_label"], _type_tone(row["type"]))}</div>
              <div class="signals-market">{escape(row["market_label"])}<br><span style="color:#90a3b7;font-weight:500;">{escape(row["question_label"])}</span></div>
              <div class="signals-summary">{escape(row["summary"])}</div>
              <div class="signals-value">{escape(row["value_label"])}</div>
              <div>{escape(row["source_label"])}</div>
              <div>{_badge(row["status_label"], _status_tone(row["status"]))}</div>
              <div><span class="signals-selected-action">Use panel below</span></div>
            </div>
            """
        )
    return f'<div class="signals-table">{header}{"".join(body)}</div>'


def _render_chart_panel_title(title: str, subtitle: str) -> None:
    import streamlit as st

    st.html(
        f"""
        <div class="signals-panel-title">
          <div class="signals-panel-title__main">{escape(title)}</div>
          <div class="signals-panel-title__sub">{escape(subtitle)}</div>
        </div>
        """
    )


def _render_latest_signal_detail(row: dict) -> None:
    import streamlit as st

    st.html(
        f"""
        <div class="signals-panel-title">
          <div class="signals-panel-title__main">LATEST SIGNAL DETAIL</div>
          <div class="signals-panel-title__sub">{escape(row["time_iso"])}</div>
        </div>
        <div class="signals-detail">
          <div class="signals-detail__top">
            {_badge(row["type_label"], _type_tone(row["type"]))}
            {_badge(row["severity_label"], _severity_tone(row["severity"]))}
            {_badge(row["status_label"], _status_tone(row["status"]))}
          </div>
          <div class="signals-detail__market">{escape(row["market_label"])}</div>
          <div class="signals-detail__question">{escape(row["question_label"])}</div>
          <div class="signals-detail__kv">
            <div class="signals-detail__item"><div class="signals-detail__label">Signal Summary</div><div class="signals-detail__value">{escape(row["summary"])}</div></div>
            <div class="signals-detail__item"><div class="signals-detail__label">Value</div><div class="signals-detail__value">{escape(row["value_label"])}</div></div>
            <div class="signals-detail__item"><div class="signals-detail__label">Source</div><div class="signals-detail__value">{escape(row["source_label"])}</div></div>
            <div class="signals-detail__item"><div class="signals-detail__label">Family</div><div class="signals-detail__value">{escape(row["family_label"])}</div></div>
            <div class="signals-detail__item"><div class="signals-detail__label">Reason</div><div class="signals-detail__value">{escape(row["reason"])}</div></div>
            <div class="signals-detail__item"><div class="signals-detail__label">Observed At</div><div class="signals-detail__value">{escape(row["time_utc"])} UTC</div></div>
          </div>
          <div class="signals-detail__button">Use the live Open Workstation / Send to Command buttons below</div>
        </div>
        """
    )


def _build_trend_figure(df: pd.DataFrame):
    if go is None:
        return None
    fig = go.Figure()
    colors = {
        "alerts": "#ff5b57",
        "anomalies": "#ffd34d",
        "ops": "#2f9bff",
    }
    for column, label in [("alerts", "Alerts"), ("anomalies", "Anomalies"), ("ops", "Ops Issues")]:
        fig.add_trace(
            go.Scatter(
                x=df["bucket"],
                y=df[column],
                mode="lines+markers",
                name=label,
                line={"width": 2.4, "color": colors[column]},
                marker={"size": 5},
            )
        )
    fig.update_layout(
        paper_bgcolor="rgba(8,16,25,0.0)",
        plot_bgcolor="rgba(8,16,25,0.0)",
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.01, "x": 0},
        xaxis={"showgrid": False, "tickfont": {"color": "#90a3b7", "size": 11}},
        yaxis={"showgrid": True, "gridcolor": "rgba(116,151,184,0.10)", "tickfont": {"color": "#90a3b7", "size": 11}},
        font={"color": "#dce7f2"},
        height=280,
    )
    return fig


def _build_distribution_figure(rows: list[dict]):
    if go is None:
        return None
    counts = Counter(row["severity_label"] for row in rows)
    labels = ["RED", "AMBER", "BLUE", "GREEN"]
    values = [counts.get(label, 0) for label in labels]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.66,
                marker={"colors": ["#ff5b57", "#ffb23f", "#2f9bff", "#30d17d"]},
                textinfo="none",
                sort=False,
            )
        ]
    )
    fig.update_layout(
        paper_bgcolor="rgba(8,16,25,0.0)",
        plot_bgcolor="rgba(8,16,25,0.0)",
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        showlegend=True,
        legend={"orientation": "v", "font": {"color": "#dce7f2", "size": 11}},
        font={"color": "#dce7f2"},
        height=280,
    )
    return fig


def _build_trend_df(rows: list[dict]) -> pd.DataFrame:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    recent = [row for row in rows if row["ts_dt"] >= cutoff]
    if not recent:
        recent = rows[:]
    records = []
    for row in recent:
        bucket = row["ts_dt"].replace(second=0, microsecond=0)
        records.append(
            {
                "bucket": bucket,
                "alerts": 1 if row["type"] == "alert" else 0,
                "anomalies": 1 if row["type"] == "anomaly" else 0,
                "ops": 1 if row["type"] in {"system", "info"} else 0,
            }
        )
    df = pd.DataFrame(records)
    if df.empty:
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        return pd.DataFrame({"bucket": [now], "alerts": [0], "anomalies": [0], "ops": [0]})
    grouped = df.groupby("bucket", as_index=False)[["alerts", "anomalies", "ops"]].sum().sort_values("bucket")
    return grouped


def _apply_filters(
    rows: list[dict],
    *,
    severity_filter: str,
    type_filter: str,
    market_filter: str,
    family_filter: str,
    search_text: str,
) -> list[dict]:
    query = str(search_text or "").strip().lower()
    filtered = []
    for row in rows:
        if severity_filter != "All" and row["severity_label"] != severity_filter:
            continue
        if type_filter != "All" and row["type_label"] != type_filter:
            continue
        if market_filter != "All" and row["market_label"] != market_filter:
            continue
        if family_filter != "All" and row["family_label"] != family_filter:
            continue
        if query:
            haystack = " ".join(
                [
                    row["market_label"],
                    row["question_label"],
                    row["summary"],
                    row["source_label"],
                    row["reason"],
                    row["family_label"],
                ]
            ).lower()
            if query not in haystack:
                continue
        filtered.append(row)
    return filtered


def _apply_signal_section(rows: list[dict], section: str) -> list[dict]:
    section_key = str(section or "Active Signals").strip().lower()
    if section_key == "signal history":
        return rows
    if section_key == "alert queue":
        return [row for row in rows if row.get("type") == "alert"]
    if section_key == "anomaly feed":
        return [row for row in rows if row.get("type") == "anomaly"]
    if section_key == "system signals":
        return [row for row in rows if row.get("type") in {"system", "info"}]
    return [row for row in rows if row.get("status") == "active"]


def _collect_signal_rows(
    *,
    scanner_status: dict,
    queue_status: dict,
    source_policy: dict,
    gate_stack: dict,
    unified_status: dict,
    family_report: dict,
) -> list[dict]:
    rows: list[dict] = []

    for alert in _load_recent_json(MARKET_ALERT_EVENTS_DIR, limit=30):
        severity = str(alert.get("severity") or "amber").lower()
        rows.append(
            _make_signal_row(
                ts=alert.get("generated_at"),
                severity=severity,
                signal_type="alert",
                market=alert.get("market_id"),
                question=_humanize_market(alert.get("market_id")),
                family=alert.get("market_family"),
                summary=alert.get("primary_reason") or "Market alert triggered",
                value=alert.get("alert_score"),
                source=_pick_source(alert),
                status="active",
                reason=alert.get("governance_reason") or alert.get("primary_reason"),
            )
        )

    for anomaly in _load_recent_jsonl(MARKET_ANOMALY_EVENTS_DIR, limit=30):
        severity = "amber" if str(anomaly.get("anomaly_bucket") or "").lower() in {"high", "medium"} else "green"
        rows.append(
            _make_signal_row(
                ts=anomaly.get("generated_at"),
                severity=severity,
                signal_type="anomaly",
                market=anomaly.get("market_id"),
                question=_humanize_market(anomaly.get("market_id")),
                family=anomaly.get("market_family"),
                summary=anomaly.get("primary_reason") or "Anomaly elevated",
                value=anomaly.get("anomaly_score"),
                source=_pick_source(anomaly),
                status="active",
                reason=anomaly.get("recommended_operator_action") or anomaly.get("governance_reason"),
            )
        )

    source_counts = source_policy.get("counts") or {}
    if source_policy:
        if int(source_counts.get("unavailable") or 0) > 0:
            rows.append(
                _make_signal_row(
                    ts=source_policy.get("generated_at"),
                    severity="red",
                    signal_type="system",
                    market="Source Layer",
                    question="Source availability degraded",
                    family="-",
                    summary=f"Unavailable sources > {source_counts.get('unavailable')}",
                    value=source_counts.get("unavailable"),
                    source="Source Policy",
                    status="active",
                    reason=source_policy.get("overall_status") or "blocked",
                )
            )
        if int(source_counts.get("stale") or 0) > 0:
            rows.append(
                _make_signal_row(
                    ts=source_policy.get("generated_at"),
                    severity="amber",
                    signal_type="system",
                    market="Source Layer",
                    question="Freshness degraded",
                    family="-",
                    summary=f"Stale sources > {source_counts.get('stale')}",
                    value=source_counts.get("stale"),
                    source="Source Policy",
                    status="active",
                    reason="stale_source_detected",
                )
            )

    if scanner_status:
        rows.append(
            _make_signal_row(
                ts=scanner_status.get("generated_at"),
                severity="blue" if int(scanner_status.get("backlog_count") or 0) == 0 else "amber",
                signal_type="info",
                market="Scanner",
                question="Evidence scanner heartbeat",
                family="-",
                summary=f"Scanned {scanner_status.get('scanned_markets') or 0} markets",
                value=scanner_status.get("backlog_count") or 0,
                source="Scanner",
                status="active",
                reason=scanner_status.get("next_scan_eta") or "heartbeat_ok",
            )
        )

    if gate_stack:
        block_reasons = gate_stack.get("block_reasons") or []
        rows.append(
            _make_signal_row(
                ts=gate_stack.get("generated_at"),
                severity="red" if str(gate_stack.get("overall_status") or "").lower() == "degraded" else "green",
                signal_type="system",
                market=gate_stack.get("market_id") or "Execution Gateway",
                question="Gate stack status",
                family="-",
                summary=(block_reasons[0] if block_reasons else gate_stack.get("overall_status")) or "gate update",
                value=len(block_reasons),
                source="Gateway",
                status="active",
                reason=(block_reasons[0] if block_reasons else gate_stack.get("overall_status")) or "-",
            )
        )

    monitoring = unified_status.get("monitoring") or {}
    counts = monitoring.get("counts") or {}
    if monitoring:
        rows.append(
            _make_signal_row(
                ts=unified_status.get("generated_at"),
                severity="amber" if int(counts.get("stale") or 0) else "green",
                signal_type="info",
                market="Runtime",
                question="Worker monitoring summary",
                family="-",
                summary=f"{counts.get('healthy', 0)} healthy / {counts.get('blocked', 0)} blocked",
                value=monitoring.get("worker_count") or 0,
                source="System",
                status="active",
                reason=monitoring.get("overall_status") or "runtime_summary",
            )
        )

    top_family = ((family_report.get("top_anomalies") or [{}])[0] if family_report else {}) or {}
    if family_report:
        rows.append(
            _make_signal_row(
                ts=family_report.get("generated_at"),
                severity="amber" if int((family_report.get("anomaly_bucket_counts") or {}).get("medium") or 0) else "green",
                signal_type="anomaly",
                market=top_family.get("market_id") or "Family Scan",
                question="Family anomaly summary",
                family=top_family.get("market_family") or "-",
                summary=(top_family.get("primary_reason") or "Family scan completed"),
                value=top_family.get("intervention_like_score") or 0,
                source="Family Scanner",
                status="resolved" if int((family_report.get("anomaly_bucket_counts") or {}).get("high") or 0) == 0 else "active",
                reason=top_family.get("recommended_operator_action") or family_report.get("input_mode"),
            )
        )

    rows.sort(key=lambda item: (item["severity_rank"], item["ts_dt"]), reverse=True)
    return rows


def _make_signal_row(
    *,
    ts: object,
    severity: str,
    signal_type: str,
    market: object,
    question: object,
    family: object,
    summary: object,
    value: object,
    source: object,
    status: str,
    reason: object,
) -> dict:
    ts_dt = _parse_dt(ts)
    severity_label = severity.upper()
    type_label = signal_type.upper()
    market_label = _clean_label(market)
    market_id = _extract_market_id(market)
    return {
        "ts_dt": ts_dt,
        "time_utc": ts_dt.astimezone(timezone.utc).strftime("%H:%M:%S"),
        "time_iso": ts_dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "severity": severity.lower(),
        "severity_label": severity_label,
        "severity_rank": _severity_rank(severity),
        "type": signal_type.lower(),
        "type_label": type_label,
        "market_id": market_id,
        "market_label": market_label,
        "question_label": _clean_label(question),
        "family_label": _clean_label(family),
        "summary": _clean_label(summary),
        "value_label": _value_label(value),
        "source_label": _clean_label(source),
        "status": status.lower(),
        "status_label": status.upper(),
        "reason": _clean_label(reason),
    }


def _extract_market_id(value: object) -> str | None:
    text = str(value or "").strip()
    if not text or text in {"Source Layer", "Runtime", "Scanner", "Execution Gateway", "Family Scan"}:
        return None
    return text


def _parse_dt(value: object) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value or "").strip()
    if not text:
        return datetime.now(timezone.utc)
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def _severity_rank(value: str) -> int:
    order = {"red": 4, "amber": 3, "yellow": 3, "blue": 2, "green": 1}
    return order.get(str(value or "").lower(), 0)


def _severity_tone(value: str) -> str:
    mapping = {"red": "red", "amber": "amber", "yellow": "yellow", "blue": "blue", "green": "green"}
    return mapping.get(str(value or "").lower(), "blue")


def _type_tone(value: str) -> str:
    mapping = {"alert": "red", "anomaly": "amber", "system": "yellow", "info": "blue"}
    return mapping.get(str(value or "").lower(), "blue")


def _status_tone(value: str) -> str:
    mapping = {"active": "green", "resolved": "blue", "suppressed": "magenta", "blocked": "red"}
    return mapping.get(str(value or "").lower(), "green")


def _badge(label: str, tone: str) -> str:
    return f'<span class="signals-badge signals-badge--{escape(tone)}">{escape(label)}</span>'


def _clean_label(value: object) -> str:
    text = str(value or "-").strip()
    return text or "-"


def _humanize_market(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "-"
    return text.replace("_", " ").replace(".", " / ").title()


def _value_label(value: object) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _pick_source(payload: dict) -> str:
    refs = payload.get("upstream_refs") or payload.get("contract_refs") or {}
    if isinstance(refs, dict):
        for key, value in refs.items():
            if value:
                return key.replace("_ref", "").replace("_", " ").title()
    return str(payload.get("source_name") or payload.get("source") or payload.get("indicator_version") or "System")


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted({value for value in values if value and value != "-"})


def _load_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_latest_json(directory: Path) -> dict:
    if not directory.exists():
        return {}
    candidates = sorted(directory.glob("*.json"), key=_sort_key, reverse=True)
    if not candidates:
        return {}
    try:
        return json.loads(candidates[0].read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_recent_json(directory: Path, *, limit: int) -> list[dict]:
    if not directory.exists():
        return []
    candidates = sorted(directory.glob("*.json"), key=_sort_key, reverse=True)[:limit]
    items: list[dict] = []
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            items.append(payload)
    return items


def _load_recent_jsonl(directory: Path, *, limit: int) -> list[dict]:
    if not directory.exists():
        return []
    candidates = sorted(directory.glob("*.jsonl"), key=_sort_key, reverse=True)[:limit]
    rows: list[dict] = []
    for path in candidates:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for line in lines[-limit:]:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows[-limit:]


def _sort_key(path: Path) -> tuple[float, str]:
    try:
        return (path.stat().st_mtime, path.name)
    except OSError:
        return (0.0, path.name)
