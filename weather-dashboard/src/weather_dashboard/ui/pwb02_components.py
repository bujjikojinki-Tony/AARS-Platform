from __future__ import annotations

from html import escape

import streamlit as st

from weather_dashboard.ui.status_badge import render_status_badge


def render_weather_descriptor_card(descriptor: dict | None) -> None:
    st.markdown("### Market Descriptor")
    if not descriptor:
        st.info("No descriptor found.")
        return
    cols = st.columns(4)
    cols[0].metric("City", str(descriptor.get("city") or "—"))
    cols[1].metric("Date", str(descriptor.get("target_date") or "—"))
    cols[2].metric("Metric", str(descriptor.get("metric") or "—"))
    cols[3].metric("Direction", str(descriptor.get("direction") or "—"))
    st.caption(str(descriptor.get("question") or ""))
    st.write(
        f"Threshold: {descriptor.get('threshold', '—')} {descriptor.get('unit', '')} | "
        f"Country: {descriptor.get('country') or '—'}"
    )
    warnings = descriptor.get("parse_warnings") or []
    if warnings:
        st.warning("Parse warnings: " + ", ".join(str(item) for item in warnings))
    render_status_badge(str(descriptor.get("confidence") or "UNKNOWN"))


def render_weather_sources_table(sources: list[dict] | None) -> None:
    st.markdown("### Weather Sources")
    items = sources or []
    if not items:
        st.info("No source records found.")
        return
    st.dataframe(
        [
            {
                "source": item.get("source_name"),
                "type": item.get("source_type"),
                "value": item.get("normalized_value"),
                "unit": item.get("unit"),
                "freshness": item.get("freshness_status"),
                "trust": item.get("trust_level"),
                "fetched": item.get("fetched_at"),
            }
            for item in items
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_evidence_pack_card(evidence_pack: dict | None) -> None:
    st.markdown("### Evidence Pack")
    if not evidence_pack:
        st.info("No evidence pack found.")
        return
    left, right = st.columns(2)
    left.metric("Freshness", str(evidence_pack.get("evidence_freshness") or "—"))
    right.metric("Conflict", str(evidence_pack.get("evidence_conflict_level") or "—"))
    descriptor = evidence_pack.get("descriptor") or {}
    st.write(f"Pack: `{evidence_pack.get('evidence_pack_id')}` for `{evidence_pack.get('market_id')}`")
    if descriptor:
        st.caption(f"Descriptor city: {descriptor.get('city')}, date: {descriptor.get('target_date')}")
    raw_refs = evidence_pack.get("raw_refs") or []
    if raw_refs:
        st.code("\n".join(str(ref) for ref in raw_refs))


def render_weather_view_card(weather_view: dict | None) -> None:
    st.markdown("### Weather View")
    if not weather_view:
        st.info("No weather view found.")
        return
    cols = st.columns(5)
    cols[0].metric("Expected", f"{float(weather_view.get('expected_value', 0.0)):.2f}")
    cols[1].metric("Range Low", f"{float(weather_view.get('expected_range_low', 0.0)):.2f}")
    cols[2].metric("Range High", f"{float(weather_view.get('expected_range_high', 0.0)):.2f}")
    cols[3].metric("Sigma", str(weather_view.get("sigma") or "—"))
    cols[4].metric("Threshold", str(weather_view.get("threshold") or "—"))
    for label in ("evidence_summary", "confirmation_rules", "invalidation_rules"):
        items = weather_view.get(label) or []
        if items:
            st.caption(label.replace("_", " ").title())
            st.write("\n".join(f"- {escape(str(item))}" for item in items))


def render_probability_view_card(probability_view: dict | None) -> None:
    st.markdown("### Probability View")
    if not probability_view:
        st.info("No probability view found.")
        return
    cols = st.columns(5)
    cols[0].metric("Model Probability", f"{float(probability_view.get('model_probability', 0.0)) * 100:.1f}%")
    cols[1].metric("Engine", str(probability_view.get("engine_id") or "—"))
    cols[2].metric("Expected", f"{float(probability_view.get('expected_value', 0.0)):.2f}")
    cols[3].metric("Sigma", str(probability_view.get("sigma") or "—"))
    cols[4].metric("Direction", str(probability_view.get("direction") or "—"))
    warnings = probability_view.get("warnings") or []
    if warnings:
        st.warning("Warnings: " + ", ".join(str(item) for item in warnings))


def render_candidate_decision_card(candidate: dict | None) -> None:
    st.markdown("### Candidate / Decision")
    if not candidate:
        st.info("No candidate found.")
        return
    cols = st.columns(6)
    cols[0].metric("Side", str(candidate.get("side") or "—"))
    cols[1].metric("Market Prob.", f"{float(candidate.get('market_probability', 0.0)) * 100:.1f}%")
    cols[2].metric("Model Prob.", f"{float(candidate.get('model_probability', 0.0)) * 100:.1f}%")
    cols[3].metric("Edge", f"{float(candidate.get('edge_percent', 0.0)):.1f}%")
    cols[4].metric("Liquidity", str(candidate.get("liquidity") or "—"))
    cols[5].metric("Spread", str(candidate.get("spread") or "—"))
    st.write(f"Risk: `{candidate.get('risk_status')}` | Action: `{candidate.get('action_status')}`")


def render_pipeline_node(title: str, description: str, status: str) -> None:
    st.markdown(
        f"""
        <section style="
            border:1px solid rgba(148,163,184,.28);
            border-radius:18px;
            padding:1rem;
            background:rgba(8,12,18,.72);
            box-shadow:0 2px 16px rgba(0,0,0,.12);
        ">
          <div style="display:flex;justify-content:space-between;gap:0.75rem;align-items:center;">
            <h3 style="margin:0;font-size:1rem;color:#eef5fa;">{escape(title)}</h3>
            <span style="border:1px solid rgba(148,163,184,.35);border-radius:999px;padding:0.18rem 0.55rem;font-size:0.72rem;font-weight:700;">{escape(status)}</span>
          </div>
          <p style="margin:0.55rem 0 0;color:#aab8c4;font-size:0.9rem;">{escape(description)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
