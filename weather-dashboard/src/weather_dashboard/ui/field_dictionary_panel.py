from __future__ import annotations

import pandas as pd
import streamlit as st

from weather_dashboard.ui.field_dictionary import (
    FIELD_DICTIONARY_VERSION,
    build_field_dictionary_rows,
)


def render_field_dictionary_panel() -> None:
    st.markdown("#### UI Field Dictionary")
    st.caption(
        f"Version `{FIELD_DICTIONARY_VERSION}`. This is the single glossary for dashboard operator-facing terms."
    )

    groups = sorted({row["group"] for row in build_field_dictionary_rows()})
    selected_group = st.selectbox(
        "Field group",
        options=["all"] + groups,
        key="field_dictionary_group",
    )
    rows = build_field_dictionary_rows(None if selected_group == "all" else selected_group)
    if not rows:
        st.info("No fields found for the selected group.")
        return
    frame = pd.DataFrame(rows)
    st.dataframe(frame, use_container_width=True, hide_index=True)
