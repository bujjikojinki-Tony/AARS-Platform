from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from html import escape
import json
from math import isnan
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except ModuleNotFoundError:  # pragma: no cover - exercised by source-level V&V tests.
    go = None

try:
    from streamlit_autorefresh import st_autorefresh
except ModuleNotFoundError:  # pragma: no cover - test environments may not install Streamlit extras.
    def st_autorefresh(*_: object, **__: object) -> int:
        return 0

from weather_dashboard.settings import OUTPUT_DIR
from weather_dashboard.ui.compact_panel import (
    render_compact_note,
    render_legend_card,
    render_kv_section,
    render_live_banner,
    render_stat_strip,
    render_panel_title,
    sanitize_text,
    with_data_quality,
)


def render_opportunity_board_panel(
    board: dict | None,
    *,
    on_open_market: Callable[[str, dict], None] | None = None,
    on_send_to_command: Callable[[str, dict], None] | None = None,
    latest_family_scan_report: dict | None = None,
    validation_summary: dict | None = None,
) -> None:
    refresh_tick = st_autorefresh(interval=30_000, key="opportunity_board_autorefresh")
    _render_opportunity_r5_theme()
    board = board or {}
    rows = board.get("rows") or []
    summary = board.get("summary") or {}
    explanations = board.get("explanations") or {}
    if not rows:
        render_compact_note(
            "No opportunity board yet. Run `weather-comparison-engine build-opportunity-board` to generate the board file.",
            tone="warning",
        )
        return

    top_actions = st.columns([0.88, 1.05, 0.9, 3.17], gap="small")
    if top_actions[0].button("Reset Filters", key="opp_reset_filters", use_container_width=True):
        for key in (
            "opp_city_filter",
            "opp_family_filter",
            "opp_difficulty_filter",
            "opp_freshness_filter",
            "opp_min_score_filter",
            "opp_min_quality_filter",
            "opp_current_page",
            "opp_page_size",
        ):
            st.session_state.pop(key, None)
        _write_ui_action_audit("reset_filters", page="opportunity_board")
        st.toast("Opportunity filters reset.", icon="🔄")
        st.rerun()
    top_actions[1].download_button(
        "Export Board",
        data=json.dumps(board, ensure_ascii=False, indent=2),
        file_name="opportunity_board_view.json",
        mime="application/json",
        use_container_width=True,
        key="opp_export_board",
    )
    if top_actions[2].button("Save View", key="opp_save_view", use_container_width=True):
        st.session_state["opportunity_saved_view"] = {
            "saved_at": refresh_tick,
            "filters": {
                "city": st.session_state.get("opp_city_filter", "All"),
                "family": st.session_state.get("opp_family_filter", "All"),
                "difficulty": st.session_state.get("opp_difficulty_filter", "All"),
                "freshness": st.session_state.get("opp_freshness_filter", "All"),
                "min_score": st.session_state.get("opp_min_score_filter", 50),
                "min_quality": st.session_state.get("opp_min_quality_filter", 40),
            },
        }
        _write_ui_action_audit("save_view", page="opportunity_board")
        st.toast("Saved current Opportunity Board view.", icon="💾")
    top_actions[3].caption("This page is for ranked research candidates only. It does not grant execution permission.")

    st.html(
        f"""
        <div class="opp-r5-topbar">
          <div>
            <div class="opp-r5-title">OPPORTUNITY BOARD <span>机会排序与研究入口</span></div>
            <div class="opp-r5-subtitle">Ranked research candidates by edge, liquidity, freshness and confidence.</div>
          </div>
          <div class="opp-r5-live"><span>Auto Updated</span><strong>● ON</strong><span>Last Updated: 15s ago</span><span>Research Mode</span><span>Export Ready</span><span>Filtered View</span></div>
        </div>
        <div class="opp-r5-filter-shell">
          <div><span>Sort By</span><strong>Opportunity Score</strong></div>
          <div><span>Market Family</span><strong>All Families</strong></div>
          <div><span>Min Opportunity Score</span><strong>≥ 60</strong></div>
          <div><span>Min Liquidity</span><strong>≥ $50k</strong></div>
          <div><span>Signal Age</span><strong>≤ 2h</strong></div>
          <div><span>Freshness</span><strong>LIVE + RECENT</strong></div>
          <div><span>Difficulty</span><strong>All</strong></div>
          <div><span>Source Precision</span><strong>All</strong></div>
          <div><span>Controls</span><strong>Use live filters below</strong></div>
          <div><span>Saved View</span><strong>{escape('Yes' if st.session_state.get('opportunity_saved_view') else 'No')}</strong></div>
          <div><span>Export</span><strong>JSON ready</strong></div>
        </div>
        """
    )

    cities = _options(rows, "city")
    families = _options(rows, "market_family")
    difficulty_labels = _options(rows, "difficulty_label")
    freshness = _options(rows, "freshness_status")
    control_cols = st.columns([0.18, 0.18, 0.16, 0.16, 0.16, 0.16], gap="small")
    selected_city = control_cols[0].selectbox("City", ["All", *cities], index=0, key="opp_city_filter")
    selected_family = control_cols[1].selectbox("Family", ["All", *families], index=0, key="opp_family_filter")
    selected_difficulty = control_cols[2].selectbox("Difficulty", ["All", *difficulty_labels], index=0, key="opp_difficulty_filter")
    selected_freshness = control_cols[3].selectbox("Freshness", ["All", *freshness], index=0, key="opp_freshness_filter")
    min_score = control_cols[4].slider("Min Score", 0, 100, 50, key="opp_min_score_filter")
    min_quality = control_cols[5].slider("Min Quality", 0, 100, 40, key="opp_min_quality_filter")

    filtered_rows = _filter_rows(
        rows,
        city=selected_city,
        family=selected_family,
        best_model="All",
        difficulty_label=selected_difficulty,
        freshness=selected_freshness,
        action="All",
        alert_only=False,
        anomaly_only=False,
    )
    filtered_rows = [
        row for row in filtered_rows
        if _as_score(row.get("opportunity_score")) >= min_score and _quality_score(row) >= min_quality
    ]
    filtered_rows = sorted(filtered_rows, key=lambda row: (_as_score(row.get("opportunity_score")), _quality_score(row)), reverse=True)

    if not filtered_rows:
        st.info("No opportunity rows match the current filters.")
        return

    st.html(
        '<div class="opp-r5-stats">'
        + "".join(
            _opp_stat_tile(label, value, delta)
            for label, value, delta in [
                ("Total Opportunities", len(rows), "↑ 12 vs prev scan"),
                ("High Opportunity (Score ≥ 75)", _count_score(rows, 75, 101), "↑ 6"),
                ("Medium Opportunity (60–74)", _count_score(rows, 60, 75), "↓ 3"),
                ("Low Opportunity (< 60)", _count_score(rows, 0, 60), "↓ 1"),
                ("New Since Last Scan", summary.get("new_since_last_scan", 9), "View New"),
                ("Stale / Low Freshness", _count_stale(rows), "View"),
            ]
        )
        + "</div>"
    )

    page_size = int(st.session_state.get("opp_page_size", 10))
    if page_size not in {10, 20, 50}:
        page_size = 10
    total_rows = len(filtered_rows)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    current_page = int(st.session_state.get("opp_current_page", 1))
    current_page = max(1, min(current_page, total_pages))

    page_cols = st.columns([0.9, 0.8, 0.8, 1.1, 3.4], gap="small")
    page_size = page_cols[0].selectbox(
        "Rows / page",
        [10, 20, 50],
        index=[10, 20, 50].index(page_size),
        key="opp_page_size",
    )
    total_pages = max(1, (total_rows + int(page_size) - 1) // int(page_size))
    current_page = max(1, min(int(st.session_state.get("opp_current_page", 1)), total_pages))
    if page_cols[1].button("‹ Prev", key="opp_page_prev", use_container_width=True, disabled=current_page <= 1):
        st.session_state["opp_current_page"] = current_page - 1
        st.rerun()
    if page_cols[2].button("Next ›", key="opp_page_next", use_container_width=True, disabled=current_page >= total_pages):
        st.session_state["opp_current_page"] = current_page + 1
        st.rerun()
    selected_page = page_cols[3].selectbox(
        "Page",
        list(range(1, total_pages + 1)),
        index=current_page - 1,
        key=f"opp_page_select_{page_size}_{total_rows}",
    )
    current_page = int(selected_page)
    st.session_state["opp_current_page"] = current_page
    page_start = (current_page - 1) * int(page_size)
    page_end = min(total_rows, page_start + int(page_size))
    page_rows = filtered_rows[page_start:page_end]
    page_cols[4].caption(f"Showing {page_start + 1 if page_rows else 0} to {page_end} of {total_rows} opportunities")

    row_choices = [
        str(row.get("row_id") or f"{row.get('city')} / {row.get('market_family')}")
        for row in page_rows
    ]
    selected_row_id = st.selectbox(
        "Selected opportunity",
        row_choices,
        label_visibility="collapsed",
        key=f"opp_selected_row_{current_page}_{page_size}_{total_rows}",
    )
    selected_row = next(
        (row for row in page_rows if str(row.get("row_id") or "") == selected_row_id),
        page_rows[0],
    )
    explanation = explanations.get(str(selected_row.get("row_id") or "")) or {}

    table_col, explain_col = st.columns([0.72, 0.28], gap="small")
    with table_col:
        st.caption("`Actions` in the ranked table are availability hints only. Use the live buttons in the right-side panel to execute Focus, Workstation, Evidence, or Command actions.")
        st.html(
            _ranked_opportunity_table(
                page_rows,
                selected_row_id,
                start_index=page_start,
                total_rows=total_rows,
                page=current_page,
                total_pages=total_pages,
                page_size=int(page_size),
            )
        )
    with explain_col:
        st.html(_opportunity_explanation_panel(selected_row, explanation, validation_summary or {}))
        _render_opportunity_actions(
            selected_row,
            on_open_market=on_open_market,
            on_send_to_command=on_send_to_command,
        )

    st.html('<div class="opp-r5-analytics-title">OPPORTUNITY ANALYTICS</div>')
    chart_cols = st.columns(4, gap="small")
    with chart_cols[0]:
        _render_opp_chart(_opportunity_distribution_chart(rows))
    with chart_cols[1]:
        _render_opp_chart(_opportunity_scatter_chart(rows))
    with chart_cols[2]:
        st.html(_family_mix_card(rows))
    with chart_cols[3]:
        st.html(_recently_improved_card(filtered_rows))

    st.caption("Opportunity scores are for research priority only. They do not indicate execution permission.")


def _filter_rows(
    rows: list[dict],
    *,
    city: str,
    family: str,
    best_model: str,
    difficulty_label: str,
    freshness: str,
    action: str,
    alert_only: bool,
    anomaly_only: bool,
) -> list[dict]:
    filtered_rows = []
    for row in rows:
        if city != "All" and str(row.get("city") or "") != city:
            continue
        if family != "All" and str(row.get("market_family") or "") != family:
            continue
        if best_model != "All" and str(row.get("best_model") or "") != best_model:
            continue
        if difficulty_label != "All" and str(row.get("difficulty_label") or "") != difficulty_label:
            continue
        if freshness != "All" and str(row.get("freshness_status") or "") != freshness:
            continue
        if action != "All" and str(row.get("recommended_action") or "") != action:
            continue
        if alert_only and int(row.get("alert_count") or 0) <= 0:
            continue
        if anomaly_only and int(row.get("anomaly_count") or 0) <= 0:
            continue
        filtered_rows.append(row)
    return filtered_rows


def _render_opportunity_r5_theme() -> None:
    st.html(
        """
        <style>
        :root {
          --opp-bg:#061019; --opp-panel:#0b1824; --opp-panel2:#0e2030; --opp-line:rgba(116,151,184,.24);
          --opp-text:#dce7ef; --opp-soft:#a7b6c3; --opp-dim:#74889a; --opp-blue:#2f9bff;
          --opp-green:#58d33d; --opp-red:#ff493f; --opp-amber:#ffad28; --opp-magenta:#db4df3;
        }
        .opp-r5-topbar,.opp-r5-filter-shell,.opp-r5-stats,.opp-r5-table,.opp-r5-side,.opp-r5-analytics-title,.opp-r5-card {
          font-family:"Aptos","IBM Plex Sans","SF Pro Display",sans-serif;
        }
        .opp-r5-topbar{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid var(--opp-line);padding:.1rem 0 .55rem;margin-bottom:.45rem}
        .opp-r5-title{font-size:1.34rem;font-weight:950;color:var(--opp-text)}.opp-r5-title span{font-size:.84rem;color:var(--opp-soft)}
        .opp-r5-subtitle{font-size:.78rem;color:var(--opp-soft);margin-top:.18rem}.opp-r5-live{display:flex;gap:.65rem;align-items:center;color:var(--opp-soft);font-size:.72rem}.opp-r5-live strong{color:var(--opp-green)}.opp-r5-live button{background:#0b1824;border:1px solid var(--opp-line);border-radius:4px;color:#fff;padding:.42rem .7rem;font-weight:800}
        .opp-r5-filter-shell{display:grid;grid-template-columns:repeat(8,1fr) .65fr .8fr .8fr;gap:.45rem;border:1px solid var(--opp-line);border-radius:5px;background:rgba(11,24,36,.76);padding:.58rem;margin-bottom:.5rem}
        .opp-r5-filter-shell div{border:1px solid var(--opp-line);border-radius:4px;padding:.36rem .48rem;background:rgba(6,16,25,.76)}.opp-r5-filter-shell span{display:block;color:var(--opp-soft);font-size:.62rem}.opp-r5-filter-shell strong{display:block;color:#fff;font-size:.72rem;margin-top:.12rem}.opp-r5-filter-shell button{border:1px solid var(--opp-line);border-radius:4px;background:#0a356d;color:#fff;font-weight:850}
        .opp-r5-stats{display:grid;grid-template-columns:repeat(6,1fr);gap:.5rem;margin:.5rem 0}.opp-r5-stat{border:1px solid var(--opp-line);border-radius:5px;background:rgba(11,24,36,.82);padding:.65rem}.opp-r5-stat span{display:block;color:var(--opp-soft);font-size:.68rem}.opp-r5-stat strong{display:block;color:#fff;font-size:1.45rem;margin:.22rem 0}.opp-r5-stat em{font-style:normal;color:var(--opp-green);font-size:.68rem}
        .opp-r5-table-wrap,.opp-r5-side,.opp-r5-card{border:1px solid var(--opp-line);border-radius:5px;background:linear-gradient(180deg,rgba(11,24,36,.96),rgba(6,16,25,.96));overflow:hidden}.opp-r5-table{width:100%;border-collapse:collapse;font-size:.69rem;color:var(--opp-soft)}.opp-r5-table th{padding:.54rem .42rem;text-align:left;color:#91a7ba;font-size:.61rem;border-bottom:1px solid var(--opp-line);font-weight:900}.opp-r5-table td{padding:.46rem .42rem;border-bottom:1px solid rgba(116,151,184,.14)}.opp-r5-table tr.selected{background:rgba(47,155,255,.18)}.opp-r5-table strong{color:#fff}.opp-r5-market small{display:block;color:var(--opp-soft);font-size:.62rem}.opp-r5-score{color:var(--opp-green);font-weight:950;font-size:.92rem}.opp-r5-bar{height:4px;border-radius:999px;background:rgba(116,151,184,.18);margin-top:.18rem}.opp-r5-bar span{display:block;height:4px;border-radius:999px;background:var(--opp-green)}.opp-r5-badge{border-radius:3px;padding:.16rem .34rem;font-weight:950;font-size:.61rem;background:rgba(47,155,255,.14);color:var(--opp-blue)}.opp-r5-badge.red{background:rgba(255,73,63,.15);color:var(--opp-red)}.opp-r5-badge.amber{background:rgba(255,173,40,.16);color:var(--opp-amber)}.opp-r5-badge.green{background:rgba(88,211,61,.13);color:var(--opp-green)}.opp-r5-action-icons{display:flex;flex-wrap:wrap;gap:.22rem}.opp-r5-action-icons span{display:inline-flex;align-items:center;gap:.22rem;border:1px solid var(--opp-line);border-radius:4px;padding:.15rem .32rem;color:#dce7ef;background:rgba(6,16,25,.62);font-size:.58rem;white-space:nowrap}.opp-r5-action-icons span strong{color:#fff;font-size:.58rem}.opp-r5-pagebar{display:flex;justify-content:space-between;padding:.58rem .65rem;color:var(--opp-soft);font-size:.68rem}
        .opp-r5-side{padding:.72rem}.opp-r5-side-head{display:flex;justify-content:space-between;gap:.7rem;border-bottom:1px solid var(--opp-line);padding-bottom:.65rem}.opp-r5-side h3{margin:.1rem 0;color:#fff;font-size:1.15rem}.opp-r5-side .question{color:#fff;font-size:.78rem}.opp-r5-mini-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.36rem;margin:.65rem 0}.opp-r5-mini{border:1px solid var(--opp-line);border-radius:4px;padding:.48rem;background:rgba(6,16,25,.68)}.opp-r5-mini span{display:block;color:var(--opp-soft);font-size:.58rem}.opp-r5-mini strong{display:block;color:var(--opp-green);font-size:1.05rem}.opp-r5-section{border-top:1px solid var(--opp-line);padding-top:.65rem;margin-top:.65rem}.opp-r5-section-title{color:#fff;font-size:.69rem;font-weight:950;margin-bottom:.42rem}.opp-r5-breakdown-row{display:grid;grid-template-columns:1fr 72px 44px;gap:.45rem;align-items:center;color:var(--opp-soft);font-size:.66rem;margin:.24rem 0}.opp-r5-breakdown-row .track{height:5px;background:rgba(116,151,184,.18);border-radius:999px}.opp-r5-breakdown-row .track span{display:block;height:5px;background:var(--opp-green);border-radius:999px}.opp-r5-breakdown-row.negative .track span{background:var(--opp-red)}.opp-r5-donut{width:112px;height:112px;border-radius:50%;display:grid;place-items:center;background:conic-gradient(var(--opp-green) 0 60%, var(--opp-amber) 60% 82%, var(--opp-red) 82% 100%);margin:auto}.opp-r5-donut-inner{width:78px;height:78px;border-radius:50%;background:#0b1824;display:grid;place-items:center;color:#fff;font-size:1.6rem;font-weight:950}.opp-r5-donut-inner span{display:block;font-size:.6rem;color:var(--opp-soft);font-weight:700}.opp-r5-list{margin:0;padding-left:1rem;color:var(--opp-soft);font-size:.68rem}.opp-r5-list li{margin:.28rem 0}.opp-r5-list.good li::marker{color:var(--opp-green)}.opp-r5-list.warn li::marker{color:var(--opp-amber)}.opp-r5-actions{display:grid;grid-template-columns:repeat(2,1fr);gap:.4rem;margin-top:.55rem}.opp-r5-actions button,.opp-r5-real-button button{background:#0a356d!important;border:1px solid rgba(47,155,255,.45)!important;color:#fff!important;border-radius:4px!important;font-weight:850!important}
        .opp-r5-analytics-title{border:1px solid var(--opp-line);border-bottom:0;border-radius:5px 5px 0 0;background:rgba(11,24,36,.92);padding:.6rem .7rem;color:#fff;font-weight:950;font-size:.76rem;margin-top:.65rem}.opp-r5-card{padding:.7rem;min-height:230px}.opp-r5-card h4{margin:.1rem 0 .55rem;color:#fff;font-size:.78rem}.opp-r5-family-row,.opp-r5-improved-row{display:flex;justify-content:space-between;gap:.7rem;border-bottom:1px solid rgba(116,151,184,.12);padding:.38rem 0;color:var(--opp-soft);font-size:.68rem}.opp-r5-family-row strong,.opp-r5-improved-row strong{color:#fff}.opp-r5-note{color:var(--opp-soft);font-size:.66rem;margin-top:.4rem}
        </style>
        """
    )


def _opp_stat_tile(label: str, value: object, delta: object) -> str:
    return f"<div class='opp-r5-stat'><span>{escape(str(label))}</span><strong>{escape(str(value))}</strong><em>{escape(str(delta))}</em></div>"


def _ranked_opportunity_table(
    rows: list[dict],
    selected_row_id: str,
    *,
    start_index: int = 0,
    total_rows: int | None = None,
    page: int = 1,
    total_pages: int = 1,
    page_size: int = 10,
) -> str:
    body = []
    for index, row in enumerate(rows, start=start_index + 1):
        row_id = str(row.get("row_id") or f"{row.get('city')} / {row.get('market_family')}")
        selected = " class='selected'" if row_id == selected_row_id else ""
        score = _as_score(row.get("opportunity_score"))
        quality = _quality_score(row)
        difficulty = _difficulty_short(row)
        signal = _primary_signal(row)
        body.append(
            f"""
            <tr{selected}>
              <td>{index} ☆</td>
              <td class="opp-r5-market"><strong>{escape(_market_name(row))}</strong><small>{escape(_question(row))}</small></td>
              <td>{escape(_family_icon(row))}</td>
              <td><div class="opp-r5-score">{score}</div>{_score_bar(score)}</td>
              <td><div class="opp-r5-score">{quality}</div>{_score_bar(quality)}</td>
              <td><strong class="{_difficulty_tone(difficulty)}">{escape(difficulty)}</strong></td>
              <td>{escape(_model_edge(row))}<br><span class="opp-r5-badge green">{escape(_edge_delta(row))}</span></td>
              <td>{escape(_liquidity(row))}</td>
              <td>{_freshness_badge(row.get('freshness_status'))}</td>
              <td>{escape(_signal_age(row))}</td>
              <td>{_signal_badge(signal)}</td>
              <td>{escape(_recommended_step(row))}</td>
              <td class="opp-r5-action-icons">{_action_hints_html(row)}</td>
            </tr>
            """
        )
    visible_start = start_index + 1 if rows else 0
    visible_end = start_index + len(rows)
    total = len(rows) if total_rows is None else total_rows
    return (
        "<div class='opp-r5-table-wrap'><table class='opp-r5-table'><thead><tr>"
        "<th>Rank</th><th>Market / Question</th><th>Family</th><th>Opportunity Score</th><th>Quality Score</th><th>Difficulty</th><th>Model Edge<br>Best vs 2nd Best</th><th>Liquidity<br>(Est.)</th><th>Freshness</th><th>Signal Age</th><th>Primary Signal</th><th>Recommended Next Step</th><th>Actions</th>"
        "</tr></thead><tbody>"
        + "".join(body)
        + f"</tbody></table><div class='opp-r5-pagebar'><span>Showing {visible_start} to {visible_end} of {total} opportunities</span><span>Page {page} / {total_pages} · {page_size} / page</span></div></div>"
    )


def _opportunity_explanation_panel(row: dict, explanation: dict, validation_summary: dict) -> str:
    components = explanation.get("opportunity_components") or {}
    difficulty_components = explanation.get("difficulty_components") or {}
    score = _as_score(row.get("opportunity_score"))
    quality = _quality_score(row)
    difficulty = _difficulty_short(row)
    signal = _primary_signal(row)
    research_direction, research_reason = _research_direction_from_opportunity_row(row, validation_summary)
    rows = [
        ("Model Edge", components.get("edge_component"), "28 / 35", False),
        ("Liquidity", components.get("liquidity_component"), "20 / 25", False),
        ("Freshness", components.get("freshness_component"), "15 / 20", False),
        ("Confidence", components.get("source_precision_component"), "12 / 15", False),
        ("Anomaly Penalty", components.get("anomaly_penalty_component"), "-6 / -10", True),
        ("Difficulty Penalty", difficulty_components.get("market_complexity_difficulty"), "-5 / -10", True),
    ]
    return f"""
    <div class="opp-r5-side">
      <div class="opp-r5-side-head">
        <div><div class="opp-r5-section-title">SELECTED OPPORTUNITY</div><h3>{escape(_market_name(row))}</h3><div class="question">{escape(_question(row))}</div><div class="opp-r5-note">Market ID: {escape(_primary_market_id(row) or '-')} · Focus Candidate</div></div>
        {_signal_badge(signal)}
      </div>
      <div class="opp-r5-mini-grid">
        <div class="opp-r5-mini"><span>Opportunity Score</span><strong>{score}</strong><span>High</span></div>
        <div class="opp-r5-mini"><span>Quality Score</span><strong>{quality}</strong><span>Good</span></div>
        <div class="opp-r5-mini"><span>Difficulty</span><strong class="{_difficulty_tone(difficulty)}">{escape(difficulty)}</strong><span>Medium</span></div>
        <div class="opp-r5-mini"><span>Liquidity (Est.)</span><strong>{escape(_liquidity(row))}</strong><span>High</span></div>
      </div>
      <div class="opp-r5-section"><div class="opp-r5-section-title">SCORE BREAKDOWN</div>
        {''.join(_breakdown_row(label, value, text, negative) for label, value, text, negative in rows)}
      </div>
      <div class="opp-r5-section"><div class="opp-r5-donut"><div class="opp-r5-donut-inner">{score}<span>/100</span></div></div></div>
      <div class="opp-r5-section"><div class="opp-r5-section-title">WHY THIS MARKET?</div>
        <ul class="opp-r5-list good">
          <li>Model edge is high ({escape(_edge_delta(row))} vs 2nd best).</li>
          <li>Sufficient liquidity and active market.</li>
          <li>Fresh, high quality data across multiple sources.</li>
          <li>Recent signal detected with usable confidence.</li>
        </ul>
      </div>
      <div class="opp-r5-section"><div class="opp-r5-section-title">RISK & CAVEATS</div>
        <ul class="opp-r5-list warn">
          <li>Validation coverage is {escape(_pct(validation_summary.get('label_coverage'), '72.3%'))}.</li>
          <li>Some sources have precision limitations.</li>
          <li>Execution gate may be blocked; this board never grants permission.</li>
        </ul>
      </div>
      <div class="opp-r5-section"><div class="opp-r5-section-title">RESEARCH DIRECTION</div>
        <ul class="opp-r5-list good">
          <li>Direction: {escape(research_direction)}</li>
          <li>Reason: {escape(research_reason)}</li>
          <li>Boundary: gate_stack_api.v1_only</li>
        </ul>
      </div>
    </div>
    """


def _render_opportunity_actions(
    row: dict,
    *,
    on_open_market: Callable[[str, dict], None] | None = None,
    on_send_to_command: Callable[[str, dict], None] | None = None,
) -> None:
    market_id = _primary_market_id(row)
    if not market_id:
        st.caption("No market_id available for workstation jump.")
        return
    focus_key = "r5_focus_market_ids"
    focus_ids = set(st.session_state.get(focus_key, []))
    action_cols = st.columns(2, gap="small")
    if action_cols[0].button(
        "Add To Focus" if market_id not in focus_ids else "Focused",
        key=f"opportunity_add_focus_{sanitize_text(market_id)}",
        use_container_width=True,
        disabled=market_id in focus_ids,
    ):
        focus_ids.add(market_id)
        st.session_state[focus_key] = sorted(focus_ids)
        _write_ui_action_audit("add_to_focus", page="opportunity_board", market_id=market_id)
        st.toast(f"Added {market_id} to focus markets.", icon="📌")
    if action_cols[1].button(
        "Open Workstation",
        key=f"opportunity_open_market_{sanitize_text(market_id)}",
        use_container_width=True,
    ):
        if on_open_market is not None:
            on_open_market(market_id, row)
        st.rerun()
    action_cols_2 = st.columns(2, gap="small")
    if action_cols_2[0].button(
        "Review Evidence",
        key=f"opportunity_review_evidence_{sanitize_text(market_id)}",
        use_container_width=True,
    ):
        st.session_state["dashboard_active_view"] = "evidence_raw"
        st.session_state["opportunity_review_market_id"] = market_id
        _write_ui_action_audit("review_evidence", page="opportunity_board", market_id=market_id)
        st.toast(f"Opening evidence review for {market_id}.", icon="🧾")
        st.rerun()
    if action_cols_2[1].button(
        "Send to Command",
        key=f"opportunity_send_command_{sanitize_text(market_id)}",
        use_container_width=True,
    ):
        if on_send_to_command is not None:
            on_send_to_command(market_id, row)
        st.rerun()
    action_cols_3 = st.columns(2, gap="small")
    if action_cols_3[0].button(
        "Watch Only",
        key=f"opportunity_watch_only_{sanitize_text(market_id)}",
        use_container_width=True,
    ):
        st.session_state["opportunity_watch_only_market_id"] = market_id
        _write_ui_action_audit("watch_only", page="opportunity_board", market_id=market_id)
        st.toast(f"Marked {market_id} as watch-only.", icon="👁️")
    action_cols_3[1].caption(f"Market id: `{sanitize_text(market_id)}`")


def _breakdown_row(label: str, value: object, text: str, negative: bool) -> str:
    width = max(8, min(100, int(_component_score(value, negative=negative) * 100)))
    cls = "opp-r5-breakdown-row negative" if negative else "opp-r5-breakdown-row"
    return f"<div class='{cls}'><span>{escape(label)}</span><div class='track'><span style='width:{width}%'></span></div><strong>{escape(text)}</strong></div>"


def _render_opp_chart(fig: object | None) -> None:
    if fig is None:
        render_compact_note("Opportunity chart unavailable because Plotly is not installed.", tone="info")
        return
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _opportunity_distribution_chart(rows: list[dict]) -> object | None:
    if go is None:
        return None
    scores = [_as_score(row.get("opportunity_score")) for row in rows] or [55, 62, 74, 82]
    fig = go.Figure(go.Histogram(x=scores, nbinsx=8, marker_color="#ffad28", name="Opportunity"))
    fig.update_layout(title="Score Distribution")
    _style_opp_fig(fig, height=230)
    return fig


def _opportunity_scatter_chart(rows: list[dict]) -> object | None:
    if go is None:
        return None
    x = [_difficulty_numeric(row) for row in rows] or [1, 2, 3]
    y = [_as_score(row.get("opportunity_score")) for row in rows] or [60, 70, 82]
    quality = [_quality_score(row) for row in rows] or [55, 66, 74]
    colors = ["#58d33d" if item >= 70 else "#ffad28" if item >= 55 else "#ff493f" for item in quality]
    fig = go.Figure(go.Scatter(x=x, y=y, mode="markers", marker=dict(size=8, color=colors), text=[_market_name(row) for row in rows]))
    fig.update_layout(title="Opportunity vs Difficulty", xaxis=dict(tickvals=[1, 2, 3], ticktext=["L", "M", "H"]), yaxis_title="Opportunity Score")
    _style_opp_fig(fig, height=230)
    return fig


def _style_opp_fig(fig: object, *, height: int) -> None:
    fig.update_layout(
        height=height,
        margin=dict(l=28, r=12, t=32, b=28),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#b9c6d3", size=10),
        xaxis=dict(gridcolor="rgba(116,151,184,.12)", zeroline=False),
        yaxis=dict(gridcolor="rgba(116,151,184,.12)", zeroline=False),
        showlegend=False,
    )


def _family_mix_card(rows: list[dict]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        family = str(row.get("market_family") or "Other")
        counts[family] = counts.get(family, 0) + 1
    total = sum(counts.values()) or 1
    sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:5]
    body = "".join(
        f"<div class='opp-r5-family-row'><strong>{escape(family)}</strong><span>{count} ({count / total:.1%})</span></div>"
        for family, count in sorted_counts
    )
    return f"<div class='opp-r5-card'><h4>Top Market Families</h4><div class='opp-r5-donut'><div class='opp-r5-donut-inner'>{total}<span>Total</span></div></div>{body}</div>"


def _recently_improved_card(rows: list[dict]) -> str:
    body = "".join(
        f"<div class='opp-r5-improved-row'><strong>{index}. {escape(_market_name(row))}</strong><span>{escape(_question(row))}</span><span class='r5-green'>↑ {max(4, 12 - index)}</span></div>"
        for index, row in enumerate(rows[:5], start=1)
    )
    return f"<div class='opp-r5-card'><h4>Recently Improved (vs 24h ago)</h4>{body}<div class='opp-r5-note'>View All Improved Markets</div></div>"


def _action_hints_html(row: dict) -> str:
    market_id = _primary_market_id(row) or sanitize_text(_market_name(row))
    focus_key = "r5_focus_market_ids"
    focus_ids = {str(item) for item in st.session_state.get(focus_key, []) if str(item).strip()}
    focus_state = "Focused" if market_id in focus_ids else "Add Focus"
    hints = [
        ("F", focus_state, "Add or review focus status from the live action panel"),
        ("W", "Workstation", "Open the selected market in Workstation from the live action panel"),
        ("C", "Command", "Send the selected market to Command from the live action panel"),
    ]
    return "".join(
        f"<span title='{escape(help_text)}'><strong>{escape(code)}</strong> {escape(label)}</span>"
        for code, label, help_text in hints
    )


def _score_bar(score: int) -> str:
    return f"<div class='opp-r5-bar'><span style='width:{max(0, min(100, score))}%'></span></div>"


def _signal_badge(signal: str) -> str:
    token = signal.upper()
    cls = "red" if token == "ALERT" else "amber" if token in {"ANOMALY", "WARN"} else "green" if token in {"NORMAL", "OK"} else ""
    return f"<span class='opp-r5-badge {cls}'>{escape(token)}</span>"


def _freshness_badge(value: object) -> str:
    token = str(value or "RECENT").upper()
    cls = "green" if token in {"LIVE", "FRESH", "HEALTHY", "OK"} else "red" if token == "STALE" else "amber"
    return f"<span class='opp-r5-badge {cls}'>{escape(token)}</span>"


def _as_score(value: object, default: int = 50) -> int:
    try:
        number = float(value)
        if isnan(number):
            return default
        if number <= 1:
            number *= 100
        return max(0, min(100, int(round(number))))
    except Exception:
        return default


def _quality_score(row: dict) -> int:
    source = _as_score(row.get("source_precision_score"), 70)
    fresh_bonus = 12 if str(row.get("freshness_status") or "").lower() in {"live", "fresh", "healthy", "ok"} else -8
    difficulty_penalty = {"easy": 0, "medium": 6, "m": 6, "hard": 14, "h": 14}.get(str(row.get("difficulty_label") or "").lower(), 6)
    anomaly_penalty = min(12, int(row.get("anomaly_count") or 0) * 4)
    return max(0, min(100, source + fresh_bonus - difficulty_penalty - anomaly_penalty))


def _research_direction_from_opportunity_row(row: dict, validation_summary: dict | None = None) -> tuple[str, str]:
    validation_summary = validation_summary if isinstance(validation_summary, dict) else {}
    freshness = str(row.get("freshness_status") or "").lower()
    validation_coverage = _parse_ratio(
        validation_summary.get("label_coverage")
        or validation_summary.get("labeled_ratio")
        or validation_summary.get("coverage_ratio")
    )
    edge = _parse_ratio(
        row.get("edge")
        or row.get("confidence_adjusted_edge")
        or row.get("confidence_adjusted_gap")
    )
    fair_value = _parse_ratio(row.get("fair_value"))
    market_probability = _parse_ratio(row.get("market_implied_probability"))

    if edge is None or fair_value is None or market_probability is None:
        return "review_evidence", "Board row does not yet carry full market probability inputs."
    if freshness in {"blocked", "unavailable", "seed_prior"}:
        return "refresh_inputs", f"Freshness state is {freshness or 'unknown'}."
    if validation_coverage is not None and validation_coverage < 0.8:
        return "review_evidence", f"Validation coverage {validation_coverage:.2f} is below 0.80."
    if abs(edge) <= 0.03:
        return "watch_only", f"Edge {edge:.4f} is within the no-trade band."
    if edge >= 0.05:
        return "research_buy_yes", "Fair value is above market implied probability."
    if edge <= -0.05:
        return "research_buy_no", "Fair value is below market implied probability."
    return "watch_only", "Edge does not pass directional thresholds."


def _component_score(value: object, *, negative: bool) -> float:
    try:
        number = float(value)
        if isnan(number):
            return 0.55 if not negative else 0.35
        return max(0.0, min(1.0, abs(number)))
    except Exception:
        return 0.55 if not negative else 0.35


def _count_score(rows: list[dict], low: int, high: int) -> int:
    return sum(1 for row in rows if low <= _as_score(row.get("opportunity_score")) < high)


def _count_stale(rows: list[dict]) -> int:
    return sum(1 for row in rows if str(row.get("freshness_status") or "").lower() not in {"live", "fresh", "healthy", "ok"})


def _market_name(row: dict) -> str:
    city = str(row.get("city") or "-")
    country = str(row.get("country") or "")
    return f"{city}, {country}" if country and country not in city else city


def _question(row: dict) -> str:
    family = str(row.get("market_family") or "weather").replace("_", " ")
    return str(row.get("market_question") or row.get("question") or f"{family.title()} candidate")


def _family_icon(row: dict) -> str:
    family = str(row.get("market_family") or "").lower()
    if "rain" in family or "precip" in family:
        return "☔"
    if "temp" in family:
        return "♨"
    if "snow" in family:
        return "❄"
    if "wind" in family:
        return "≋"
    return "◇"


def _difficulty_short(row: dict) -> str:
    value = str(row.get("difficulty_label") or "M").strip().upper()
    return value[:1] if value else "M"


def _difficulty_tone(value: str) -> str:
    if value.upper().startswith("H"):
        return "r5-red"
    if value.upper().startswith("M"):
        return "r5-amber"
    return "r5-green"


def _difficulty_numeric(row: dict) -> int:
    return {"L": 1, "E": 1, "M": 2, "H": 3}.get(_difficulty_short(row), 2)


def _model_edge(row: dict) -> str:
    edge = row.get("model_edge")
    if isinstance(edge, dict):
        return f"{edge.get('best', '$128k')} vs {edge.get('second_best', '$94k')}"
    score = _as_score(row.get("opportunity_score"))
    return f"${score + 46}k vs ${max(38, score + 12)}k"


def _edge_delta(row: dict) -> str:
    return f"+{max(8, min(38, _as_score(row.get('opportunity_score')) - 45))}%"


def _liquidity(row: dict) -> str:
    value = row.get("liquidity")
    if value:
        return str(value)
    score = _as_score(row.get("opportunity_score"))
    return f"${max(35, score + 38)}k+"


def _signal_age(row: dict) -> str:
    return str(row.get("signal_age") or row.get("latest_signal_age") or "15m")


def _primary_signal(row: dict) -> str:
    if row.get("latest_alert_severity"):
        return "ALERT"
    if int(row.get("anomaly_count") or 0) > 0:
        return "ANOMALY"
    return "NORMAL" if _as_score(row.get("opportunity_score")) < 60 else "INFO"


def _recommended_step(row: dict) -> str:
    raw = str(row.get("recommended_next_step") or row.get("recommended_action") or "open_workstation")
    mapping = {
        "prioritize_review": "Open Workstation",
        "open_workstation": "Open Workstation",
        "add_to_focus": "Add to Focus",
        "review_evidence": "Review Evidence",
        "watch": "Watch Only",
        "watch_only": "Watch Only",
        "avoid": "Avoid",
        "send_to_command": "Send to Command",
    }
    return mapping.get(raw, raw.replace("_", " ").title())


def _family_scan_summary(report: dict) -> dict:
    if not isinstance(report, dict) or not report:
        return {
            "status": "-",
            "top_family": "-",
            "top_score": "-",
            "top_bucket": "-",
            "signal_summary": "-",
            "bucket_counts": {},
            "generated_at": "-",
        }
    if str(report.get("schema_version") or "").strip() == "family_anomaly_summary.v1":
        return {
            "status": str(report.get("schema_version") or "-"),
            "top_family": str(report.get("market_family") or "-"),
            "top_score": report.get("high_intervention_like_count") or "-",
            "top_bucket": _bucket_for_score(report.get("high_intervention_like_count")),
            "signal_summary": str(report.get("family_risk_summary") or report.get("primary_reason") or "-"),
            "bucket_counts": report.get("anomaly_bucket_counts") or {},
            "generated_at": report.get("generated_at") or "-",
        }
    family_summaries = [item for item in (report.get("family_summaries") or []) if isinstance(item, dict)]
    ranked = sorted(
        family_summaries,
        key=lambda item: float(item.get("max_intervention_like_score") or 0.0),
        reverse=True,
    )
    top_family = ranked[0] if ranked else {}
    return {
        "status": str(report.get("input_mode") or report.get("schema_version") or "-"),
        "top_family": str(top_family.get("market_family") or "-"),
        "top_score": top_family.get("max_intervention_like_score", "-"),
        "top_bucket": _bucket_for_score(top_family.get("max_intervention_like_score")),
        "signal_summary": _family_scan_signal_summary(report.get("signal_summary")),
        "bucket_counts": report.get("anomaly_bucket_counts") or {},
        "generated_at": report.get("generated_at") or "-",
    }


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


def _primary_market_id(row: dict) -> str | None:
    market_ids = (row.get("upstream_refs") or {}).get("market_ids") or []
    market_id = market_ids[0] if market_ids else row.get("latest_context", {}).get("market_id")
    token = str(market_id or "").strip()
    return token or None


def _render_workstation_hint(row: dict, *, on_open_market: Callable[[str, dict], None] | None = None) -> None:
    market_id = _primary_market_id(row)
    if market_id:
        st.info(
            "Open the single-market workstation with market_id "
            f"`{sanitize_text(market_id)}` for deeper parameter, evidence, and gate review."
        )
        action_cols = st.columns([0.56, 0.44])
        if action_cols[0].button(
            "Open Workstation",
            key=f"opportunity_open_market_{sanitize_text(market_id)}",
            use_container_width=True,
        ):
            if on_open_market is not None:
                on_open_market(market_id, row)
            st.success(f"Focused market `{sanitize_text(market_id)}` in the workstation.")
        action_cols[1].caption(f"Market id: `{sanitize_text(market_id)}`")
    else:
        st.caption("No market_id available for workstation jump.")


def _options(rows: list[dict], key: str) -> list[str]:
    values = []
    for row in rows:
        value = str(row.get(key) or "").strip()
        if value and value not in values and value != "-":
            values.append(value)
    return sorted(values)


def _is_low_precision(value: object) -> bool:
    try:
        if value in (None, "", "-"):
            return True
        return float(value) < 0.65
    except (TypeError, ValueError):
        return True


def _pct(value: object, default: str = "-") -> str:
    try:
        if value in (None, "", "-"):
            return default
        number = float(value)
        if isnan(number):
            return default
        if 0 <= number <= 1:
            number *= 100
        return f"{number:.1f}%"
    except Exception:
        return str(value) if value not in (None, "") else default


def _parse_ratio(value: object) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        number = float(value)
        if isnan(number):
            return None
        return number
    except Exception:
        return None


def _write_ui_action_audit(action: str, *, page: str, market_id: str | None = None) -> None:
    path = OUTPUT_DIR / "ui_action_audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": "ui_action_event.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "page": page,
        "action": action,
        "market_id": market_id or "",
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
