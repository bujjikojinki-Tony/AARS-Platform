from __future__ import annotations

import streamlit as st


def render_status_badge(label: str) -> None:
    normalized = str(label or "UNKNOWN")
    st.markdown(
        f"""
        <span style="
            display:inline-flex;
            align-items:center;
            border:1px solid rgba(148,163,184,.35);
            border-radius:999px;
            padding:0.18rem 0.55rem;
            font-size:0.72rem;
            font-weight:700;
            letter-spacing:0.02em;
            color:#d8e2ea;
            background:rgba(8,12,18,.72);
            white-space:nowrap;
        ">{normalized}</span>
        """,
        unsafe_allow_html=True,
    )
