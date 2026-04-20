from __future__ import annotations

import pandas as pd
import streamlit as st

from weather_dashboard.ui.compact_panel import render_kv_section, render_panel_title, sanitize_text


def find_resolver_rule(resolver_report: dict | None, market_id: str | None) -> dict | None:
    if not resolver_report:
        return None
    rules = resolver_report.get("rules") or []
    if not isinstance(rules, list):
        return None
    if market_id:
        for rule in rules:
            if isinstance(rule, dict) and str(rule.get("market_id") or "") == str(market_id):
                return rule
    return None


def render_architecture_styles() -> None:
    return None


def render_architecture_brief(
    *,
    market_snapshot: dict | None,
    resolver_rule: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
    bot_authorized: bool,
) -> None:
    question = _first(
        (market_snapshot or {}).get("market_question"),
        (comparison_row or {}).get("market_question"),
        "No market selected",
    )
    market_id = _first((market_snapshot or {}).get("market_id"), (comparison_row or {}).get("market_id"), "-")
    family = _first(
        (resolver_rule or {}).get("market_family"),
        (probability_state or {}).get("market_family"),
        (market_snapshot or {}).get("market_family"),
        "-",
    )
    market_probability = _fmt_num((market_snapshot or {}).get("market_probability"))
    fair_value = _fmt_num((probability_state or {}).get("fair_value"))
    edge = _fmt_num((probability_state or {}).get("edge"), signed=True)
    resolver_status = str((resolver_rule or {}).get("resolver_status") or "-")
    comparison_status = str((comparison_row or {}).get("comparison_status") or "-")
    bot_status = "AUTHORIZED" if bot_authorized else "LOCKED"
    action_hint = str((comparison_row or {}).get("action_hint") or "watch")

    render_panel_title(
        "Architecture Brief",
        f"market={sanitize_text(market_id)} · family={sanitize_text(family)} · action_hint={sanitize_text(action_hint)}",
    )

    with st.container(border=True):
        st.metric("Current Market", sanitize_text(market_id))
        st.markdown(f"**Question:** {sanitize_text(question)}")
        st.markdown(f"**Market Family:** {sanitize_text(family)}")

    cols = st.columns(5)
    _render_metric_card(cols[0], "Market Prob", market_probability, (market_snapshot or {}).get("favored_side") or "-")
    _render_metric_card(cols[1], "Shadow Fair", fair_value, f"edge {edge}")
    _render_metric_card(cols[2], "Resolver", resolver_status, (resolver_rule or {}).get("required_data_source") or "-")
    _render_metric_card(cols[3], "Comparison", comparison_status, f"gap {_fmt_num((comparison_row or {}).get('confidence_adjusted_gap'))}")
    _render_metric_card(cols[4], "BOT Gate", bot_status, "operator permission")


def render_layer_ribbon(
    *,
    market_snapshot: dict | None,
    resolver_rule: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
    bot_authorized: bool,
) -> None:
    render_panel_title("Realtime Architecture Chain")
    layers = [
        ("01", "Market", "live" if market_snapshot else "missing", "ok" if market_snapshot else "block"),
        (
            "02",
            "Resolver",
            str((resolver_rule or {}).get("resolver_status") or "missing"),
            _tone_for_status((resolver_rule or {}).get("resolver_status")),
        ),
        (
            "03",
            "Probability",
            "shadow" if probability_state else "missing",
            "warn" if probability_state else "block",
        ),
        (
            "04",
            "Comparison",
            str((comparison_row or {}).get("comparison_status") or "missing"),
            _tone_for_comparison((comparison_row or {}).get("comparison_status")),
        ),
        ("05", "Decision", str((comparison_row or {}).get("action_hint") or "watch"), "warn"),
        (
            "06",
            "XAI",
            "evidence ready" if resolver_rule or comparison_row else "pending",
            "ok" if resolver_rule or comparison_row else "warn",
        ),
        ("07", "Authorization", "authorized" if bot_authorized else "locked", "ok" if bot_authorized else "block"),
        ("08", "Execution", "dry-run only", "warn"),
    ]
    cols = st.columns(4)
    for idx, layer in enumerate(layers):
        with cols[idx % 4]:
            with st.container(border=True):
                st.caption(f"{layer[0]} {sanitize_text(layer[1]).upper()}")
                st.metric("Status", sanitize_text(layer[2]))
                st.caption(f"Tone: {sanitize_text(layer[3])}")


