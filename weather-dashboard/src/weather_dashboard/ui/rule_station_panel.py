import streamlit as st


def build_selected_rule(rulebook_payload: dict | list | None, selected_market_id: str | None) -> tuple[list[dict], dict | None]:
    if not rulebook_payload:
        return [], None

    if isinstance(rulebook_payload, dict):
        rules = rulebook_payload.get("rules", [])
    elif isinstance(rulebook_payload, list):
        rules = rulebook_payload
    else:
        rules = []

    if not rules:
        return [], None

    selected_rule = None
    if selected_market_id:
        for rule in rules:
            if rule.get("market_id") == selected_market_id:
                selected_rule = rule
                break

    return rules, selected_rule


def render_rule_station_panel(
    rulebook_payload: dict | list | None,
    selected_market_id: str | None,
) -> None:
    st.subheader("Rule / Station Info")

    rules, selected_rule = build_selected_rule(rulebook_payload, selected_market_id)
    if not rulebook_payload:
        st.info("No rulebook payload available.")
        return
    if not rules:
        st.info("No rules found in rulebook.")
        return

    if selected_rule is None:
        st.info("No matching rule found for the selected market.")
        with st.expander("Available Rulebook Entries", expanded=False):
            st.dataframe(
                [
                    {
                        "market_id": rule.get("market_id", "-"),
                        "question": rule.get("market_question", "-"),
                        "location_name": rule.get("location_name", "-"),
                        "station_name": rule.get("station_name", "-"),
                    }
                    for rule in rules[:20]
                ],
                use_container_width=True,
                hide_index=True,
            )
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Market ID:** `{selected_rule.get('market_id', '-')}`")
        st.markdown(f"**Question:** {selected_rule.get('market_question', '-')}")
        st.markdown(f"**Market Type:** {selected_rule.get('market_type', '-')}")
        st.markdown(f"**Location:** {selected_rule.get('location_name', '-')}")
        st.markdown(f"**Target Date:** {selected_rule.get('target_date', '-')}")

    with col2:
        st.markdown(f"**Station Name:** {selected_rule.get('station_name', '-')}")
        st.markdown(f"**NWS Station ID:** {selected_rule.get('nws_station_id', '-')}")
        st.markdown(f"**CDO Station ID:** {selected_rule.get('cdo_station_id', '-')}")
        st.markdown(f"**Timezone:** {selected_rule.get('timezone', '-')}")
        st.markdown(f"**Variable:** {selected_rule.get('variable_name', '-')}")
        st.markdown(f"**Parse Confidence:** {selected_rule.get('parse_confidence', '-')}")

    with st.expander("Raw Rule", expanded=False):
        st.json(selected_rule)
