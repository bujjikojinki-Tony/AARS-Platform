from __future__ import annotations

import streamlit as st


def render_signal_panel(signal_payload: dict) -> None:
    st.subheader("Latest Signal")

    if not signal_payload:
        st.info("No signal payload found.")
        return

    st.json(signal_payload)