def render_pipeline_summary(
    *,
    market_snapshot: dict | None,
    resolver_rule: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
) -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("#### 01 Market")
        st.json(_compact_dict(market_snapshot, ["market_id", "market_question", "market_probability", "yes_price", "no_price", "market_band"]))
    with col2:
        st.markdown("#### 02 Resolver")
        st.json(_compact_dict(resolver_rule, ["resolver_status", "market_family", "required_data_source", "band_scheme", "expected_band", "station_id", "variable_name"]))
    with col3:
        st.markdown("#### 03 Probability")
        st.json(_compact_dict(probability_state, ["fair_value", "model_probability", "edge", "confidence_adjusted_edge", "calibration_status", "probability_reason"]))
    with col4:
        st.markdown("#### 04-05 Compare / Decide")
        st.json(_compact_dict(comparison_row, ["comparison_status", "confidence_adjusted_gap", "band_distance", "action_hint", "comparison_reason"]))


def render_pipeline_flow(
    *,
    market_snapshot: dict | None,
    resolver_rule: dict | None,
    probability_state: dict | None,
    comparison_row: dict | None,
) -> None:
    render_panel_title("Market-to-Execution Data Flow")
    cards = [
        _flow_card(
            "01",
            "Market",
            f"p={_fmt_num((market_snapshot or {}).get('market_probability'))}",
            _first((market_snapshot or {}).get("market_band"), (market_snapshot or {}).get("favored_side"), "-"),
        ),
        _flow_card(
            "02",
            "Resolver",
            str((resolver_rule or {}).get("resolver_status") or "missing"),
            _first((resolver_rule or {}).get("required_data_source"), (resolver_rule or {}).get("market_family"), "-"),
        ),
        _flow_card(
            "03",
            "Probability",
            f"fair={_fmt_num((probability_state or {}).get('fair_value'))}",
            _first((probability_state or {}).get("probability_reason"), "shadow / not calibrated"),
        ),
        _flow_card(
            "04",
            "Compare",
            f"edge={_fmt_num((probability_state or {}).get('edge'), signed=True)}",
            _first((comparison_row or {}).get("comparison_status"), "-"),
        ),
        _flow_card(
            "05-08",
            "Decision Gate",
            str((comparison_row or {}).get("action_hint") or "watch"),
            "XAI -> auth gate -> dry-run execution",
        ),
    ]
    cols = st.columns(2)
    for idx, card in enumerate(cards):
        with cols[idx % 2]:
            with st.container(border=True):
                st.caption(sanitize_text(card["step"]))
                st.metric(sanitize_text(card["name"]), sanitize_text(card["main"]))
                st.caption(sanitize_text(card["sub"]))


def _render_metric_card(col, label: str, value: str, hint: object) -> None:
    with col:
        with st.container(border=True):
            st.caption(sanitize_text(label).upper())
            st.metric("Value", sanitize_text(value))
            st.caption(sanitize_text(hint))


def _flow_card(step: str, name: str, main: object, sub: object) -> dict:
    return {
        "step": step,
        "name": name,
        "main": main,
        "sub": sub,
    }


def _tone_for_status(status: object) -> str:
    if status == "matched":
        return "ok"
    if status:
        return "warn"
    return "block"


def _tone_for_comparison(status: object) -> str:
    if status == "aligned":
        return "ok"
    if status in {"mild_divergence", "strong_divergence"}:
        return "warn"
    if status:
        return "block"
    return "warn"


def _fmt_num(value: object, signed: bool = False) -> str:
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if signed:
        return f"{number:+.2f}"
    return f"{number:.2f}"


def _first(*values: object) -> object:
    for value in values:
        if value not in (None, ""):
            return value
    return "-"


def _compact_dict(payload: dict | None, keys: list[str]) -> dict:
    if not payload:
        return {"status": "missing"}
    return {key: payload.get(key) for key in keys if key in payload}
