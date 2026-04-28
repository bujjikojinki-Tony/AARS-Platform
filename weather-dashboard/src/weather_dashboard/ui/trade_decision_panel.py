from __future__ import annotations

import streamlit as st

from weather_dashboard.ui.compact_panel import (
    render_compact_note,
    render_kv_section,
    render_panel_title,
    sanitize_text,
)
from weather_dashboard.ui.field_dictionary import field_label


def _support_score(comparison_status: str | None, confidence_score: float | None) -> float:
    confidence = float(confidence_score or 0.0)
    if comparison_status == "aligned":
        return min(0.5 + 0.4 * confidence, 0.95)
    if comparison_status == "mild_divergence":
        return min(0.5 + 0.15 * confidence, 0.75)
    if comparison_status == "strong_divergence":
        return max(0.5 - 0.2 * confidence, 0.20)
    if comparison_status in {"unmatched_rule", "market_mismatch"}:
        return 0.5
    return 0.5


def render_trade_decision_panel(
    market_snapshot: dict | None,
    forecast_snapshot: dict | None,
    probability_state: dict | None = None,
    comparison_row: dict | None = None,
) -> None:
    render_panel_title("Trade Decision")

    if not market_snapshot:
        st.info("No selected market available.")
        return

    favored_side = market_snapshot.get("favored_side")
    market_probability = market_snapshot.get("market_probability")
    yes_price = market_snapshot.get("yes_price")
    no_price = market_snapshot.get("no_price")

    comparison_status = (comparison_row or {}).get("comparison_status")
    confidence_score = (comparison_row or {}).get(
        "confidence_score",
        forecast_snapshot.get("confidence_score") if forecast_snapshot else None,
    )
    band_distance = (comparison_row or {}).get("band_distance")
    band_scheme = (comparison_row or {}).get("band_scheme")
    market_band_scheme = (comparison_row or {}).get("market_band_scheme")
    probability_mode = (probability_state or {}).get("probability_mode", "-")
    execution_constraint = (probability_state or {}).get("execution_constraint", "-")
    promotion_state = (probability_state or {}).get("promotion_state") or {}
    promotion_reason = promotion_state.get("promotion_reason") or (probability_state or {}).get("promotion_reason", "-")
    demotion_reason = promotion_state.get("demotion_reason") or (probability_state or {}).get("demotion_reason", "-")

    if market_probability is None:
        st.info("Selected market has no probability data yet.")
        return

    support_score = _support_score(comparison_status, confidence_score)
    market_prob = float(market_probability)
    heuristic_prob = market_prob * support_score + (1.0 - market_prob) * (1.0 - support_score)
    heuristic_prob = max(0.01, min(0.99, heuristic_prob))
    contrarian_prob = 1.0 - heuristic_prob
    recommended_side = favored_side or "yes"
    if contrarian_prob > heuristic_prob:
        recommended_side = "contrarian"
        heuristic_prob = contrarian_prob

    cards = [
        {
            "title": "Market Price",
            "value": f"{market_prob:.2f}",
            "rows": [
                ("Favored Side", favored_side or "-"),
                ("YES", yes_price if yes_price is not None else "-"),
                ("NO", no_price if no_price is not None else "-"),
            ],
        },
        {
            "title": "Decision",
            "value": recommended_side,
            "rows": [
                ("Heuristic Choice", f"{heuristic_prob:.2f}"),
                ("Forecast Support", f"{support_score:.2f}"),
                ("Forecast Confidence", f"{float(confidence_score or 0.0):.2f}"),
            ],
        },
        {
            "title": "Evidence",
            "value": comparison_status or "-",
            "rows": [
                ("Band Distance", band_distance if band_distance is not None else "-"),
                ("Counter Probability", f"{contrarian_prob:.2f}"),
                (field_label("probability_mode"), probability_mode),
            ],
        },
        {
            "title": "Constraint",
            "value": execution_constraint,
            "rows": [
                ("Can Live", "yes" if execution_constraint == "live_execution_allowed" else "no"),
                (field_label("probability_mode"), probability_mode),
                ("Use", "advisory"),
            ],
        },
        {
            "title": "Promotion",
            "value": promotion_state.get("probability_mode", probability_mode),
            "rows": [
                ("Reason", promotion_reason),
                ("Demotion", demotion_reason),
                ("Approved", "yes" if promotion_state.get("approved_for_live") else "no"),
            ],
        },
    ]
    _render_trade_decision_cards(cards)

    if st.checkbox("Show trade details", value=False, key="trade_decision_show_details"):
        c1, c2 = st.columns(2)
        with c1:
            render_kv_section(
                "Decision Inputs",
                [
                    ("Forecast Support", f"{support_score:.2f}"),
                    ("Forecast Confidence", f"{float(confidence_score or 0.0):.2f}"),
                    ("Probability Mode", probability_mode),
                    ("Execution Constraint", execution_constraint),
                ],
                metric_label="Heuristic Choice",
                metric_value=f"{heuristic_prob:.2f}",
            )
        with c2:
            render_kv_section(
                "Band / Counter",
                [
                    ("Comparison Status", comparison_status or "-"),
                    ("Band Distance", band_distance if band_distance is not None else "-"),
                    ("Band Scheme", band_scheme or "-"),
                    ("Market Band Scheme", market_band_scheme or "-"),
                    ("Contrarian Probability", f"{contrarian_prob:.2f}"),
                ],
            )
        render_compact_note(
            "Heuristic only: blends market pricing with forecast agreement. "
            "Use it as a decision aid, not a calibrated model."
        )


def _render_trade_card_styles() -> None:
    return None


def _render_trade_decision_cards(cards: list[dict]) -> None:
    _render_trade_card_styles()
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            with st.container(border=True):
                st.caption(str(card["title"]).upper())
                st.metric("Status", str(card["value"]))
                for label, value in card["rows"]:
                    st.markdown(f"**{sanitize_text(label)}:** `{sanitize_text(value)}`")
