from __future__ import annotations

import pandas as pd
import streamlit as st

from weather_dashboard.ui.compact_panel import render_panel_title, sanitize_text


def _fmt_probability(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def _latest_row(df: pd.DataFrame | None) -> dict | None:
    if df is None or df.empty:
        return None
    return df.iloc[0].to_dict()


def _status_label(done: bool, active: bool = False) -> str:
    if done:
        return "completed"
    if active:
        return "active"
    return "pending"


def _step_card(index: int, title: str, desc: str, status: str) -> str:
    return sanitize_text(title)


def _monitor_item(level: str, label: str, value: str) -> str:
    return sanitize_text(label)


def _status_tile(label: str, value: str, tone: str = "neutral") -> str:
    return sanitize_text(label)


def _control_button(label: str, tone: str, hint: str) -> str:
    return sanitize_text(label)


def _segment_choice(label: str, options: list[str], key: str, default: str) -> str:
    if key not in st.session_state:
        st.session_state[key] = default
    if hasattr(st, "segmented_control"):
        return st.segmented_control(
            label,
            options,
            key=key,
            label_visibility="collapsed",
        )
    return st.radio(
        label,
        options,
        key=key,
        horizontal=True,
        label_visibility="collapsed",
    )


def _append_action_log(message: str) -> None:
    logs = st.session_state.setdefault("weather_console_action_logs", [])
    logs.insert(0, message)
    del logs[5:]


def _set_console_state(state: str) -> None:
    st.session_state["weather_console_state"] = state


def _return_to_overview() -> None:
    st.session_state["weather_console_active_step"] = "3 规则物理"
    st.session_state["weather_console_xai_level"] = "物理证据"
    _set_console_state("Overview")


def _argument_level_for_step(step_id: int) -> str:
    if step_id == 1:
        return "结论"
    if step_id in {2, 3, 4}:
        return "物理证据"
    return "孪生推演"


def render_app_header() -> None:
    render_panel_title("Polymarket Weather Desk", "Forecast Edge Command Center")


def render_command_center(
    comparison_df: pd.DataFrame | None,
    market_snapshot: dict | None,
    forecast_snapshot: dict | None,
) -> None:
    row = _latest_row(comparison_df)
    market_question = (
        (market_snapshot or {}).get("market_question")
        or (row or {}).get("market_question")
        or "No market selected"
    )
    market_id = (market_snapshot or {}).get("market_id") or (row or {}).get("market_id") or "-"
    market_family = (
        (market_snapshot or {}).get("market_family")
        or (row or {}).get("market_family")
        or "-"
    )
    market_probability = (
        (market_snapshot or {}).get("market_probability")
        if market_snapshot
        else (row or {}).get("market_probability")
    )
    yes_price = (market_snapshot or {}).get("yes_price") or (row or {}).get("yes_price")
    no_price = (market_snapshot or {}).get("no_price") or (row or {}).get("no_price")
    favored_side = (market_snapshot or {}).get("favored_side") or (row or {}).get("favored_side") or "-"
    comparison_status = (row or {}).get("comparison_status") or "-"
    gap = (row or {}).get("confidence_adjusted_gap")
    model_band = (forecast_snapshot or {}).get("model_band") or (row or {}).get("model_band") or "-"
    market_band = (market_snapshot or {}).get("market_band") or (row or {}).get("market_band") or "-"
    band_scheme = (forecast_snapshot or {}).get("band_scheme") or (row or {}).get("band_scheme") or "-"
    forecast_market_id = (forecast_snapshot or {}).get("market_id")
    rule_status = (forecast_snapshot or {}).get("rule_status") or (row or {}).get("rule_status")
    confidence_score = (forecast_snapshot or {}).get("confidence_score") or (row or {}).get("confidence_score")
    required_data_source = (
        (forecast_snapshot or {}).get("required_data_source")
        or (row or {}).get("required_data_source")
        or "-"
    )
    target_date = (forecast_snapshot or {}).get("target_date") or (row or {}).get("target_date") or "-"
    variable_name = (forecast_snapshot or {}).get("variable_name") or (row or {}).get("variable_name") or "-"

    resolver_label = "Matched"
    if forecast_market_id and str(forecast_market_id) != str(market_id):
        resolver_label = "Different Market"
    elif not forecast_snapshot:
        resolver_label = "No Forecast"
    elif (forecast_snapshot or {}).get("rule_status") not in (None, "matched", "matched_index", "matched_snapshot"):
        resolver_label = str((forecast_snapshot or {}).get("rule_status"))

    gap_display = "-"
    if gap is not None:
        try:
            gap_display = f"{float(gap):.2f}"
        except (TypeError, ValueError):
            gap_display = str(gap)

    has_market = bool(market_snapshot)
    has_family = market_family not in (None, "-", "")
    forecast_matches = bool(
        forecast_snapshot
        and forecast_market_id
        and str(forecast_market_id) == str(market_id)
    )
    has_comparison = row is not None and comparison_status not in (None, "-")
    needs_guard = resolver_label != "Matched" or comparison_status in {"unmatched_rule", "market_mismatch", None}

    confidence_display = "-"
    if confidence_score is not None:
        try:
            confidence_display = f"{float(confidence_score):.2f}"
        except (TypeError, ValueError):
            confidence_display = str(confidence_score)

    monitor_level = "info"
    monitor_text = "Ready"
    if resolver_label == "Different Market":
        monitor_level = "critical"
        monitor_text = "Market mismatch"
    elif resolver_label == "No Forecast":
        monitor_level = "warning"
        monitor_text = "Forecast unavailable"
    elif comparison_status == "strong_divergence":
        monitor_level = "warning"
        monitor_text = "Strong divergence"

    action_side = "YES" if str(favored_side).lower() == "yes" else "NO"
    if comparison_status in {"market_mismatch", "unmatched_rule", "-"}:
        action_side = "WAIT"
    elif comparison_status == "strong_divergence":
        action_side = "CONTRARIAN CHECK"

    footer_hint = (
        "BOT 自动买卖暂不可执行：需先核对 resolver 与 market_id 是否一致。"
        if needs_guard
        else f"BOT 可围绕 {action_side} 侧进入自动执行/监控，但仍需遵守授权边界。"
    )
    xai_conclusion = (
        f"当前市场概率为 {_fmt_probability(market_probability)}，比较状态为 {comparison_status}。"
    )
    xai_evidence = (
        f"Polymarket band={market_band}，forecast band={model_band}，gap={gap_display}。"
    )
    xai_simulation = (
        f"若盘口继续偏离 resolver band，系统将维持 {action_side} 的执行边界。"
    )

    step_options = [
        "1 结论",
        "2 市场物理",
        "3 规则物理",
        "4 比较证据",
        "5 孪生预演",
    ]
    st.session_state.setdefault("weather_console_state", "Overview")
    previous_step = st.session_state.get("weather_console_prev_step")

    render_panel_title("State Machine Controls")
    with st.container(border=True):
        step_col, xai_col = st.columns([1.3, 1])
        with step_col:
            st.caption("论证规程 / activeStepId")
            active_step_choice = _segment_choice(
                "Argument procedure step",
                step_options,
                "weather_console_active_step",
                "3 规则物理",
            )
        with xai_col:
            preview_step_id = int(active_step_choice.split(" ", 1)[0])
            st.caption("绑定论据层")
            st.markdown(
                f"**{_argument_level_for_step(preview_step_id)}** · 随规程步骤同步",
            )

        bot_auth_col, auth_col, action_col, overview_col = st.columns([1.1, 0.9, 1.1, 0.9])
        with bot_auth_col:
            st.caption("BOT 买卖授权")
            if st.button(
                "授权 BOT 自动买卖",
                use_container_width=True,
                key="weather_console_evidence_authorize",
            ):
                st.session_state["weather_console_authorized"] = True
                authorized = True
                _set_console_state("Authorized")
                _append_action_log(f"BOT 自动买卖授权已启用：market {market_id}，建议侧 {action_side}")
                st.rerun()
        with auth_col:
            st.caption("BOT 门禁")
            if "weather_console_authorized" not in st.session_state:
                st.session_state["weather_console_authorized"] = False
            authorized = bool(st.session_state["weather_console_authorized"])
            if st.button(
                "启用授权" if not authorized else "撤销授权",
                use_container_width=True,
                key="weather_console_auth_toggle",
            ):
                st.session_state["weather_console_authorized"] = not authorized
                authorized = bool(st.session_state["weather_console_authorized"])
                _set_console_state("Authorized" if authorized else "Locked")
                _append_action_log("BOT 交易授权已启用" if authorized else "BOT 交易授权已撤销")
                st.rerun()
        with action_col:
            st.caption("BOT 执行")
            can_execute = authorized and action_side not in {"WAIT", "-"}
            if st.button(
                f"提交 BOT {action_side}",
                use_container_width=True,
                disabled=not can_execute,
                key="weather_console_execute_action",
            ):
                _set_console_state("Logged")
                _append_action_log(f"BOT 执行语义动作：{action_side} for market {market_id}")
                st.toast(f"Bot action logged: {action_side}", icon="✅")
        with overview_col:
            st.caption("状态机")
            st.button(
                "返回总览",
                use_container_width=True,
                key="weather_console_return_overview",
                on_click=_return_to_overview,
            )

    active_step_id = int(active_step_choice.split(" ", 1)[0])
    active_xai_level = _argument_level_for_step(active_step_id)
    st.session_state["weather_console_xai_level"] = active_xai_level

    if previous_step is None:
        st.session_state["weather_console_prev_step"] = active_step_choice
    elif previous_step != active_step_choice:
        st.session_state["weather_console_prev_step"] = active_step_choice
        _set_console_state("ArgumentStepFocused")

    active_step_title = {
        1: "顶层结论规程",
        2: "市场物理事实规程",
        3: "Forecast / Resolver 规则规程",
        4: "赔率-预测比较证据规程",
        5: "孪生预演推算规程",
    }.get(active_step_id, "Forecast / Resolver 规则规程")
    authorized_label = "BOT已授权" if authorized else "BOT未授权"
    xai_body_by_level = {
        "结论": xai_conclusion,
        "物理证据": xai_evidence,
        "孪生推演": xai_simulation,
    }
    active_xai_body = xai_body_by_level.get(active_xai_level, xai_conclusion)
    action_log = st.session_state.get("weather_console_action_logs", [])
    latest_action_log = action_log[0] if action_log else "暂无动作日志"
    console_state = st.session_state.get("weather_console_state", "Overview")
    control_state = "BOT Authorized" if authorized else "BOT Locked"
    state_class = {
        "Overview": "state-overview",
        "StepFocused": "state-step",
        "ArgumentStepFocused": "state-step",
        "XAILevelChanged": "state-xai",
        "Locked": "state-locked",
        "Authorized": "state-authorized",
        "Logged": "state-logged",
    }.get(str(console_state), "state-overview")

    st.markdown(
        "",
    )
    with st.container(border=True):
        st.metric("Market", sanitize_text(market_id))
        st.markdown(f"**Situation:** {sanitize_text(market_question)}")
        top_cols = st.columns(6)
        _inline_metric(top_cols[0], "Family", market_family)
        _inline_metric(top_cols[1], "AI", confidence_display)
        _inline_metric(top_cols[2], "Mode", resolver_label)
        _inline_metric(top_cols[3], "BOT", authorized_label)
        _inline_metric(top_cols[4], "State", console_state)
        _inline_metric(top_cols[5], "Action", action_side)
        status_cols = st.columns(4)
        _inline_metric(status_cols[0], "规程", active_step_title)
        _inline_metric(status_cols[1], "论据", active_xai_level)
        _inline_metric(status_cols[2], "Forecast", model_band)
        _inline_metric(status_cols[3], "Market Gap", gap_display)
        st.caption(f"{sanitize_text(active_xai_body)} · {sanitize_text(footer_hint)}")


def render_deerflow_signature() -> None:
    st.caption("Created By Deerflow · https://deerflow.tech")


def _inline_metric(col, label: str, value: object) -> None:
    with col:
        with st.container(border=True):
            st.caption(sanitize_text(label))
            st.metric("Value", sanitize_text(value))
