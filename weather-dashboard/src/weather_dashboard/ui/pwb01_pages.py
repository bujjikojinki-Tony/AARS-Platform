from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from weather_dashboard.ui.pwb01_runtime import get_pwb01_runtime


def render_pwb01_opportunity_board_page() -> None:
    runtime = get_pwb01_runtime()
    st.markdown("## Opportunity Board")
    st.caption("Round PWB-01 execution candidates. Scan mock markets, rank opportunities, and send candidate ids to Command.")

    top_cols = st.columns([1, 4], gap="small")
    if top_cols[0].button("Scan Markets", key="pwb01_opp_scan", use_container_width=True):
        result = runtime.opportunity_routes.post_scan()
        st.session_state["pwb01_last_scan_result"] = result
        st.rerun()
    last_scan = st.session_state.get("pwb01_last_scan_result")
    top_cols[1].caption(
        f"Last scan: {last_scan.get('candidate_count', 0)} candidates created."
        if isinstance(last_scan, dict) and last_scan.get("ok")
        else "Run a scan to generate candidates from the mock market source."
    )

    response = runtime.opportunity_routes.get_opportunities()
    items = response.get("items", [])
    if not items:
        st.info("No candidates yet. Click `Scan Markets` to generate opportunity candidates.")
        return

    df = pd.DataFrame(items)
    preferred_columns = [
        "candidate_id",
        "market_id",
        "question",
        "side",
        "market_probability",
        "model_probability",
        "edge_percent",
        "risk_status",
        "action_status",
        "created_at",
    ]
    display_columns = [column for column in preferred_columns if column in df.columns]
    st.dataframe(df[display_columns], use_container_width=True, hide_index=True)

    selected_candidate_id = st.selectbox(
        "Selected candidate",
        df["candidate_id"].tolist(),
        key="pwb01_opp_selected_candidate",
    )
    selected_row = next(row for row in items if row["candidate_id"] == selected_candidate_id)
    st.markdown(
        f"""
        <div style="border:1px solid rgba(110,140,168,.25);border-radius:10px;padding:0.8rem;background:rgba(9,18,28,.82);">
          <div style="font-size:0.75rem;color:#8ea3b7;">Candidate Detail</div>
          <div style="font-size:1rem;color:#f5f8fb;font-weight:800;">{escape(str(selected_row.get('question') or selected_row.get('market_id')))}</div>
          <div style="font-size:0.8rem;color:#b8c7d3;margin-top:0.3rem;">
            Side: <strong>{escape(str(selected_row.get('side')))}</strong> ·
            Edge: <strong>{escape(str(selected_row.get('edge_percent')))}%</strong> ·
            Risk: <strong>{escape(str(selected_row.get('risk_status')))}</strong> ·
            Action: <strong>{escape(str(selected_row.get('action_status')))}</strong>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pwb01_command_page() -> None:
    runtime = get_pwb01_runtime()
    st.markdown("## Command")
    st.caption("Local command console for PWB-01. LIVE_EXECUTE is disabled and unsupported commands are rejected.")

    response = runtime.opportunity_routes.get_opportunities()
    candidates = response.get("items", [])

    quick_cols = st.columns([1, 1, 1, 2], gap="small")
    if quick_cols[0].button("Run /run scan", key="pwb01_cmd_run_scan", use_container_width=True):
        st.session_state["pwb01_last_command_result"] = runtime.command_routes.post_command("/run scan")
        st.rerun()
    simulate_candidate_id = quick_cols[1].selectbox(
        "Simulate candidate",
        [row["candidate_id"] for row in candidates] if candidates else ["No candidates"],
        disabled=not bool(candidates),
        key="pwb01_cmd_candidate_id",
    )
    if quick_cols[2].button("Run /simulate", key="pwb01_cmd_simulate", use_container_width=True, disabled=not bool(candidates)):
        st.session_state["pwb01_last_command_result"] = runtime.command_routes.post_command(f"/simulate {simulate_candidate_id}")
        st.rerun()
    quick_cols[3].caption("Also supported: `/show rules`, `/set mode simulation`, `/set mode observe_only`")

    command_text = st.text_input(
        "Command Input",
        value=st.session_state.get("pwb01_command_text", "/show rules"),
        key="pwb01_command_text",
        placeholder="/run scan",
    )
    if st.button("Execute Command", key="pwb01_cmd_execute", use_container_width=True):
        st.session_state["pwb01_last_command_result"] = runtime.command_routes.post_command(command_text)
        st.rerun()

    mode = runtime.settings_routes.get_mode()
    st.caption(f"Current mode: `{mode.get('mode', 'OBSERVE_ONLY')}`")
    result = st.session_state.get("pwb01_last_command_result")
    if isinstance(result, dict):
        st.json(result)
    else:
        st.info("No command executed yet.")


def render_pwb01_history_page() -> None:
    runtime = get_pwb01_runtime()
    st.markdown("## History")
    st.caption("Persisted execution-core history across signals, candidates, simulations, and audit logs.")

    tabs = st.tabs(["Signals", "Candidates", "Simulations", "Audit Logs"])
    history_payloads = [
        runtime.history_routes.get_signals(),
        runtime.history_routes.get_candidates(),
        runtime.history_routes.get_simulations(),
        runtime.history_routes.get_audit(),
    ]
    for tab, payload in zip(tabs, history_payloads, strict=True):
        with tab:
            items = payload.get("items", [])
            if not items:
                st.info("No records yet.")
                continue
            st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)


def render_pwb01_settings_page(*, section: str = "alerts_rules") -> None:
    runtime = get_pwb01_runtime()
    st.markdown("## Settings")
    st.caption("Minimal rule and mode controls for PWB-01. These update the local execution-core registry only.")

    section_cols = st.columns([1, 1, 1], gap="small")
    section_cols[0].metric("Section", "Rules")
    section_cols[1].metric("View", section.replace("_", " ").title())
    section_cols[2].metric("Execution Mode", runtime.settings_routes.get_mode().get("mode", "OBSERVE_ONLY"))

    rules_response = runtime.settings_routes.get_rules()
    rules = rules_response.get("rules", {})
    left, right = st.columns([0.64, 0.36], gap="medium")
    with left:
        st.dataframe(
            pd.DataFrame(
                [{"rule": key, "value": value} for key, value in rules.items() if key != "execution_mode"]
            ),
            use_container_width=True,
            hide_index=True,
        )
        with st.form(f"pwb01_rules_form_{section}"):
            min_edge_percent = st.number_input("min_edge_percent", value=float(rules.get("min_edge_percent", 10.0)), step=0.5)
            min_liquidity = st.number_input("min_liquidity", value=float(rules.get("min_liquidity", 100.0)), step=10.0)
            max_spread = st.number_input("max_spread", value=float(rules.get("max_spread", 0.08)), step=0.01, format="%.2f")
            submitted = st.form_submit_button("Update Rules", use_container_width=True)
            if submitted:
                result = runtime.settings_routes.post_rules(
                    {
                        "min_edge_percent": min_edge_percent,
                        "min_liquidity": min_liquidity,
                        "max_spread": max_spread,
                    }
                )
                st.session_state["pwb01_last_settings_result"] = result
                st.rerun()
    with right:
        mode_choice = st.selectbox(
            "Execution Mode",
            ["OBSERVE_ONLY", "SIMULATION"],
            index=0 if runtime.settings_routes.get_mode().get("mode") == "OBSERVE_ONLY" else 1,
            key=f"pwb01_mode_choice_{section}",
        )
        if st.button("Update Mode", key=f"pwb01_update_mode_{section}", use_container_width=True):
            st.session_state["pwb01_last_settings_result"] = runtime.settings_routes.post_mode(mode_choice)
            st.rerun()
        result = st.session_state.get("pwb01_last_settings_result")
        if isinstance(result, dict):
            st.json(result)
        else:
            st.info("No settings update yet.")
