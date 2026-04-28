from __future__ import annotations

import json
from datetime import datetime
from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Callable

from weather_dashboard.settings import OPERATIONS_MONITOR_VIEW_JSON
from weather_dashboard.ui.compact_panel import (
    fmt_value,
    render_compact_note,
    render_legend_card,
    sanitize_text,
    with_data_quality,
)


def render_operations_monitor_page(
    view: dict | None = None,
    *,
    on_open_market: Callable[[str, dict], None] | None = None,
    on_send_to_command: Callable[[str, dict], None] | None = None,
) -> None:
    import streamlit as st
    from streamlit_autorefresh import st_autorefresh

    refresh_tick = st_autorefresh(interval=15_000, key="operations_monitor_autorefresh")
    now_local = datetime.now().astimezone()
    view = view or _load_operations_monitor_view()
    if not view:
        render_compact_note(
            "Operations monitor snapshot not found yet. Run `weather-comparison-engine build-operations-monitor` to generate it.",
            tone="warning",
        )
        return

    global_summary = view.get("global_summary") or {}
    focus_markets = [item for item in (view.get("focus_markets") or []) if isinstance(item, dict)]
    cards = [item for item in (view.get("market_monitor_cards") or []) if isinstance(item, dict)]
    system_health = view.get("system_health") or {}
    ops_alerts = [item for item in (view.get("ops_alerts") or []) if isinstance(item, dict)]
    selected_detail = view.get("selected_market_quick_detail") or {}

    control_cols = st.columns([1, 1, 1, 1.7, 1.4], gap="small")
    scope_filter = control_cols[0].selectbox("Scope", ["All Markets", "Focus Markets", "Non-focus Markets"], key="ops_live_scope_filter")
    status_options = ["All", *sorted({str(card.get("primary_state") or "NORMAL").upper() for card in cards})]
    status_filter = control_cols[1].selectbox("Status", status_options, key="ops_live_status_filter")
    family_options = ["All", *sorted({str(card.get("market_family") or "-") for card in cards if card.get("market_family")})]
    family_filter = control_cols[2].selectbox("Family", family_options, key="ops_live_family_filter")
    search_filter = control_cols[3].text_input("Search", placeholder="Search market, city, question...", key="ops_live_search_filter")
    focus_ids = {str(item.get("market_id") or "") for item in focus_markets}
    filtered_cards = []
    for card in cards:
        market_id = str(card.get("market_id") or "")
        hay = " ".join(
            str(card.get(field) or "")
            for field in ["market_id", "city", "market_family", "market_question_short", "recommended_action"]
        ).lower()
        if scope_filter == "Focus Markets" and market_id not in focus_ids:
            continue
        if scope_filter == "Non-focus Markets" and market_id in focus_ids:
            continue
        if status_filter != "All" and str(card.get("primary_state") or "").upper() != status_filter:
            continue
        if family_filter != "All" and str(card.get("market_family") or "-") != family_filter:
            continue
        if search_filter.strip() and search_filter.lower().strip() not in hay:
            continue
        filtered_cards.append(card)

    card_choices = [
        f"{card.get('city') or card.get('market_id')} · {card.get('market_family') or '-'} · {card.get('market_id')}"
        for card in filtered_cards
    ]
    if card_choices:
        selected_choice = control_cols[4].selectbox("Selected Market", card_choices, key="ops_live_selected_market")
        st.session_state["operations_monitor_selected_market_id"] = selected_choice.rsplit(" · ", 1)[-1]

    selected_market_id = (
        str(st.session_state.get("operations_monitor_selected_market_id") or "").strip()
        or str((view.get("view_context") or {}).get("selected_market_id") or "").strip()
        or str(selected_detail.get("market_id") or "").strip()
        or (str(filtered_cards[0].get("market_id") or "") if filtered_cards else (str(cards[0].get("market_id") or "") if cards else ""))
    )
    selected_card = _find_card(cards, selected_market_id)
    quick_detail = _resolve_quick_detail(view, selected_market_id=selected_market_id, selected_card=selected_card)

    _render_theme()
    _render_poly_r4_cockpit(
        global_summary=global_summary,
        focus_markets=focus_markets,
        cards=filtered_cards,
        system_health=system_health,
        ops_alerts=ops_alerts,
        quick_detail=quick_detail,
        now_local=now_local,
        on_open_market=on_open_market,
        on_send_to_command=on_send_to_command,
    )
    return
    _render_ops_toolbar(global_summary=global_summary, quick_detail=quick_detail, system_health=system_health, now_local=now_local)
    _render_header(
        global_summary=global_summary,
        quick_detail=quick_detail,
        system_health=system_health,
        now_local=now_local,
        refresh_tick=refresh_tick,
    )
    _render_status_strip(global_summary=global_summary, system_health=system_health)

    left_col, center_col, right_col = st.columns([0.88, 1.52, 0.84])

    with left_col:
        _render_panel(
            "Scan / Queue / Gate",
            "Scanner health and runtime boundary",
            [
                (
                    "Scanner Status",
                    with_data_quality(
                        (system_health.get("scanner_health") or {}).get("status"),
                        "bad",
                    )
                    if str((system_health.get("scanner_health") or {}).get("status") or "").lower() not in {"healthy", "ready", "ok"}
                    else (system_health.get("scanner_health") or {}).get("status"),
                ),
                ("Scanned Markets", (system_health.get("scanner_health") or {}).get("scanned_markets")),
                ("Fresh Markets", (system_health.get("scanner_health") or {}).get("fresh_markets")),
                ("Stale Markets", (system_health.get("scanner_health") or {}).get("stale_markets")),
                ("Alert Queue", (system_health.get("queue_health") or {}).get("accepted_count")),
                ("Gate Blocked", global_summary.get("gate_blocked_markets")),
                (
                    "Source Health",
                    with_data_quality(
                        (system_health.get("source_health") or {}).get("overall_status"),
                        "bad",
                    )
                    if str((system_health.get("source_health") or {}).get("overall_status") or "").lower() not in {"healthy", "fresh", "ok"}
                    else (system_health.get("source_health") or {}).get("overall_status"),
                ),
            ],
        )
        _render_panel(
            "Focus Gate",
            "Selected market boundary",
            [
                ("Selected Market", quick_detail.get("market_id")),
                ("Recommended Action", quick_detail.get("recommended_operator_action")),
                ("Execution Boundary", quick_detail.get("execution_boundary")),
                ("Can Execute", (quick_detail.get("gate_advisory_panel") or {}).get("can_execute")),
            ],
        )
        _render_panel(
            "Queue Details",
            "Alert routing state",
            [
                ("Accepted", (system_health.get("queue_health") or {}).get("accepted_count")),
                ("Suppressed", (system_health.get("queue_health") or {}).get("suppressed_count")),
                ("Pending", (system_health.get("queue_health") or {}).get("pending_count")),
                ("Cooldown", "active" if ops_alerts else "idle"),
            ],
        )

    with center_col:
        _render_section_title("Focus Markets")
        if focus_markets:
            requires_action, watch_list = _split_focus_markets(focus_markets)
            focus_display: list[dict] = []
            for focus in requires_action[:2]:
                focus_display.append({**focus, "focus_group": "Requires Action"})
            for focus in watch_list[:2]:
                focus_display.append({**focus, "focus_group": "Watch"})
            if not focus_display:
                focus_display = [{**focus, "focus_group": "Focus"} for focus in focus_markets[:4]]
            if focus_display:
                focus_cols = st.columns(len(focus_display[:4]))
                for index, focus in enumerate(focus_display[:4]):
                    with focus_cols[index % len(focus_cols)]:
                        _render_focus_card(
                            focus,
                            on_open_market=on_open_market,
                            index=index,
                            key_suffix=f"focus_{index}",
                        )
        else:
            render_compact_note("No focus markets yet.", tone="info")

        _render_section_title("Market Radar")
        if cards:
            visible_cards = cards[:6]
            for row_start in range(0, len(visible_cards), 3):
                row_cards = visible_cards[row_start : row_start + 3]
                row_cols = st.columns(3)
                for col_index, card in enumerate(row_cards):
                    with row_cols[col_index]:
                        _render_market_card(
                            card,
                            on_open_market=on_open_market,
                            key_suffix=f"radar_{row_start + col_index}",
                        )
            if len(cards) > len(visible_cards):
                with st.expander(f"More markets (+{len(cards) - len(visible_cards)})", expanded=False):
                    for row_start in range(len(visible_cards), len(cards), 3):
                        row_cards = cards[row_start : row_start + 3]
                        row_cols = st.columns(3)
                        for col_index, card in enumerate(row_cards):
                            with row_cols[col_index]:
                                _render_market_card(
                                    card,
                                    on_open_market=on_open_market,
                                    key_suffix=f"more_{row_start + col_index}",
                                )
        else:
            render_compact_note("No market monitor cards yet.", tone="info")

        _render_section_title("Selected Market Snapshot")
        _render_selected_market_drawer(quick_detail, on_open_market=on_open_market)

    with right_col:
        _render_panel(
            "Operator Summary",
            "Recommended next step",
            [
                ("Summary", _operator_summary_line(global_summary, focus_markets, ops_alerts)),
                ("Selected Market", quick_detail.get("market_id")),
                ("Recommended Action", quick_detail.get("recommended_operator_action")),
                ("Fresh Ratio", global_summary.get("fresh_ratio")),
                ("Scanner Status", (system_health.get("scanner_health") or {}).get("status")),
            ],
        )
        _render_status_list_panel(
            "Source Health",
            "stale / unavailable / fallback / precision",
            [
                ("Stale", ((system_health.get("source_health") or {}).get("counts") or {}).get("stale"), "warning"),
                ("Unavailable", ((system_health.get("source_health") or {}).get("counts") or {}).get("unavailable"), "critical"),
                ("Fallback", ((system_health.get("source_health") or {}).get("counts") or {}).get("fallback"), "neutral"),
                ("Precision", ((system_health.get("source_health") or {}).get("counts") or {}).get("precision_degrade"), "warning"),
            ],
        )
        _render_status_list_panel(
            "Queue Summary",
            "pending / sent / ack / suppress",
            [
                ("Pending", (system_health.get("queue_health") or {}).get("pending_count"), "warning"),
                ("Sent", (system_health.get("queue_health") or {}).get("sent_count"), "ok"),
                ("Acked", (system_health.get("queue_health") or {}).get("acked_count"), "ok"),
                ("Suppressed", (system_health.get("queue_health") or {}).get("suppressed_count"), "neutral"),
            ],
        )
        _render_panel(
            "Latest Ops Alerts",
            "System-level conditions",
            [
                ("Ops Alerts", len(ops_alerts)),
                ("Scanner ETA", (system_health.get("scanner_health") or {}).get("next_scan_eta")),
                ("Alert Queue", (system_health.get("queue_health") or {}).get("accepted_count")),
            ],
        )
        if ops_alerts:
            for alert in ops_alerts[:4]:
                _render_alert_card(alert)
        else:
            render_compact_note("No current ops alerts.", tone="ok")


def _render_theme() -> None:
    import streamlit as st

    st.html(
        dedent(
            """
        <style>
        :root {
            --ops-bg: #020305;
            --ops-bg-2: #070a0f;
            --ops-surface: #0d1117;
            --ops-surface-2: #11161d;
            --ops-surface-3: #161c24;
            --ops-border: rgba(255, 255, 255, 0.12);
            --ops-border-strong: rgba(106, 161, 239, 0.38);
            --ops-text: #dce7ef;
            --ops-text-muted: #a7b5c1;
            --ops-text-dim: #7f8b96;
            --ops-accent: #4f8fe6;
            --ops-accent-2: #3f6fa8;
            --ops-good: #69d39a;
            --ops-warn: #d7ab57;
            --ops-bad: #d96d67;
            --compact-panel-title-color: #dce7ef;
            --compact-panel-subtitle-color: #93a0aa;
            --compact-panel-border-color: rgba(255, 255, 255, 0.12);
            --compact-panel-bg: rgba(12, 15, 20, 0.98);
            --compact-card-title-color: #b5bec7;
            --compact-metric-border-color: rgba(255, 255, 255, 0.12);
            --compact-metric-bg: rgba(14, 18, 24, 0.98);
            --compact-row-border-color: rgba(255, 255, 255, 0.12);
            --compact-row-bg: rgba(12, 15, 20, 0.98);
            --compact-note-border-color: rgba(255, 255, 255, 0.12);
            --compact-note-bg: rgba(12, 15, 20, 0.98);
            --compact-note-color: #a3adb7;
            --compact-note-warning-border-color: rgba(215, 171, 87, 0.24);
            --compact-note-warning-bg: rgba(29, 24, 16, 0.96);
            --compact-note-warning-color: #d9b96d;
            --compact-note-critical-border-color: rgba(217, 109, 103, 0.24);
            --compact-note-critical-bg: rgba(31, 19, 19, 0.96);
            --compact-note-critical-color: #de8f8a;
            --compact-note-ok-border-color: rgba(105, 211, 154, 0.22);
            --compact-note-ok-bg: rgba(16, 25, 20, 0.96);
            --compact-note-ok-color: #8fe2b0;
            --compact-label-color: #a3adb7;
            --compact-value-color: #dce7ef;
            --compact-divider-color: rgba(255, 255, 255, 0.12);
            --compact-ok-color: #8fe2b0;
            --compact-warning-color: #d9b96d;
            --compact-critical-color: #de8f8a;
            --compact-neutral-color: #edf2f6;
            --compact-muted-color: #8f9aa5;
            --compact-ok-border-color: rgba(105, 211, 154, 0.22);
            --compact-ok-bg: rgba(16, 25, 20, 0.92);
            --compact-warning-border-color: rgba(215, 171, 87, 0.24);
            --compact-warning-bg: rgba(29, 24, 16, 0.92);
            --compact-critical-border-color: rgba(217, 109, 103, 0.24);
            --compact-critical-bg: rgba(31, 19, 19, 0.92);
        }
        .stApp {
            background:
                linear-gradient(180deg, var(--ops-bg) 0%, var(--ops-bg-2) 42%, #090c10 100%);
            color: var(--ops-text);
            font-family: "Avenir Next", "Avenir", "SF Pro Text", "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif;
        }
        .stApp,
        .stApp [data-testid="stAppViewContainer"],
        .stApp [data-testid="stAppViewContainer"] * {
            color: var(--ops-text);
        }
        .block-container {
            max-width: none;
            padding: 0.42rem 0.62rem 0.5rem;
        }
        .command-app-header {
            display: none !important;
        }
        .ops-header {
            display: flex;
            justify-content: space-between;
            gap: 0.78rem;
            padding: 0.5rem 0.68rem;
            margin: 0.02rem 0 0.24rem;
            border-radius: 0.72rem;
            background: linear-gradient(180deg, rgba(15, 18, 24, 0.99), rgba(9, 12, 16, 0.99));
            border: 1px solid var(--ops-border);
            box-shadow: none;
        }
        .ops-toolbar {
            display: grid;
            grid-template-columns: minmax(10rem, 1.02fr) minmax(12rem, 1.42fr) minmax(8rem, 0.72fr) auto auto;
            align-items: center;
            gap: 0.45rem;
            padding: 0.35rem 0.62rem;
            margin: 0 0 0.28rem;
            border-radius: 0.72rem;
            background: linear-gradient(180deg, rgba(15, 18, 24, 0.99), rgba(9, 12, 16, 0.99));
            border: 1px solid var(--ops-border);
            box-shadow: none;
        }
        .ops-toolbar__field .stSelectbox,
        .ops-toolbar__field .stTextInput {
            margin: 0;
        }
        .ops-toolbar__field label {
            color: #93a0aa !important;
            font-size: 0.43rem !important;
            font-weight: 900 !important;
            letter-spacing: 0.15em !important;
            text-transform: uppercase !important;
            margin-bottom: 0.1rem !important;
        }
        .ops-toolbar__field input,
        .ops-toolbar__field textarea,
        .ops-toolbar__field div[data-baseweb="select"],
        .ops-toolbar__field div[data-baseweb="select"] > div,
        .ops-toolbar__field div[data-baseweb="select"] input {
            background: rgba(12, 15, 20, 0.98) !important;
            background-color: rgba(12, 15, 20, 0.98) !important;
            border-color: rgba(255, 255, 255, 0.12) !important;
            color: #f7fbff !important;
            min-height: 2.02rem !important;
        }
        .ops-toolbar__field div[data-baseweb="select"] * {
            color: #f7fbff !important;
        }
        .ops-toolbar__field div[data-baseweb="select"] svg {
            fill: #c9d4de !important;
        }
        .ops-toolbar__badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.26rem 0.5rem;
            border-radius: 999px;
            border: 1px solid rgba(79, 143, 230, 0.28);
            background: rgba(12, 15, 20, 0.98);
            color: #d8e6f7;
            font-size: 0.54rem;
            font-weight: 900;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .ops-toolbar__clock {
            color: #f7fbff;
            font-size: 0.58rem;
            font-weight: 900;
            line-height: 1.08;
            text-align: right;
        }
        .ops-toolbar__alert {
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2.2rem;
            height: 2.02rem;
            border-radius: 0.58rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(12, 15, 20, 0.98);
            color: #edf2f6;
            font-size: 0.88rem;
        }
        .ops-toolbar__alert::after {
            content: attr(data-count);
            position: absolute;
            top: -0.08rem;
            right: -0.06rem;
            min-width: 0.8rem;
            height: 0.8rem;
            padding: 0 0.18rem;
            border-radius: 999px;
            background: #d96d67;
            color: #fff;
            font-size: 0.42rem;
            font-weight: 900;
            line-height: 0.8rem;
            text-align: center;
        }
        .ops-header__eyebrow {
            color: #d3e2f7;
            font-size: 0.64rem;
            font-weight: 850;
            letter-spacing: 0.17em;
            text-transform: uppercase;
        }
        .ops-header__title {
            margin-top: 0.12rem;
            color: var(--ops-text);
            font-size: 1rem;
            font-weight: 900;
            letter-spacing: 0.01em;
            line-height: 1.06;
        }
        .ops-header__subtitle {
            margin-top: 0.1rem;
            color: var(--ops-text-muted);
            font-size: 0.66rem;
            line-height: 1.26;
            max-width: 66rem;
        }
        .ops-header__right {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            align-content: flex-start;
            gap: 0.42rem;
            min-width: 16rem;
        }
        .ops-live {
            display: flex;
            align-items: center;
            gap: 0.42rem;
            margin-top: 0.16rem;
            color: var(--ops-text-muted);
            font-size: 0.56rem;
            font-weight: 850;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }
        .ops-live__dot {
            width: 0.48rem;
            height: 0.48rem;
            border-radius: 999px;
            background: var(--ops-good);
            box-shadow: 0 0 0 0.16rem rgba(105, 211, 154, 0.15);
            animation: opsPulse 1.8s ease-in-out infinite;
            flex: 0 0 auto;
        }
        .ops-live__hint {
            color: #c7d0d8;
        }
        @keyframes opsPulse {
            0% { transform: scale(0.92); opacity: 0.72; }
            50% { transform: scale(1.08); opacity: 1; }
            100% { transform: scale(0.92); opacity: 0.72; }
        }
        .ops-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.28rem 0.56rem;
            border-radius: 0.5rem;
            border: 1px solid var(--ops-border);
            background: rgba(12, 15, 20, 0.98);
            color: #f2f6fa;
            font-size: 0.62rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .ops-chip--blue { border-color: rgba(79, 143, 230, 0.32); color: #d8e6f7; }
        .ops-chip--emerald { border-color: rgba(105, 211, 154, 0.26); color: #c8f0d8; }
        .ops-chip--amber { border-color: rgba(215, 171, 87, 0.28); color: #f3dfaf; }
        .ops-status-strip {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 0.42rem;
            margin: 0 0 0.42rem;
        }
        .ops-status-tile {
            padding: 0.34rem 0.42rem;
            border-radius: 0.5rem;
            background: linear-gradient(180deg, rgba(15, 18, 24, 0.99), rgba(9, 12, 16, 0.99));
            border: 1px solid var(--ops-border);
            box-shadow: none;
        }
        .ops-status-tile__label {
            color: var(--ops-text-dim);
            font-size: 0.48rem;
            font-weight: 850;
            letter-spacing: 0.15em;
            text-transform: uppercase;
        }
        .ops-status-tile__value {
            margin-top: 0.06rem;
            color: var(--ops-text);
            font-size: 0.88rem;
            font-weight: 900;
            line-height: 1.08;
        }
        .ops-section-title {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin: 0.08rem 0 0.18rem;
            color: #edf2f6;
            font-size: 0.64rem;
            font-weight: 900;
            letter-spacing: 0.18em;
            text-transform: uppercase;
        }
        .ops-section-title::before {
            content: "";
            width: 0.38rem;
            height: 0.38rem;
            border-radius: 0.08rem;
            background: rgba(79, 143, 230, 0.85);
            box-shadow: 0 0 0 0.12rem rgba(79, 143, 230, 0.18);
            flex: 0 0 auto;
        }
        .ops-section-title::after {
            content: "";
            flex: 0 0 2.8rem;
            height: 1px;
            background: linear-gradient(90deg, rgba(79, 143, 230, 0.38), rgba(255, 255, 255, 0.06));
        }
        .ops-card {
            margin: 0 0 0.28rem;
            padding: 0.4rem 0.46rem;
            border-radius: 0.6rem;
            border: 1px solid var(--ops-border);
            background: linear-gradient(180deg, rgba(15, 18, 24, 0.99), rgba(9, 12, 16, 0.99));
            box-shadow: none;
        }
        .ops-card--selected {
            border-color: rgba(79, 143, 230, 0.42);
            box-shadow: 0 0 0 1px rgba(79, 143, 230, 0.10) inset;
        }
        .ops-card--live { border-color: rgba(105, 211, 154, 0.22); }
        .ops-card--stale { border-color: rgba(215, 171, 87, 0.26); }
        .ops-card--anom { border-color: rgba(215, 171, 87, 0.34); }
        .ops-card--alert { border-color: rgba(217, 109, 103, 0.38); }
        .ops-card--blocked { border-color: rgba(217, 109, 103, 0.44); }
        .ops-card--focus-strong {
            border-color: rgba(217, 109, 103, 0.56);
            box-shadow: 0 0 0 1px rgba(217, 109, 103, 0.10) inset;
        }
        .ops-card--focus-soft {
            border-color: rgba(215, 171, 87, 0.28);
        }
        .ops-card__head {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 0.75rem;
            margin-bottom: 0.34rem;
        }
        .ops-card__title {
            color: var(--ops-text);
            font-size: 0.82rem;
            font-weight: 900;
            line-height: 1.16;
        }
        .ops-rank-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 1rem;
            height: 1rem;
            margin-right: 0.28rem;
            border-radius: 0.24rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(18, 24, 33, 0.98);
            color: #f7fbff;
            font-size: 0.48rem;
            font-weight: 950;
            letter-spacing: 0.08em;
            vertical-align: middle;
        }
        .ops-card__meta {
            color: var(--ops-text-dim);
            font-size: 0.52rem;
            font-weight: 820;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .ops-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.24rem;
            margin: 0.16rem 0 0.26rem;
        }
        .ops-chip-mini {
            display: inline-flex;
            align-items: center;
            padding: 0.12rem 0.28rem;
            border-radius: 0.42rem;
            border: 1px solid var(--ops-border);
            background: rgba(12, 15, 20, 0.98);
            color: #e0e8f1;
            font-size: 0.5rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .ops-state-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.2rem;
            margin: 0.06rem 0 0.24rem;
        }
        .ops-state-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.22rem;
            padding: 0.1rem 0.26rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            font-size: 0.46rem;
            font-weight: 900;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .ops-state-pill--live { border-color: rgba(105, 211, 154, 0.22); color: #8fe2b0; background: rgba(16, 25, 20, 0.92); }
        .ops-state-pill--stale { border-color: rgba(215, 171, 87, 0.22); color: #d9b96d; background: rgba(29, 24, 16, 0.92); }
        .ops-state-pill--anom { border-color: rgba(215, 171, 87, 0.26); color: #e6c67c; background: rgba(34, 29, 16, 0.92); }
        .ops-state-pill--alert { border-color: rgba(217, 109, 103, 0.26); color: #e79a95; background: rgba(31, 19, 19, 0.92); }
        .ops-state-pill--blocked { border-color: rgba(217, 109, 103, 0.28); color: #de8f8a; background: rgba(31, 19, 19, 0.92); }
        .ops-state-pill--muted { border-color: rgba(255, 255, 255, 0.08); color: #8f9aa5; background: rgba(16, 20, 27, 0.92); }
        .ops-row {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 0.7rem;
            padding: 0.06rem 0;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }
        .ops-row:first-of-type { border-top: 0; padding-top: 0; }
        .ops-row__label {
            flex: 0 0 42%;
            color: var(--ops-text-dim);
            font-size: 0.5rem;
            font-weight: 850;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .ops-row__value {
            flex: 1 1 auto;
            color: var(--ops-text);
            font-size: 0.68rem;
            font-weight: 820;
            line-height: 1.12;
            text-align: right;
            word-break: break-word;
        }
        .ops-next-action {
            margin-top: 0.22rem;
            padding: 0.24rem 0.3rem;
            border-radius: 0.58rem;
            border: 1px solid rgba(79, 143, 230, 0.28);
            background: rgba(11, 18, 29, 0.96);
        }
        .ops-next-action__label {
            color: #8ebcff;
            font-size: 0.44rem;
            font-weight: 950;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }
        .ops-next-action__value {
            margin-top: 0.05rem;
            color: #f7fbff;
            font-size: 0.7rem;
            font-weight: 900;
            line-height: 1.12;
        }
        .ops-card-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.35rem;
            margin-top: 0.22rem;
            padding-top: 0.18rem;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }
        .ops-card-footer__label {
            color: #8ebcff;
            font-size: 0.42rem;
            font-weight: 950;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }
        .ops-card-footer__value {
            color: #8f9aa5;
            font-size: 0.48rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            text-align: right;
        }
        .ops-summary-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.24rem;
            margin: 0.08rem 0 0.18rem;
        }
        .ops-summary-cell {
            padding: 0.26rem 0.32rem;
            border-radius: 0.56rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(12, 15, 20, 0.98);
        }
        .ops-summary-cell__label {
            color: #aab4be;
            font-size: 0.44rem;
            font-weight: 900;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .ops-summary-cell__value {
            margin-top: 0.04rem;
            color: #f7fbff;
            font-size: 0.68rem;
            font-weight: 900;
            line-height: 1.1;
        }
        .ops-matrix-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.2rem;
        }
        .ops-matrix-cell {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.35rem;
            padding: 0.22rem 0.28rem;
            border-radius: 0.56rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(12, 15, 20, 0.98);
        }
        .ops-matrix-cell__label {
            color: #cfd8e2;
            font-size: 0.46rem;
            font-weight: 900;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }
        .ops-matrix-cell__value {
            color: #f7fbff;
            font-size: 0.68rem;
            font-weight: 900;
            font-variant-numeric: tabular-nums;
        }
        .ops-matrix-cell--ok { border-color: rgba(105, 211, 154, 0.22); }
        .ops-matrix-cell--warning { border-color: rgba(215, 171, 87, 0.24); }
        .ops-matrix-cell--critical { border-color: rgba(217, 109, 103, 0.28); }
        .ops-matrix-cell--neutral { border-color: rgba(79, 143, 230, 0.16); }
        .ops-status-list {
            display: flex;
            flex-direction: column;
            gap: 0.18rem;
        }
        .ops-status-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.38rem;
            padding: 0.2rem 0.26rem;
            border-radius: 0.46rem;
            border: 1px solid rgba(255, 255, 255, 0.09);
            background: rgba(12, 15, 20, 0.98);
        }
        .ops-status-item__left {
            display: flex;
            align-items: center;
            gap: 0.28rem;
            min-width: 0;
        }
        .ops-status-item__dot {
            width: 0.38rem;
            height: 0.38rem;
            border-radius: 999px;
            flex: 0 0 auto;
        }
        .ops-status-item__label {
            color: #d7e2eb;
            font-size: 0.48rem;
            font-weight: 900;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .ops-status-item__value {
            color: #f7fbff;
            font-size: 0.64rem;
            font-weight: 900;
            font-variant-numeric: tabular-nums;
            text-align: right;
        }
        .ops-status-item--ok .ops-status-item__dot { background: rgba(105, 211, 154, 0.95); box-shadow: 0 0 0 0.1rem rgba(105, 211, 154, 0.12); }
        .ops-status-item--warning .ops-status-item__dot { background: rgba(215, 171, 87, 0.95); box-shadow: 0 0 0 0.1rem rgba(215, 171, 87, 0.12); }
        .ops-status-item--critical .ops-status-item__dot { background: rgba(217, 109, 103, 0.95); box-shadow: 0 0 0 0.1rem rgba(217, 109, 103, 0.12); }
        .ops-status-item--neutral .ops-status-item__dot { background: rgba(79, 143, 230, 0.95); box-shadow: 0 0 0 0.1rem rgba(79, 143, 230, 0.10); }
        .ops-drawer {
            margin-top: 0.35rem;
            padding: 0.52rem 0.58rem;
            border-radius: 0.66rem;
            border: 1px solid var(--ops-border);
            background: linear-gradient(180deg, rgba(15, 18, 24, 0.99), rgba(9, 12, 16, 0.99));
            box-shadow: none;
        }
        .ops-drawer__title {
            margin-bottom: 0.38rem;
            color: #edf2f6;
            font-size: 0.66rem;
            font-weight: 900;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }
        .ops-button-row {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.42rem;
            margin-top: 0.45rem;
        }
        .ops-note {
            color: var(--ops-text-muted);
            font-size: 0.8rem;
            line-height: 1.36;
        }
        div[data-testid="stButton"] > button {
            width: 100%;
            border-radius: 0.52rem;
            border: 1px solid rgba(255, 255, 255, 0.09);
            background: linear-gradient(180deg, rgba(22, 27, 35, 0.98), rgba(15, 19, 25, 0.98));
            color: #edf2f6;
            font-size: 0.72rem;
            font-weight: 800;
            line-height: 1;
            padding: 0.5rem 0.72rem;
        }
        .stButton > button,
        .stButton button,
        div[data-testid="stButton"] > button {
            background: linear-gradient(180deg, rgba(22, 27, 35, 0.98), rgba(15, 19, 25, 0.98)) !important;
            background-color: rgba(15, 19, 25, 0.98) !important;
            color: #edf2f6 !important;
            border: 1px solid rgba(255, 255, 255, 0.09) !important;
            box-shadow: none !important;
        }
        div[data-testid="stButton"] > button:hover {
            border-color: rgba(79, 143, 230, 0.45);
            background: linear-gradient(180deg, rgba(26, 32, 42, 0.98), rgba(17, 21, 28, 0.98));
            color: #ffffff;
        }
        .stButton > button:hover,
        .stButton button:hover {
            background: linear-gradient(180deg, rgba(26, 32, 42, 0.98), rgba(17, 21, 28, 0.98)) !important;
            color: #ffffff !important;
            border-color: rgba(79, 143, 230, 0.45) !important;
        }
        div[data-testid="stButton"] > button:focus {
            box-shadow: 0 0 0 0.08rem rgba(79, 143, 230, 0.18);
            border-color: rgba(79, 143, 230, 0.54);
        }
        @media (max-width: 1180px) {
            .ops-toolbar {
                grid-template-columns: 1fr 1.2fr;
            }
            .ops-status-strip {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
            .ops-header {
                flex-direction: column;
            }
        }
        @media (max-width: 860px) {
            .ops-status-strip {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        </style>
        """
        ).lstrip()
    )


def _poly_state_class(state: object) -> str:
    normalized = str(state or "LIVE").upper()
    if normalized in {"ALERT", "BLOCKED"}:
        return "alert"
    if normalized == "ANOM":
        return "anom"
    if normalized == "STALE":
        return "stale"
    if normalized == "NORMAL":
        return "normal"
    return "live"


def _poly_gate_class(value: object) -> str:
    text = str(value).lower()
    if text in {"true", "yes", "allow", "allowed", "1"}:
        return "poly-good"
    if text in {"false", "no", "blocked", "0"}:
        return "poly-bad"
    return "poly-warn"


def _poly_percent(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fmt_value(value)
    if number <= 1:
        number *= 100
    return f"{number:.1f}%"


def _poly_action_label(value: object) -> str:
    text = str(value or "").strip().lower()
    return {
        "refresh_pipeline_inputs": "Review evidence",
        "review_monitoring": "Check gate reason",
        "prioritize_review": "Review evidence",
        "open_workstation": "Open workstation",
        "watch": "Watch",
        "avoid": "Hold / avoid",
    }.get(text, fmt_value(value))


def _poly_reason_label(focus: dict) -> str:
    reason = str(focus.get("focus_reason") or focus.get("primary_state_reason") or "").strip()
    if focus.get("is_selected_market"):
        return "SELECTED + GATE BLOCKED" if focus.get("can_execute") is False else "SELECTED"
    reason_lower = reason.lower()
    if "opp=" in reason_lower:
        return "HIGH OPPORTUNITY"
    if "block=none" in reason_lower:
        return "WATCH"
    return fmt_value(reason or "-")


def _poly_city_from_question(question: object) -> str:
    text = str(question or "").strip()
    if not text:
        return "-"
    known_cities = (
        "Shanghai",
        "Ankara",
        "Buenos Aires",
        "Chicago",
        "London",
        "Miami",
        "New York",
        "Seoul",
        "Tokyo",
        "Houston",
        "Sydney",
        "Berlin",
        "Paris",
        "Toronto",
        "Boston",
        "Dubai",
        "Mexico City",
    )
    lowered = text.lower()
    for city in known_cities:
        if city.lower() in lowered:
            return city
    return "-"


def _poly_derive_primary_state(item: dict) -> str:
    explicit = str(item.get("primary_state") or "").strip().upper()
    if explicit:
        return explicit
    severity = str(item.get("latest_alert_severity") or "").strip().lower()
    if severity in {"red", "critical", "alert"}:
        return "ALERT"
    anomaly_score = item.get("latest_anomaly_score")
    try:
        if anomaly_score is not None and float(anomaly_score) >= 0.5:
            return "ANOM"
    except (TypeError, ValueError):
        pass
    freshness = str(item.get("freshness_status") or "").strip().lower()
    if freshness in {"stale", "unavailable", "blocked"}:
        return "STALE"
    if item.get("selected_market") or item.get("is_selected_market"):
        return "BLOCKED" if item.get("can_execute") is False else "LIVE"
    return "NORMAL"


def _poly_enrich_focus_markets(focus_markets: list[dict], cards: list[dict]) -> list[dict]:
    cards_by_id = {str(card.get("market_id") or ""): card for card in cards}
    enriched: list[dict] = []
    for focus in focus_markets:
        market_id = str(focus.get("market_id") or "")
        if market_id and market_id not in cards_by_id and not focus.get("is_selected_market"):
            continue
        card = cards_by_id.get(market_id, {})
        merged = {**card, **focus}
        if fmt_value(merged.get("city")) in {"-", ""}:
            merged["city"] = _poly_city_from_question(merged.get("market_question_short") or card.get("market_question_short"))
        merged["primary_state"] = _poly_derive_primary_state(merged)
        if "can_execute" not in merged and "can_execute" in card:
            merged["can_execute"] = card.get("can_execute")
        if not merged.get("gate_status"):
            merged["gate_status"] = "allow" if merged.get("can_execute") is True else "blocked" if merged.get("can_execute") is False else "-"
        enriched.append(merged)
    return enriched


def _poly_focus_card_html(focus: dict, rank: int, tone: str) -> str:
    primary_state = str(focus.get("primary_state") or "LIVE").upper()
    state_class = _poly_state_class(primary_state)
    rank_class = "poly-rank--watch" if tone == "watch" else ""
    border_class = "poly-focus-card--watch" if tone == "watch" else "poly-focus-card--action"
    city = fmt_value(focus.get("city") or _poly_city_from_question(focus.get("market_question_short")) or focus.get("market_id") or "-")
    question = fmt_value(focus.get("market_question_short") or focus.get("market_family") or "-")
    reason = _poly_reason_label(focus)
    next_action = _poly_action_label(focus.get("next_action") or focus.get("recommended_action") or reason)
    opp = fmt_value(focus.get("latest_priority_score") or focus.get("opportunity_score"))
    fresh = fmt_value(focus.get("freshness_status") or "live")
    gate = fmt_value(focus.get("gate_status") or focus.get("can_execute") or "allow")
    return f"""
    <div class="poly-focus-card {border_class}">
      <span class="poly-badge poly-badge--{state_class}">{escape(_display_state_title(primary_state))}</span>
      <div class="poly-card-title"><span class="poly-rank {rank_class}">{escape(str(rank))}</span>{escape(city)}</div>
      <div class="poly-question">{escape(question)}</div>
      <div class="poly-reason">Reason: <b>{escape(reason)}</b></div>
      <div class="poly-metrics">
        <div><div class="poly-metric-label">Opp</div><div class="poly-metric-value">{escape(opp)}</div></div>
        <div><div class="poly-metric-label">Fresh</div><div class="poly-metric-value poly-good">{escape(fresh.upper())}</div></div>
        <div><div class="poly-metric-label">Gate</div><div class="poly-metric-value {_poly_gate_class(gate)}">{escape(gate.upper())}</div></div>
      </div>
      <div class="poly-next"><b>Next Action</b>{escape(next_action)}</div>
    </div>
    """


def _poly_market_card_html(card: dict) -> str:
    primary_state = _poly_derive_primary_state(card)
    state_class = _poly_state_class(primary_state)
    city = fmt_value(card.get("city") if fmt_value(card.get("city")) != "-" else _poly_city_from_question(card.get("market_question_short")))
    family = fmt_value(card.get("market_family") or "-")
    question = fmt_value(card.get("market_question_short") or "-")
    opp = fmt_value(card.get("opportunity_score"))
    diff = fmt_value(card.get("difficulty_label"))
    freshness = fmt_value(card.get("freshness_status") or "-")
    gate = fmt_value("allow" if card.get("can_execute") is True else "blocked" if card.get("can_execute") is False else "-")
    gate_display = "BLK" if gate.lower() == "blocked" else gate.upper()
    diff_display = (diff[:1] or "-").upper()
    model = fmt_value(card.get("best_model") or "-")
    return f"""
    <div class="poly-market-card">
      <span class="poly-badge poly-badge--{state_class}">{escape(_display_state_title(primary_state))}</span>
      <div class="poly-card-title">{escape(city)}</div>
      <div class="poly-question">{escape(question)}</div>
      <div class="poly-mini-row">
        <span>Opp<br><b>{escape(opp)}</b></span>
        <span>Diff<br><b>{escape(diff_display)}</b></span>
        <span>Gate<br><b class="{_poly_gate_class(gate)}">{escape(gate_display)}</b></span>
      </div>
      <div class="poly-mini-row">
        <span>Fresh<br><b class="{'poly-good' if str(freshness).lower() in {'fresh', 'live'} else 'poly-warn'}">{escape('LIVE' if str(freshness).lower() == 'fresh' else freshness.upper())}</b></span>
        <span>Model<br><b>{escape(model)}</b></span>
        <span>Family<br><b>{escape(family[:5])}</b></span>
      </div>
    </div>
    """


def _poly_ops_issue_html(alert: dict) -> str:
    ts = fmt_value(alert.get("generated_at") or alert.get("ts") or "-")
    title = fmt_value(alert.get("primary_reason") or alert.get("alert_type") or alert.get("component") or "Ops issue")
    subtitle = fmt_value(alert.get("affected_scope") or alert.get("component") or "-")
    return f"""
    <div class="poly-issue">
      <div class="poly-issue-dot">!</div>
      <div>
        <div class="poly-issue-title">{escape(ts[-8:] if len(ts) > 8 else ts)} · {escape(title)}</div>
        <div class="poly-issue-sub">{escape(subtitle)}</div>
      </div>
    </div>
    """


def _poly_status_rows(entries: list[tuple[str, tuple[object, str]]]) -> str:
    rows = []
    for label, (value, tone) in entries:
        rows.append(
            f"<div class='poly-status-row'>"
            f"<span class='poly-dot poly-dot--{escape(sanitize_text(tone))}'></span>"
            f"<span>{escape(sanitize_text(label))}</span>"
            f"<span class='poly-status-value'>{escape(fmt_value(value))}</span>"
            "</div>"
        )
    return "".join(rows)


def _poly_selected_detail_html(detail: dict) -> str:
    top = detail.get("top_parameter_summary") or {}
    gate = detail.get("gate_advisory_panel") or {}
    validation = detail.get("validation_compare_panel") or {}
    research = detail.get("buy_sell_decision_panel") or {}
    market_id = fmt_value(detail.get("market_id") or "-")
    question = fmt_value(detail.get("market_question") or "-")
    action = fmt_value(detail.get("next_action") or detail.get("recommended_operator_action") or "Review evidence")
    opp = fmt_value((detail.get("opportunity_context") or {}).get("opportunity_score") or "-")
    model = fmt_value((detail.get("rule_source_model_panel") or {}).get("best_model") or "-")
    fresh = fmt_value(top.get("freshness_status") or "-")
    anomaly = fmt_value((detail.get("latest_anomaly") or {}).get("anomaly_score") or "-")
    block = fmt_value(gate.get("primary_block_reason") or detail.get("execution_boundary") or "-")
    coverage = fmt_value(validation.get("label_coverage") or "-")
    research_direction = fmt_value(research.get("decision_outcome") or "review_evidence")
    research_reason = fmt_value(research.get("decision_reason") or "Research direction unavailable")
    return f"""
    <div>
      <div class="poly-detail-title">{escape(market_id)}</div>
      <div class="poly-question">{escape(question)}</div>
      <div class="poly-metrics">
        <div><div class="poly-metric-label">Opp</div><div class="poly-metric-value">{escape(opp)}</div></div>
        <div><div class="poly-metric-label">Best Model</div><div class="poly-metric-value">{escape(model)}</div></div>
        <div><div class="poly-metric-label">Fresh</div><div class="poly-metric-value poly-good">{escape(fresh.upper())}</div></div>
      </div>
    </div>
    <div>
      <div class="poly-panel-title poly-panel-title--blue">Current Risk Summary</div>
      <div class="poly-metrics">
        <div><div class="poly-metric-label">Anomaly</div><div class="poly-metric-value poly-warn">{escape(anomaly)}</div></div>
        <div><div class="poly-metric-label">Gate</div><div class="poly-metric-value poly-bad">{escape('BLOCKED' if block != '-' else 'ALLOW')}</div></div>
        <div><div class="poly-metric-label">Coverage</div><div class="poly-metric-value">{escape(coverage)}</div></div>
      </div>
      <div class="poly-reason">Primary block: <b>{escape(block)}</b></div>
    </div>
    <div>
      <div class="poly-panel-title poly-panel-title--blue">Quick Actions</div>
      <div class="poly-next"><b>Next Action</b>{escape(action)}</div>
      <div class="poly-next"><b>Research Direction</b>{escape(research_direction)}</div>
      <div class="poly-reason">Reason: <b>{escape(research_reason)}</b></div>
      <div class="poly-reason">Use the live Open Workstation / Send to Command buttons below.</div>
    </div>
    """


def _render_poly_r4_cockpit(
    *,
    global_summary: dict,
    focus_markets: list[dict],
    cards: list[dict],
    system_health: dict,
    ops_alerts: list[dict],
    quick_detail: dict,
    now_local: datetime,
    on_open_market: Callable[[str, dict], None] | None = None,
    on_send_to_command: Callable[[str, dict], None] | None = None,
) -> None:
    import streamlit as st

    scanner = system_health.get("scanner_health") or {}
    source = system_health.get("source_health") or {}
    queue = system_health.get("queue_health") or {}
    focus_markets = _poly_enrich_focus_markets(focus_markets, cards)
    requires_action, watch_list = _split_focus_markets(focus_markets)
    if len(requires_action) >= 4 and not watch_list:
        watch_list = requires_action[2:4]
        requires_action = requires_action[:2]
    action_items = requires_action[:2]
    watch_items = watch_list[: max(0, 4 - len(action_items))]
    focus_action_html = "".join(_poly_focus_card_html(item, index + 1, "action") for index, item in enumerate(action_items))
    focus_watch_html = "".join(
        _poly_focus_card_html(item, index + len(action_items) + 1, "watch") for index, item in enumerate(watch_items)
    )
    if not focus_action_html:
        focus_action_html = "<div class='poly-empty'>No action markets</div>"
    if not focus_watch_html:
        focus_watch_html = "<div class='poly-empty'>No watch markets</div>"

    non_focus_cards = [card for card in cards if not card.get("is_focus_market")]
    if not non_focus_cards:
        non_focus_cards = cards
    radar_html = "".join(_poly_market_card_html(card) for card in non_focus_cards[:12])
    ops_html = "".join(_poly_ops_issue_html(alert) for alert in ops_alerts[:3]) or "<div class='poly-empty'>No ops issues</div>"
    focus_markets_count = escape(fmt_value(global_summary.get("focus_markets_count")))
    top_ops_count = escape(fmt_value(len(ops_alerts)))
    source_html = _poly_status_rows(
        [
            ("Stale", ((source.get("counts") or {}).get("stale"), "warn")),
            ("Unavailable", ((source.get("counts") or {}).get("unavailable"), "bad")),
            ("Fallback Active", ((source.get("counts") or {}).get("fallback"), "blue")),
            ("Precision Degrade", ((source.get("counts") or {}).get("precision_degrade"), "warn")),
        ]
    )
    queue_html = _poly_status_rows(
        [
            ("Pending", (queue.get("pending_count"), "warn")),
            ("Sent (30m)", (queue.get("sent_count"), "ok")),
            ("Acked (30m)", (queue.get("acked_count"), "ok")),
            ("Suppressed", (queue.get("suppressed_count"), "blue")),
            ("Cooldown Active", (queue.get("cooldown_count") or queue.get("cooldown_active_count"), "blue")),
        ]
    )
    selected_html = _poly_selected_detail_html(quick_detail)
    st.html(
        dedent(
            f"""
        <style>
	        .poly-r4 {{
	            --bg: #02070d;
            --panel: #06131e;
            --panel2: #071722;
            --line: rgba(93, 139, 168, 0.34);
            --line2: rgba(93, 139, 168, 0.18);
            --text: #f3f7fb;
            --muted: #8ea0ad;
            --blue: #22a7ff;
            --green: #39d36d;
            --red: #ff4038;
            --amber: #ffad1f;
	            font-family: "Avenir Next", "SF Pro Text", "Helvetica Neue", sans-serif;
	            color: var(--text);
	            margin-top: -0.1rem;
	            font-size: 15px;
	            height: calc(100dvh - 0.35rem);
	            min-height: 0;
	            display: flex;
	            flex-direction: column;
	            overflow: hidden;
	        }}
	        @media (min-height: 2100px) {{
	            .poly-r4 {{ font-size: 17px; height: calc(100dvh - 0.55rem); }}
	            .poly-summary {{ margin: 0.6rem 0 0.65rem; }}
	            .poly-live-panel, .poly-load-panel, .poly-risk-panel {{ min-height: 4.55rem; }}
	            .poly-focus-card, .poly-market-card {{ min-height: 5.2rem; }}
	            .poly-detail {{ padding: 0.56rem 0.7rem; }}
	        }}
	        @media (min-height: 1400px) and (max-height: 2099px) {{
	            .poly-r4 {{ font-size: 15px; height: calc(100dvh - 0.4rem); }}
	        }}
	        @media (max-height: 1399px) {{
	            .poly-r4 {{ font-size: 14px; height: calc(100dvh - 0.22rem); }}
	            .poly-summary {{ margin: 0.36rem 0 0.38rem; gap: 0.42rem; }}
	            .poly-live-panel, .poly-load-panel, .poly-risk-panel {{ min-height: 3.55rem; padding: 0.5rem 0.58rem; }}
	            .poly-section {{ padding: 0.42rem; }}
	            .poly-focus-card, .poly-market-card {{ min-height: 3.72rem; padding: 0.38rem; }}
	            .poly-detail {{ padding: 0.38rem 0.48rem; }}
	            .poly-rail .poly-panel {{ padding: 0.48rem; }}
	        }}
	        .poly-topbar {{
	            display: grid;
	            grid-template-columns: minmax(17rem, 1fr) 2.4rem 6.4rem;
	            gap: 0.55rem;
	            align-items: center;
	            padding: 0 0 0.5rem;
	            border-bottom: 1px solid var(--line2);
	        }}
        .poly-title-row {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
            min-width: 0;
        }}
	        .poly-page-title {{
	            color: var(--text);
	            font-size: 1.12rem;
            line-height: 1;
            font-weight: 900;
            text-transform: uppercase;
            white-space: nowrap;
        }}
	        .poly-subtitle {{
	            color: var(--muted);
	            font-size: 0.66rem;
	            white-space: nowrap;
	        }}
        .poly-live {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: max-content;
            padding: 0.24rem 0.48rem;
            border-radius: 0.26rem;
            background: rgba(23, 112, 50, 0.34);
            border: 1px solid rgba(57, 211, 109, 0.22);
            color: var(--green);
            font-size: 0.66rem;
            font-weight: 900;
        }}
        .poly-bell {{
            position: relative;
	            height: 1.85rem;
            display: grid;
            place-items: center;
            border-left: 1px solid var(--line2);
            border-right: 1px solid var(--line2);
            color: #f7fbff;
            font-size: 1.05rem;
        }}
        .poly-bell::after {{
            content: "{escape(str(global_summary.get('ops_alert_count') or 0))}";
            position: absolute;
            top: 0.12rem;
            right: 0.38rem;
            min-width: 0.9rem;
            height: 0.9rem;
            border-radius: 999px;
            background: var(--red);
            color: white;
            font-size: 0.56rem;
            font-weight: 900;
            text-align: center;
            line-height: 0.9rem;
        }}
	        .poly-clock {{
	            color: #dce6ef;
	            font-size: 0.62rem;
            line-height: 1.18;
            text-align: right;
            font-weight: 800;
        }}
	        .poly-summary {{
	            display: grid;
	            grid-template-columns: 1fr 1.8fr 0.95fr;
	            gap: 0.55rem;
	            margin: 0.5rem 0 0.55rem;
	        }}
        .poly-panel {{
            border: 1px solid var(--line);
            border-radius: 0.32rem;
            background: linear-gradient(180deg, rgba(7, 21, 33, 0.98), rgba(4, 13, 22, 0.98));
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.015);
        }}
	        .poly-live-panel, .poly-load-panel {{
	            display: grid;
	            grid-template-columns: 2.8rem 1fr 0.92fr;
	            align-items: center;
	            min-height: 4.15rem;
	            padding: 0.62rem 0.72rem;
	        }}
	        .poly-load-panel {{
	            grid-template-columns: 2.6rem 1fr 1fr;
	        }}
	        .poly-risk-panel {{
	            min-height: 4.15rem;
	            padding: 0.58rem 0.72rem;
	        }}
        .poly-panel-title {{
            color: #f4f8fb;
	            font-size: 0.68rem;
            font-weight: 900;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }}
        .poly-panel-title--red {{ color: var(--red); }}
        .poly-panel-title--blue {{ color: #4bc2ff; }}
        .poly-icon-circle {{
	            width: 1.85rem;
	            height: 1.85rem;
            border-radius: 999px;
            display: grid;
            place-items: center;
            background: rgba(57, 211, 109, 0.13);
            color: var(--green);
	            font-size: 1.1rem;
            font-weight: 900;
        }}
        .poly-icon-circle--red {{
            background: transparent;
            border: 2px solid var(--red);
            color: var(--red);
        }}
        .poly-k-label {{
            color: var(--muted);
	            font-size: 0.62rem;
            margin-bottom: 0.16rem;
        }}
        .poly-k-value {{
            color: var(--text);
	            font-size: 1.25rem;
            font-weight: 900;
            line-height: 1;
        }}
        .poly-k-value--green {{ color: var(--green); }}
        .poly-k-value--red {{ color: var(--red); }}
        .poly-k-sub {{
            margin-top: 0.24rem;
            color: var(--muted);
            font-size: 0.68rem;
        }}
        .poly-risk-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
        }}
        .poly-risk-item {{
            display: grid;
	            grid-template-columns: 2.55rem 1fr;
	            gap: 0.38rem;
            align-items: center;
            border-left: 1px solid var(--line2);
	            padding-left: 0.6rem;
	        }}
	        .poly-body {{
	            display: grid;
	            grid-template-columns: minmax(0, 1fr) 16.2rem;
	            gap: 0.55rem;
	            flex: 1 1 auto;
	            min-height: 0;
	        }}
	        .poly-main {{
	            display: flex;
	            flex-direction: column;
	            gap: 0.55rem;
	            min-width: 0;
	            min-height: 0;
	        }}
	        .poly-section {{
	            padding: 0.55rem;
	        }}
	        .poly-market-panel {{
	            flex: 1 1 auto;
	            min-height: 0;
	            overflow: hidden;
	        }}
        .poly-section-head {{
            display: flex;
            justify-content: space-between;
            align-items: center;
	            margin-bottom: 0.42rem;
            color: #4bc2ff;
            font-size: 0.78rem;
            font-weight: 900;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }}
        .poly-section-head span:last-child {{
            color: var(--muted);
            font-size: 0.66rem;
            font-weight: 700;
            text-transform: none;
        }}
        .poly-focus-row {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
	            gap: 0.45rem;
	        }}
	        .poly-focus-card, .poly-market-card {{
	            position: relative;
	            min-height: 4.95rem;
	            padding: 0.5rem;
	            border-radius: 0.28rem;
	            border: 1px solid rgba(93, 139, 168, 0.3);
	            background: rgba(4, 15, 24, 0.96);
	            overflow: hidden;
	            min-width: 0;
	        }}
        .poly-focus-card--action {{ border-color: rgba(255, 64, 56, 0.72); }}
        .poly-focus-card--watch {{ border-color: rgba(255, 173, 31, 0.68); }}
        .poly-rank {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
	            width: 1.18rem;
	            height: 1.18rem;
            margin-right: 0.42rem;
            border-radius: 0.22rem;
            background: rgba(255, 64, 56, 0.78);
            color: white;
            font-weight: 900;
	            font-size: 0.72rem;
        }}
        .poly-rank--watch {{ background: rgba(60, 66, 70, 0.94); border: 1px solid rgba(255,255,255,0.2); }}
        .poly-card-title {{
            color: var(--text);
	            font-size: 0.74rem;
            font-weight: 900;
            line-height: 1.1;
            min-width: 0;
        }}
        .poly-question {{
            margin-top: 0.28rem;
            color: #dce6ef;
	            font-size: 0.56rem;
	            line-height: 1.2;
	            min-height: 1.05rem;
	            overflow: hidden;
	        }}
	        .poly-reason {{
	            margin-top: 0.28rem;
	            color: var(--muted);
		            font-size: 0.52rem;
	            line-height: 1.18;
	            white-space: nowrap;
	            overflow: hidden;
	            text-overflow: ellipsis;
	        }}
        .poly-reason b {{ color: var(--red); }}
        .poly-badge {{
            position: absolute;
	            top: 0.55rem;
	            right: 0.55rem;
            padding: 0.22rem 0.34rem;
            border-radius: 0.2rem;
            color: white;
            font-size: 0.58rem;
            font-weight: 900;
            text-transform: uppercase;
        }}
        .poly-badge--live, .poly-badge--normal {{ background: rgba(42, 132, 73, 0.84); }}
        .poly-badge--blocked, .poly-badge--alert {{ background: rgba(172, 43, 39, 0.92); }}
        .poly-badge--anom {{ background: rgba(175, 117, 24, 0.92); }}
        .poly-badge--stale {{ background: rgba(43, 105, 169, 0.92); }}
        .poly-metrics {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.45rem;
	            margin-top: 0.38rem;
	            padding-top: 0.32rem;
            border-top: 1px solid var(--line2);
        }}
        .poly-metric-label {{
            color: var(--muted);
	            font-size: 0.5rem;
        }}
        .poly-metric-value {{
            margin-top: 0.1rem;
            color: var(--text);
	            font-size: 0.68rem;
            font-weight: 900;
        }}
        .poly-good {{ color: var(--green); }}
        .poly-bad {{ color: var(--red); }}
        .poly-warn {{ color: var(--amber); }}
        .poly-next {{
	            margin-top: 0.32rem;
	            padding-top: 0.28rem;
            border-top: 1px solid var(--line2);
            color: #dce6ef;
	            font-size: 0.58rem;
        }}
        .poly-next b {{
            display: block;
            color: var(--amber);
            font-size: 0.58rem;
            text-transform: uppercase;
	            margin-bottom: 0.1rem;
	        }}
        .poly-grid-toolbar {{
            display: flex;
	            gap: 0.35rem;
	            margin-bottom: 0.45rem;
        }}
        .poly-filter {{
            border: 1px solid var(--line);
            border-radius: 0.24rem;
            background: rgba(6, 17, 27, 0.96);
            color: #cdd8e1;
	            padding: 0.3rem 0.48rem;
	            font-size: 0.62rem;
        }}
	        .poly-market-grid {{
	            display: grid;
	            grid-template-columns: repeat(6, minmax(0, 1fr));
	            gap: 0.38rem;
	            overflow: hidden;
	        }}
        .poly-market-card {{
	            min-height: 4.15rem;
	            padding: 0.42rem;
	        }}
	        .poly-market-card .poly-card-title {{ font-size: 0.66rem; padding-right: 2.5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
	        .poly-market-card .poly-question {{ font-size: 0.5rem; min-height: 1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
	        .poly-mini-row {{
	            display: grid;
	            grid-template-columns: repeat(3, 1fr);
	            gap: 0.14rem;
	            margin-top: 0.28rem;
	            color: var(--muted);
	            font-size: 0.48rem;
	        }}
	        .poly-mini-row b {{ color: var(--text); font-size: 0.56rem; white-space: nowrap; }}
	        .poly-rail {{
	            display: flex;
	            flex-direction: column;
	            gap: 0.55rem;
	            min-height: 0;
	            overflow: hidden;
	        }}
	        .poly-rail .poly-panel {{ padding: 0.62rem; }}
        .poly-issue {{
            display: grid;
            grid-template-columns: 1.3rem 1fr;
            gap: 0.5rem;
	            padding: 0.35rem 0;
            border-bottom: 1px solid var(--line2);
        }}
        .poly-issue-dot {{
            width: 1.05rem;
            height: 1.05rem;
            border-radius: 999px;
            display: grid;
            place-items: center;
            background: rgba(255, 64, 56, 0.16);
            border: 1px solid rgba(255, 64, 56, 0.45);
            color: var(--red);
            font-size: 0.72rem;
            font-weight: 900;
        }}
        .poly-issue-title {{
            color: var(--red);
            font-size: 0.68rem;
            font-weight: 900;
        }}
        .poly-issue-sub {{
            color: var(--muted);
            font-size: 0.62rem;
            margin-top: 0.12rem;
        }}
        .poly-status-row {{
            display: grid;
            grid-template-columns: 0.75rem 1fr auto;
            gap: 0.45rem;
            align-items: center;
	            padding: 0.24rem 0;
            color: #dce6ef;
            font-size: 0.68rem;
        }}
        .poly-dot {{
            width: 0.55rem;
            height: 0.55rem;
            border-radius: 999px;
        }}
        .poly-dot--ok {{ background: var(--green); }}
        .poly-dot--warn {{ background: var(--amber); }}
        .poly-dot--bad {{ background: var(--red); }}
        .poly-dot--blue {{ background: var(--blue); }}
        .poly-status-value {{
            color: var(--text);
            font-weight: 900;
            font-variant-numeric: tabular-nums;
        }}
	        .poly-detail {{
	            display: grid;
	            grid-template-columns: 1.4fr 1.45fr 1fr;
	            gap: 0.55rem;
	            padding: 0.48rem 0.58rem;
	            flex: 0 0 auto;
	        }}
        .poly-detail-title {{
            color: var(--text);
            font-size: 1rem;
            font-weight: 900;
        }}
        .poly-empty {{
            color: var(--muted);
            font-size: 0.72rem;
            padding: 0.7rem;
        }}
	        @media (max-width: 860px) {{
	            .poly-market-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
	            .poly-focus-row {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
	        }}
        </style>
        <div class="poly-r4">
          <div class="poly-topbar">
            <div class="poly-title-row">
              <div class="poly-page-title">Operations Monitor</div>
              <div class="poly-subtitle">Real-time System & Market Overview</div>
              <div class="poly-live">LIVE</div>
            </div>
            <div class="poly-bell">!</div>
            <div class="poly-clock">UTC {escape(now_local.strftime('%H:%M:%S'))}<br>{escape(now_local.strftime('%Y-%m-%d'))}</div>
          </div>
          <div class="poly-summary">
            <div class="poly-panel poly-live-panel">
              <div class="poly-icon-circle">✓</div>
              <div>
                <div class="poly-panel-title">System Live</div>
                <div class="poly-k-label">Fresh Ratio</div>
	                <div class="poly-k-value poly-k-value--green">{escape(_poly_percent(global_summary.get('fresh_ratio')))}</div>
              </div>
              <div>
                <div class="poly-k-label">Last Scan</div>
                <div class="poly-k-value" style="font-size:1rem;">{escape(fmt_value(scanner.get('last_scan_age') or scanner.get('last_run_age') or '30s ago'))}</div>
              </div>
            </div>
            <div class="poly-panel poly-risk-panel">
              <div class="poly-panel-title poly-panel-title--red">Risk Overview (Primary)</div>
              <div class="poly-risk-grid">
                <div class="poly-risk-item"><div class="poly-icon-circle poly-icon-circle--red">!</div><div><div class="poly-k-label poly-k-value--red">Alert Markets</div><div class="poly-k-value poly-k-value--red">{escape(fmt_value(global_summary.get('high_alert_markets')))}</div><div class="poly-k-sub">of scanned</div></div></div>
                <div class="poly-risk-item"><div class="poly-icon-circle poly-icon-circle--red">▣</div><div><div class="poly-k-label poly-k-value--red">Gate Blocked</div><div class="poly-k-value poly-k-value--red">{escape(fmt_value(global_summary.get('gate_blocked_markets')))}</div><div class="poly-k-sub">requires review</div></div></div>
                <div class="poly-risk-item"><div class="poly-icon-circle poly-icon-circle--red">●</div><div><div class="poly-k-label poly-k-value--red">Ops Alerts</div><div class="poly-k-value poly-k-value--red">{escape(fmt_value(global_summary.get('ops_alert_count')))}</div><div class="poly-k-sub">requires attention</div></div></div>
              </div>
            </div>
            <div class="poly-panel poly-load-panel">
              <div class="poly-icon-circle" style="background:rgba(34,167,255,0.12); color:var(--blue);">▦</div>
              <div>
                <div class="poly-panel-title poly-panel-title--blue">System Load</div>
                <div class="poly-k-label">Scan Backlog</div>
                <div class="poly-k-value">{escape(fmt_value(scanner.get('scan_backlog') or queue.get('backlog_count') or 0))}</div>
              </div>
              <div>
                <div class="poly-k-label">Queue Pending</div>
                <div class="poly-k-value">{escape(fmt_value(queue.get('pending_count')))}</div>
              </div>
            </div>
          </div>
          <div class="poly-body">
            <div class="poly-main">
	              <div class="poly-panel poly-section poly-market-panel">
	                <div class="poly-section-head"><span>Focus Opportunities ({focus_markets_count})</span><span>Opportunity-led focus list, managed from Markets / Board</span></div>
                <div class="poly-focus-row">{focus_action_html}{focus_watch_html}</div>
              </div>
              <div class="poly-panel poly-section">
	                <div class="poly-section-head"><span>Market Monitor Grid</span><span>Top non-focus monitored markets ({escape(fmt_value(len(non_focus_cards)))})</span></div>
                <div class="poly-grid-toolbar"><div class="poly-filter">Sort: Opportunity</div><div class="poly-filter">Status: All</div><div class="poly-filter">Family: All</div><div class="poly-filter">More Filters</div></div>
                <div class="poly-market-grid">{radar_html}</div>
              </div>
              <div class="poly-panel poly-detail">{selected_html}</div>
            </div>
            <div class="poly-rail">
              <div class="poly-panel"><div class="poly-section-head"><span>Top Ops Issues ({top_ops_count})</span><span>History has full audit</span></div>{ops_html}</div>
              <div class="poly-panel"><div class="poly-section-head"><span>Source Health</span><span>Count</span></div>{source_html}</div>
              <div class="poly-panel"><div class="poly-section-head"><span>Queue Summary</span><span>Count</span></div>{queue_html}</div>
            </div>
          </div>
        </div>
        """
        ).lstrip()
    )
    market_id = str(quick_detail.get("market_id") or "")
    if market_id:
        action_cols = st.columns([1.2, 1.2, 4.6], gap="small")
        if action_cols[0].button(
            "Open Workstation",
            key=f"ops_poly_open_workstation_{_slugify(market_id)}",
            use_container_width=True,
        ):
            st.session_state["operations_monitor_selected_market_id"] = market_id
            if on_open_market is not None:
                on_open_market(market_id, quick_detail)
            st.rerun()
        if action_cols[1].button(
            "Send to Command",
            key=f"ops_poly_send_command_{_slugify(market_id)}",
            use_container_width=True,
        ):
            if on_send_to_command is not None:
                on_send_to_command(market_id, quick_detail)
            st.rerun()


def _render_header(
    *,
    global_summary: dict,
    quick_detail: dict,
    system_health: dict,
    now_local: datetime,
    refresh_tick: int,
) -> None:
    scanner_health = system_health.get("scanner_health") or {}
    source_health = system_health.get("source_health") or {}
    title = sanitize_text(quick_detail.get("recommended_operator_action") or "review_scan_freshness")
    market_id = sanitize_text(quick_detail.get("market_id") or "no selected market")
    st = __import__("streamlit")
    live_time = sanitize_text(now_local.strftime("%H:%M:%S"))
    st.markdown(
        f"""
        <div class="ops-header">
          <div>
            <div class="ops-header__eyebrow">Operations Monitor</div>
            <div class="ops-header__title">Realtime scan command center</div>
            <div class="ops-header__subtitle">
              {escape(title)} • {escape(market_id)} • {escape(str(global_summary.get("focus_markets_count") or 0))} focus markets •
              {escape(str(scanner_health.get("status") or "unknown"))} scanner • {escape(str(source_health.get("overall_status") or "unknown"))} source health
            </div>
            <div class="ops-live">
              <span class="ops-live__dot"></span>
              <span>LIVE</span>
              <span class="ops-live__hint">Auto-refresh 15s</span>
              <span class="ops-live__hint">Tick {escape(str(refresh_tick))}</span>
              <span class="ops-live__hint">Last {escape(live_time)}</span>
              <span class="ops-live__hint">Scanner / queue / alerts / freshness / selected market</span>
            </div>
          </div>
          <div class="ops-header__right">
            <span class="ops-chip ops-chip--blue">{escape(str(global_summary.get("markets_scanned") or 0))} scanned</span>
            <span class="ops-chip ops-chip--emerald">{escape(str(global_summary.get("fresh_ratio") or "0.00"))} fresh ratio</span>
            <span class="ops-chip ops-chip--amber">{escape(str(global_summary.get("ops_alert_count") or 0))} ops alerts</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_ops_toolbar(
    *,
    global_summary: dict,
    quick_detail: dict,
    system_health: dict,
    now_local: datetime,
) -> None:
    import streamlit as st

    scope_value = st.session_state.setdefault("operations_monitor_scope", "All Markets")
    scope_options = ["All Markets", "Focus Markets", "Selected Market"]
    if scope_value not in scope_options:
        scope_value = "All Markets"
    scope_cols = st.columns([1.0, 1.38, 0.88, 0.18, 0.52])
    with scope_cols[0]:
        st.markdown("<div class='ops-toolbar__field'>", unsafe_allow_html=True)
        st.selectbox("Watchlist", scope_options, index=scope_options.index(scope_value), key="operations_monitor_scope", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
    with scope_cols[1]:
        st.markdown("<div class='ops-toolbar__field'>", unsafe_allow_html=True)
        st.text_input(
            "Search market, city, question...",
            value=st.session_state.get("operations_monitor_search_query", ""),
            placeholder="Search market, city, question...",
            key="operations_monitor_search_query",
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with scope_cols[2]:
        st.markdown(
            f"<div class='ops-toolbar__badge'>{escape(str(global_summary.get('markets_scanned') or 0))} scanned</div>",
            unsafe_allow_html=True,
        )
    with scope_cols[3]:
        st.markdown(
            f"<div class='ops-toolbar__alert' data-count='{escape(str(global_summary.get('ops_alert_count') or 0))}'>🔔</div>",
            unsafe_allow_html=True,
        )
    with scope_cols[4]:
        st.markdown(
            f"<div class='ops-toolbar__clock'>UTC {escape(now_local.strftime('%H:%M:%S'))}<br/>{escape(now_local.strftime('%Y-%m-%d'))}</div>",
            unsafe_allow_html=True,
        )


def _render_status_strip(*, global_summary: dict, system_health: dict) -> None:
    import streamlit as st

    scanner_health = system_health.get("scanner_health") or {}
    source_health = system_health.get("source_health") or {}
    queue_health = system_health.get("queue_health") or {}
    tiles = [
        ("Markets Scanned", global_summary.get("markets_scanned")),
        ("Focus Markets", global_summary.get("focus_markets_count")),
        ("Fresh Ratio", global_summary.get("fresh_ratio")),
        ("Alert Markets", global_summary.get("high_alert_markets")),
        ("Gate Blocked", global_summary.get("gate_blocked_markets")),
        ("Ops Alerts", global_summary.get("ops_alert_count")),
    ]
    if scanner_health.get("next_scan_eta") or source_health.get("overall_status") or queue_health.get("pending_count") is not None:
        tiles.extend(
            [
                ("Scanner ETA", scanner_health.get("next_scan_eta")),
                ("Source Health", source_health.get("overall_status")),
                ("Queue Pending", queue_health.get("pending_count")),
                ("Fresh Markets", scanner_health.get("fresh_markets")),
                ("Stale Markets", scanner_health.get("stale_markets")),
                ("Priority Mix", scanner_health.get("priority_counts")),
            ]
        )
    row_tiles = tiles[:6]
    columns = st.columns(len(row_tiles))
    for index, (label, value) in enumerate(row_tiles):
        with columns[index]:
            st.markdown(
                f"""
                <div class="ops-status-tile">
                  <div class="ops-status-tile__label">{escape(str(label))}</div>
                  <div class="ops-status-tile__value">{escape(fmt_value(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_section_title(title: str) -> None:
    import streamlit as st

    st.markdown(f"<div class='ops-section-title'>{escape(sanitize_text(title))}</div>", unsafe_allow_html=True)


def _render_panel(title: str, subtitle: str, rows: list[tuple[str, object]]) -> None:
    import streamlit as st

    row_markup = []
    for label, value in rows:
        if value in (None, "", "-", [], {}):
            continue
        row_markup.append(
            f"<div class='ops-row'><div class='ops-row__label'>{escape(sanitize_text(label))}</div><div class='ops-row__value'>{escape(fmt_value(value))}</div></div>"
        )
    body = "".join(row_markup) or "<div class='ops-note'>-</div>"
    st.markdown(
        f"""
        <div class="ops-card">
          <div class="ops-card__head">
            <div class="ops-card__title">{escape(sanitize_text(title))}</div>
            <div class="ops-card__meta">{escape(sanitize_text(subtitle))}</div>
          </div>
          {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _card_state_class(primary_state: str, *, selected: bool = False, focus: bool = False) -> str:
    state = str(primary_state or "LIVE").upper()
    classes = ["ops-card", f"ops-card--{state.lower()}"]
    if selected:
        classes.append("ops-card--selected")
    if focus and state in {"ALERT", "BLOCKED"}:
        classes.append("ops-card--focus-strong")
    elif focus:
        classes.append("ops-card--focus-soft")
    return " ".join(classes)


def _state_pill_class(state: str) -> str:
    normalized = str(state or "LIVE").upper()
    return {
        "LIVE": "ops-state-pill ops-state-pill--live",
        "STALE": "ops-state-pill ops-state-pill--stale",
        "ANOM": "ops-state-pill ops-state-pill--anom",
        "ALERT": "ops-state-pill ops-state-pill--alert",
        "BLOCKED": "ops-state-pill ops-state-pill--blocked",
    }.get(normalized, "ops-state-pill ops-state-pill--muted")


def _split_focus_markets(focus_markets: list[dict]) -> tuple[list[dict], list[dict]]:
    requires_action: list[dict] = []
    watch_list: list[dict] = []
    for focus in focus_markets:
        state = str(focus.get("primary_state") or "").upper()
        reason = str(focus.get("focus_reason") or "").lower()
        next_action = str(focus.get("next_action") or "").lower()
        actionable_block = "block=none" not in reason and "block: none" not in reason and "block=None" not in str(
            focus.get("focus_reason") or ""
        )
        if state in {"ALERT", "BLOCKED"} or ("block" in reason and actionable_block) or any(
            token in reason for token in ("alert", "anom")
        ) or any(
            token in next_action for token in ("review", "dry-run", "gate", "ack")
        ):
            requires_action.append(focus)
        else:
            watch_list.append(focus)
    return requires_action, watch_list


def _display_state_title(state: str) -> str:
    state = str(state or "LIVE").upper()
    return {
        "LIVE": "LIVE",
        "STALE": "STALE",
        "ANOM": "ANOM",
        "ALERT": "ALERT",
        "BLOCKED": "BLOCKED",
    }.get(state, state or "LIVE")


def _render_status_matrix_panel(title: str, subtitle: str, entries: list[tuple[str, object, str]]) -> None:
    import streamlit as st

    grid_rows = []
    for label, value, tone in entries:
        grid_rows.append(
            f"<div class='ops-matrix-cell ops-matrix-cell--{escape(sanitize_text(tone))}'>"
            f"<div class='ops-matrix-cell__label'>{escape(sanitize_text(label))}</div>"
            f"<div class='ops-matrix-cell__value'>{escape(fmt_value(value))}</div>"
            "</div>"
        )
    st.markdown(
        f"""
        <div class="ops-card">
          <div class="ops-card__head">
            <div class="ops-card__title">{escape(sanitize_text(title))}</div>
            <div class="ops-card__meta">{escape(sanitize_text(subtitle))}</div>
          </div>
          <div class="ops-matrix-grid">{''.join(grid_rows)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_status_list_panel(title: str, subtitle: str, entries: list[tuple[str, object, str]]) -> None:
    import streamlit as st

    item_markup = []
    for label, value, tone in entries:
        item_markup.append(
            f"<div class='ops-status-item ops-status-item--{escape(sanitize_text(tone))}'>"
            f"<div class='ops-status-item__left'>"
            f"<span class='ops-status-item__dot'></span>"
            f"<span class='ops-status-item__label'>{escape(sanitize_text(label))}</span>"
            f"</div>"
            f"<div class='ops-status-item__value'>{escape(fmt_value(value))}</div>"
            "</div>"
        )
    st.markdown(
        f"""
        <div class="ops-card">
          <div class="ops-card__head">
            <div class="ops-card__title">{escape(sanitize_text(title))}</div>
            <div class="ops-card__meta">{escape(sanitize_text(subtitle))}</div>
          </div>
          <div class="ops-status-list">{''.join(item_markup)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_focus_card(
    focus: dict,
    *,
    on_open_market: Callable[[str, dict], None] | None = None,
    index: int = 0,
    key_suffix: str | None = None,
) -> None:
    import streamlit as st

    market_id = str(focus.get("market_id") or "")
    primary_state = str(focus.get("primary_state") or "LIVE")
    secondary_states = [str(item).upper() for item in (focus.get("secondary_states") or []) if str(item).strip()]
    badge_classes = [_state_pill_class(primary_state)] + [_state_pill_class(item) for item in secondary_states[:2]]
    rank_value = str(focus.get("focus_rank") or (index + 1))
    chips = [
        f"Opp {fmt_value(focus.get('latest_priority_score'))}",
        f"{fmt_value(focus.get('market_family'))}",
        f"{fmt_value(focus.get('market_question_short'))}",
    ]
    st.markdown(
        f"""
        <div class="{_card_state_class(primary_state, selected=bool(focus.get('is_selected_market')), focus=bool(focus.get('is_selected_market')))}">
          <div class="ops-card__head">
            <div class="ops-card__title"><span class="ops-rank-badge">{escape(rank_value)}</span>{escape(fmt_value(focus.get('city') or market_id))}</div>
            <div class="ops-card__meta">{escape(fmt_value(focus.get("focus_group") or ("selected focus" if focus.get("is_selected_market") else "focus")))}</div>
          </div>
          <div class="ops-state-row">
            <span class="{badge_classes[0]}">{escape(_display_state_title(primary_state))}</span>
            {''.join(f"<span class='{escape(cls)}'>{escape(_display_state_title(state))}</span>" for cls, state in zip(badge_classes[1:], secondary_states[:2]))}
          </div>
          <div class="ops-chip-row">{''.join(f"<span class='ops-chip-mini'>{escape(chip)}</span>" for chip in chips)}</div>
          <div class="ops-row"><div class="ops-row__label">Reason</div><div class="ops-row__value">{escape(fmt_value(focus.get('focus_reason')))}</div></div>
          <div class="ops-row"><div class="ops-row__label">Priority</div><div class="ops-row__value">{escape(fmt_value(focus.get('latest_priority_score')))}</div></div>
          <div class="ops-next-action">
            <div class="ops-next-action__label">Next Action</div>
            <div class="ops-next-action__value">{escape(fmt_value(focus.get('next_action') or focus.get('focus_reason') or 'review evidence'))}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    button_key = f"ops_focus_open_{_slugify(market_id or index)}_{_slugify(key_suffix or '')}"
    if st.button("Open Workstation", key=button_key, use_container_width=True):
        st.session_state["operations_monitor_selected_market_id"] = market_id
        if on_open_market is not None and market_id:
            on_open_market(market_id, focus)
        st.rerun()


def _render_market_card(
    card: dict,
    *,
    on_open_market: Callable[[str, dict], None] | None = None,
    key_suffix: str | None = None,
) -> None:
    import streamlit as st

    market_id = str(card.get("market_id") or "")
    primary_state = str(card.get("primary_state") or "LIVE")
    secondary_states = [str(item).upper() for item in (card.get("secondary_states") or []) if str(item).strip()]
    selected_market = bool(card.get("selected_market"))
    freshness_value = card.get("freshness_status")
    source_precision_value = card.get("source_precision_score")
    try:
        source_precision_score = float(source_precision_value) if source_precision_value not in (None, "", "-") else None
    except (TypeError, ValueError):
        source_precision_score = None
    quality_bad = source_precision_score is not None and source_precision_score < 0.65
    rows = [
        ("Opp", card.get("opportunity_score")),
        ("Diff", card.get("difficulty_label")),
        ("Best Model", card.get("best_model")),
        ("Freshness", with_data_quality(freshness_value, "bad") if str(freshness_value or "").lower() not in {"fresh", "healthy", "ok"} else freshness_value),
        ("Alert", card.get("latest_alert_severity")),
        ("Anomaly", card.get("latest_anomaly_score")),
        ("Gate", card.get("can_execute")),
        ("Block", card.get("primary_block_reason")),
        ("Action", card.get("recommended_action")),
    ]
    next_action = str(card.get("recommended_action") or "review evidence")
    st.markdown(
        f"""
        <div class="{_card_state_class(primary_state, selected=selected_market, focus=False)}">
          <div class="ops-card__head">
            <div class="ops-card__title">{escape(fmt_value(card.get('city') or '-'))} / {escape(fmt_value(card.get('market_family') or '-'))}</div>
            <div class="ops-card__meta">{escape(fmt_value(card.get('scan_priority') or 'market'))}</div>
          </div>
          <div class="ops-state-row">
            <span class="{escape(_state_pill_class(primary_state))}">{escape(_display_state_title(primary_state))}</span>
            {''.join(f"<span class='{escape(_state_pill_class(state))}'>{escape(_display_state_title(state))}</span>" for state in secondary_states[:2])}
          </div>
          <div class="ops-chip-row">
            <span class="ops-chip-mini">{escape(fmt_value(card.get('market_question_short') or '-'))}</span>
            <span class="ops-chip-mini">{escape(fmt_value(source_precision_value))}</span>
            <span class="ops-chip-mini">{escape('focus' if card.get('is_focus_market') else 'monitor')}</span>
          </div>
          {''.join(f"<div class='ops-row'><div class='ops-row__label'>{escape(sanitize_text(label))}</div><div class='ops-row__value'>{escape(fmt_value(value))}</div></div>" for label, value in rows if value not in (None, '', '-', [], {}))}
          <div class="ops-next-action">
            <div class="ops-next-action__label">Next Action</div>
            <div class="ops-next-action__value">{escape(next_action)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def index_token(card: dict) -> str:
    return str(card.get("city") or card.get("market_family") or "card")


def _render_selected_market_drawer(detail: dict, *, on_open_market: Callable[[str, dict], None] | None = None) -> None:
    import streamlit as st

    if not detail:
        render_compact_note("No selected market detail available.", tone="info")
        return

    top_parameter_summary = detail.get("top_parameter_summary") or {}
    rule_source_model = detail.get("rule_source_model_panel") or {}
    gate_panel = detail.get("gate_advisory_panel") or {}
    validation_panel = detail.get("validation_compare_panel") or {}
    freshness_status = str(top_parameter_summary.get("freshness_status") or "").lower()
    source_match_grade = str(top_parameter_summary.get("source_match_grade") or "").lower()
    quality_bad = freshness_status not in {"fresh", "healthy", "ok"} or source_match_grade not in {"exact_station", "aligned"}
    primary_state = str(top_parameter_summary.get("primary_state") or "LIVE")
    summary_cells = [
        ("Market", detail.get("market_id")),
        ("State", primary_state),
        (
            "Opp",
            (detail.get("opportunity_context") or {}).get("opportunity_score")
            or (detail.get("opportunity_context") or {}).get("latest_priority_score")
            or detail.get("market_id"),
        ),
        ("Next", detail.get("next_action") or detail.get("recommended_operator_action")),
    ]
    st.markdown(
        f"""
        <div class="ops-summary-grid">
          {''.join(
              f"<div class='ops-summary-cell'><div class='ops-summary-cell__label'>{escape(sanitize_text(label))}</div><div class='ops-summary-cell__value'>{escape(fmt_value(value))}</div></div>"
              for label, value in summary_cells
          )}
        </div>
        """,
        unsafe_allow_html=True,
    )
    buttons = st.columns(2)
    market_id = str(detail.get("market_id") or "")
    if buttons[0].button("Open Workstation", key=f"ops_detail_open_{_slugify(market_id or 'detail')}", use_container_width=True):
        if on_open_market is not None and market_id:
            on_open_market(market_id, detail)
        st.rerun()
    if buttons[1].button("Focus This Market", key=f"ops_detail_focus_{_slugify(market_id or 'detail')}", use_container_width=True):
        st.session_state["operations_monitor_selected_market_id"] = market_id
        if on_open_market is not None and market_id:
            on_open_market(market_id, detail)
        st.rerun()

    with st.expander("Expand detail", expanded=False):
        cols = st.columns([1.02, 0.98])
        with cols[0]:
            _render_panel(
                "Top Parameter Summary",
                "display / canonical / freshness",
                [
                    ("Market", detail.get("market_id")),
                    ("Question", detail.get("market_question")),
                    ("Display Value", with_data_quality(top_parameter_summary.get("display_value"), "bad") if quality_bad else top_parameter_summary.get("display_value")),
                    ("Display Unit", with_data_quality(top_parameter_summary.get("display_unit"), "bad") if quality_bad else top_parameter_summary.get("display_unit")),
                    ("Model Band", with_data_quality(top_parameter_summary.get("model_band"), "bad") if quality_bad else top_parameter_summary.get("model_band")),
                    ("Observation Band", with_data_quality(top_parameter_summary.get("observation_band"), "bad") if quality_bad else top_parameter_summary.get("observation_band")),
                    ("Freshness", with_data_quality(top_parameter_summary.get("freshness_status"), "bad") if quality_bad else top_parameter_summary.get("freshness_status")),
                ],
            )
            _render_panel(
                "Rule / Source Summary",
                "best model / difficulty",
                [
                    ("Best Model", rule_source_model.get("best_model")),
                    ("Difficulty", rule_source_model.get("difficulty_label")),
                    ("Block Reason", (gate_panel.get("primary_block_reason") or "-")),
                ],
            )
        with cols[1]:
            validation_status = str(validation_panel.get("validation_status") or "").lower()
            promotion_status = str(validation_panel.get("promotion_readiness") or "").lower()
            _render_panel(
                "Validation Summary",
                "coverage / promotion",
                [
                    ("Validation Status", with_data_quality(validation_panel.get("validation_status"), "bad") if validation_status in {"weak", "insufficient"} else validation_panel.get("validation_status")),
                    ("Promotion", with_data_quality(validation_panel.get("promotion_readiness"), "bad") if promotion_status not in {"ready", "conditional"} else validation_panel.get("promotion_readiness")),
                    ("Label Coverage", with_data_quality(validation_panel.get("label_coverage"), "bad") if _is_low_coverage(validation_panel.get("label_coverage")) else validation_panel.get("label_coverage")),
                ],
            )
            _render_panel(
                "Gate Summary",
                "execution boundary",
                [
                    ("Can Execute", gate_panel.get("can_execute")),
                    ("Primary Block", gate_panel.get("primary_block_reason")),
                ],
            )


def _is_low_coverage(value: object) -> bool:
    try:
        if value in (None, "", "-"):
            return True
        return float(value) < 0.7
    except (TypeError, ValueError):
        return True


def _render_alert_card(alert: dict) -> None:
    import streamlit as st

    st.markdown(
        f"""
        <div class="ops-card">
          <div class="ops-card__head">
            <div class="ops-card__title">{escape(fmt_value(alert.get('component') or alert.get('alert_type') or 'ops'))}</div>
            <div class="ops-card__meta">{escape(fmt_value(alert.get('severity') or '-'))}</div>
          </div>
          <div class="ops-row"><div class="ops-row__label">Type</div><div class="ops-row__value">{escape(fmt_value(alert.get('alert_type')))}</div></div>
          <div class="ops-row"><div class="ops-row__label">Reason</div><div class="ops-row__value">{escape(fmt_value(alert.get('primary_reason')))}</div></div>
          <div class="ops-row"><div class="ops-row__label">Scope</div><div class="ops-row__value">{escape(fmt_value(alert.get('affected_scope')))}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _operator_summary_line(global_summary: dict, focus_markets: list[dict], ops_alerts: list[dict]) -> str:
    return (
        f"{len(focus_markets)} focus | "
        f"{global_summary.get('high_alert_markets') or 0} high-alert | "
        f"{global_summary.get('ops_alert_count') or 0} ops alerts | "
        f"{len(ops_alerts)} alerts visible"
    )


def _resolve_quick_detail(view: dict, *, selected_market_id: str, selected_card: dict | None) -> dict:
    detail = view.get("selected_market_quick_detail") or {}
    if str(detail.get("market_id") or "") == selected_market_id:
        return detail
    if not selected_card:
        return detail
    return {
        "schema_version": "selected_market_quick_detail.v1",
        "market_id": selected_market_id,
        "market_question": selected_card.get("market_question_short") or "-",
        "city": selected_card.get("city") or "-",
        "market_family": selected_card.get("market_family") or "-",
        "opportunity_context": selected_card,
        "top_parameter_summary": {
            "display_value": selected_card.get("display_value") or "-",
            "display_unit": selected_card.get("display_unit") or "-",
            "model_band": selected_card.get("model_band") or "-",
            "observation_band": selected_card.get("observation_band") or "-",
            "source_match_grade": (selected_card.get("latest_context") or {}).get("comparison_status") or "-",
            "freshness_status": selected_card.get("freshness_status") or "-",
        },
        "rule_source_model_panel": {
            "best_model": selected_card.get("best_model") or "-",
            "best_source_stack": selected_card.get("best_source_stack") or [],
            "difficulty_label": selected_card.get("difficulty_label") or "-",
        },
        "validation_compare_panel": {},
        "buy_sell_decision_panel": _build_quick_detail_buy_sell_decision_panel(selected_card),
        "gate_advisory_panel": {
            "can_execute": selected_card.get("can_execute"),
            "primary_block_reason": selected_card.get("primary_block_reason") or "-",
        },
        "latest_alert": {},
        "latest_anomaly": {},
        "latest_gate": {},
        "latest_ops": {},
        "recommended_operator_action": selected_card.get("recommended_action") or "-",
        "execution_boundary": selected_card.get("primary_block_reason") or "-",
        "source_refs": selected_card.get("upstream_refs") or {},
    }


def _build_quick_detail_buy_sell_decision_panel(selected_card: dict | None) -> dict:
    selected_card = selected_card if isinstance(selected_card, dict) else {}
    freshness = str(selected_card.get("freshness_status") or "").lower()
    edge = _to_float(selected_card.get("edge") or selected_card.get("confidence_adjusted_edge"))
    fair_value = _to_float(selected_card.get("fair_value"))
    market_probability = _to_float(selected_card.get("market_implied_probability"))
    source_precision = _to_float(selected_card.get("source_precision_score"))

    if edge is None or fair_value is None or market_probability is None:
        outcome = "review_evidence"
        reason = "Quick detail does not yet have full probability inputs."
    elif freshness in {"blocked", "unavailable", "seed_prior"}:
        outcome = "refresh_inputs"
        reason = f"Freshness state is {freshness or 'unknown'}."
    elif source_precision is not None and source_precision < 0.7:
        outcome = "review_evidence"
        reason = f"Source precision score {source_precision:.2f} is below 0.70."
    elif abs(edge) <= 0.03:
        outcome = "watch_only"
        reason = f"Edge {edge:.4f} is within the no-trade band."
    elif edge >= 0.05:
        outcome = "research_buy_yes"
        reason = "Fair value is above market implied probability."
    elif edge <= -0.05:
        outcome = "research_buy_no"
        reason = "Fair value is below market implied probability."
    else:
        outcome = "review_evidence"
        reason = "Directional threshold not met."

    return {
        "schema_version": "buy_sell_decision_panel.v1",
        "decision_outcome": outcome,
        "decision_reason": reason,
        "market_implied_probability": market_probability if market_probability is not None else "-",
        "fair_value": fair_value if fair_value is not None else "-",
        "edge": edge if edge is not None else "-",
        "execution_boundary": "gate_stack_api.v1_only",
    }


def _to_float(value: object) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _find_card(cards: list[dict], market_id: str) -> dict:
    market_id_text = str(market_id or "").strip()
    for card in cards:
        if str(card.get("market_id") or "").strip() == market_id_text and market_id_text:
            return card
    return {}


def _load_operations_monitor_view() -> dict:
    if not OPERATIONS_MONITOR_VIEW_JSON.exists():
        return {}
    try:
        payload = json.loads(OPERATIONS_MONITOR_VIEW_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _slugify(value: str) -> str:
    text = value.strip().lower().replace(" ", "_").replace("/", "_")
    text = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in text)
    while "__" in text:
        text = text.replace("__", "_")
    return text or "unknown"
