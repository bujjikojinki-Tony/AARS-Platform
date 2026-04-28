from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

from weather_dashboard.settings import (
    GATE_STACK_OPS_ALERTS_JSONL,
    MONITORING_STATUS_JSON,
    OUTPUT_DIR,
    PAGE_CONTEXT_JSON,
    SOURCE_POLICY_STATUS_JSON,
    UNIFIED_STATUS_JSON,
    WORKSPACE_DIR,
)
from weather_dashboard.ui.action_policy import decide_action_visibility


UI_POLICY_REGISTRY_DIR = WORKSPACE_DIR / "weather-comparison-engine" / "data" / "registries" / "ui_policy_registry"


def render_alerts_rules_settings_page() -> None:
    _render_settings_theme()
    rules = _build_alert_rule_rows()
    ops_alerts = _load_jsonl(GATE_STACK_OPS_ALERTS_JSONL)

    _apply_record_overrides(rules, state_key="settings_alert_rule_overrides", id_field="rule_id")
    status_overrides = st.session_state.setdefault("settings_alert_rule_status", {})
    for rule in rules:
        rule["status"] = status_overrides.get(rule["rule_id"], rule["status"])

    _render_page_frame_start(
        title="Settings > Alerts & Rules",
        subtitle="Manage alert rules, thresholds, notification channels and routing policies.",
        active_label="ALERT GOVERNANCE",
    )
    _render_top_actions(
        [
            ("Test Rule", "settings_alert_top_test"),
            ("Import", "settings_alert_top_import"),
            ("Export", "settings_alert_top_export"),
            ("+ New Rule", "settings_alert_top_new"),
        ],
        payload=rules,
        export_name="alert_rules_registry_view.json",
        page="alerts_rules",
    )
    active_tab = _render_subtabs(
        ["Alert Rules", "Notification Channels", "Routing Policies", "Snooze Schedule", "Alert History"],
        "Alert Rules",
        key="settings_alerts_active_tab",
    )

    _metric_strip(
        [
            ("Total Rules", len(rules), "up 3 vs last 7d", "info"),
            ("Active", _count_where(rules, "status", "Enabled"), "71%", "good"),
            ("Disabled", _count_where(rules, "status", "Disabled"), "17%", "warn"),
            ("Testing", _count_where(rules, "status", "Testing"), "12%", "info"),
            ("Critical Alerts (24h)", _severity_count(rules, "Critical"), "up 3", "danger"),
            ("Warnings (24h)", max(23, len(ops_alerts)), "up 5", "warn"),
            ("Info (24h)", 41, "down 6", "good"),
        ]
    )
    _render_settings_result_banner(
        "alerts_rules",
        fallback_title="Rules Registry Ready",
        fallback_message="Use the filters and action buttons below to inspect, test, enable, disable, or draft rules.",
    )

    if active_tab != "Alert Rules":
        _render_alerts_rules_secondary_tab(active_tab, rules, ops_alerts)
        _render_page_frame_end()
        return

    filters = st.columns([1.4, 1, 1, 1, 1], gap="small")
    query = filters[0].text_input("Search rules", placeholder="Rule name, condition, target...", key="settings_alert_query")
    type_filter = filters[1].selectbox("Type", ["All", *_unique(rules, "type")], key="settings_alert_type")
    severity_filter = filters[2].selectbox("Severity", ["All", *_unique(rules, "severity")], key="settings_alert_severity")
    status_filter = filters[3].selectbox("Status", ["All", "Enabled", "Disabled", "Testing"], key="settings_alert_status")
    channel_filter = filters[4].selectbox("Channel", ["All", "Telegram", "Dashboard", "Ops Log", "Email", "Webhook"], key="settings_alert_channel")

    filtered = _filter_records(
        rules,
        query=query,
        query_fields=["rule_name", "condition", "target", "type"],
        exact_filters={"type": type_filter, "severity": severity_filter, "status": status_filter},
        contains_filters={"actions": channel_filter},
    )
    selected_rule = _select_record(filtered, label_field="rule_name", key="settings_selected_rule", empty_message="No alert rules match the current filters.")
    _write_settings_page_context(
        source_page="settings",
        target_page="alerts_rules",
        entry_reason="inspect_rule",
        entry_context={
            "active_tab": active_tab,
            "selected_rule_id": (selected_rule or {}).get("rule_id"),
            "selected_rule_name": (selected_rule or {}).get("rule_name"),
            "selected_rule_type": (selected_rule or {}).get("type"),
        },
    )
    _current_page_context_summary(
        "Alerts & Rules",
        active_tab,
        str((selected_rule or {}).get("rule_name") or "None"),
        str((selected_rule or {}).get("rule_id") or "-"),
    )

    left, right = st.columns([0.76, 0.24], gap="medium")
    with left:
        _render_alert_rules_table(filtered, selected_rule)
        _action_bar_alert_rule(selected_rule)
    with right:
        _render_alert_rule_detail(selected_rule, ops_alerts)
        _render_alert_rule_editor(selected_rule)

    _render_page_frame_end()


def render_data_sources_settings_page() -> None:
    _render_settings_theme()
    sources = _build_source_rows()

    _apply_record_overrides(sources, state_key="settings_source_overrides", id_field="source_id")
    status_overrides = st.session_state.setdefault("settings_source_status_overrides", {})
    for source in sources:
        source["status"] = status_overrides.get(source["source_id"], source["status"])

    _render_page_frame_start(
        title="Settings > Data & Sources",
        subtitle="Manage data sources, measurement mappings, refresh schedules and data quality.",
        active_label="SOURCE GOVERNANCE",
    )
    _render_top_actions(
        [
            ("Test Connection", "settings_source_top_test"),
            ("+ Add Source", "settings_source_top_add"),
            ("Export", "settings_source_top_export"),
        ],
        payload=sources,
        export_name="data_sources_settings_view.json",
        page="data_sources",
    )
    active_tab = _render_subtabs(
        ["Data Sources", "Source Groups", "Measurement Mappings", "Refresh Schedules", "Data Quality Rules"],
        "Data Sources",
        key="settings_sources_active_tab",
    )

    _metric_strip(
        [
            ("Total Sources", len(sources), "up 2 vs last 7d", "info"),
            ("Active", _count_where(sources, "status", "Active"), "85%", "good"),
            ("Degraded", _count_where(sources, "status", "Degraded"), "8%", "warn"),
            ("Down", _count_where(sources, "status", "Down"), "8%", "danger"),
            ("Avg Freshness", f"{_average_minutes(sources, 'freshness_minutes')}m", "LIVE", "good"),
            ("Avg Precision Score", f"{_average_float(sources, 'precision_score'):.2f}", "Good", "good"),
            ("Coverage (Markets)", f"{_average_float(sources, 'coverage_ratio') * 100:.0f}%", "up 2%", "good"),
        ]
    )
    _render_settings_result_banner(
        "data_sources",
        fallback_title="Source Registry Ready",
        fallback_message="Use the filters and action buttons below to inspect, test, enable, disable, or refresh sources.",
    )

    if active_tab != "Data Sources":
        _render_data_sources_secondary_tab(active_tab, sources)
        _render_page_frame_end()
        return

    filters = st.columns([1.4, 1, 1, 1, 1], gap="small")
    query = filters[0].text_input("Search sources", placeholder="Source, provider, type...", key="settings_source_query")
    status_filter = filters[1].selectbox("Status", ["All", *_unique(sources, "status")], key="settings_source_status")
    type_filter = filters[2].selectbox("Type", ["All", *_unique(sources, "source_type")], key="settings_source_type")
    provider_filter = filters[3].selectbox("Provider", ["All", *_unique(sources, "provider")], key="settings_source_provider")
    priority_filter = filters[4].selectbox("Priority", ["All", *_unique(sources, "priority_level")], key="settings_source_priority")

    filtered = _filter_records(
        sources,
        query=query,
        query_fields=["source_name", "provider", "primary_use", "source_type"],
        exact_filters={"status": status_filter, "source_type": type_filter, "provider": provider_filter, "priority_level": priority_filter},
    )
    selected_source = _select_record(filtered, label_field="source_name", key="settings_selected_source", empty_message="No sources match the current filters.")
    _write_settings_page_context(
        source_page="settings",
        target_page="data_sources",
        entry_reason="inspect_source",
        entry_context={
            "active_tab": active_tab,
            "selected_source_id": (selected_source or {}).get("source_id"),
            "selected_source_name": (selected_source or {}).get("source_name"),
            "selected_source_type": (selected_source or {}).get("source_type"),
        },
    )
    _current_page_context_summary(
        "Data & Sources",
        active_tab,
        str((selected_source or {}).get("source_name") or "None"),
        str((selected_source or {}).get("source_id") or "-"),
    )

    left, right = st.columns([0.76, 0.24], gap="medium")
    with left:
        _render_sources_table(filtered, selected_source)
        _action_bar_source(selected_source)
    with right:
        _render_source_detail(selected_source)
        _render_source_editor(selected_source)

    _render_page_frame_end()


def render_system_settings_page() -> None:
    _render_settings_theme()
    system = _build_system_state()
    services = system["services"]

    _apply_record_overrides(services, state_key="settings_service_overrides", id_field="service_id")
    status_overrides = st.session_state.setdefault("settings_service_status_overrides", {})
    for service in services:
        service["status"] = status_overrides.get(service["service_id"], service["status"])

    _render_page_frame_start(
        title="Settings > System",
        subtitle="System health, performance, system configuration and maintenance.",
        active_label="SYSTEM ADMIN",
    )
    _render_top_actions(
        [
            ("Restart Services", "settings_system_top_restart"),
            ("Clear Cache", "settings_system_top_clear"),
            ("Run Diagnostics", "settings_system_top_diagnostics"),
            ("Download Logs", "settings_system_top_download"),
        ],
        payload=system,
        export_name="system_logs_snapshot.json",
        page="system",
    )
    active_tab = _render_subtabs(
        ["System Health", "Performance", "Configuration", "Users & Access", "Audit Logs", "Maintenance"],
        "System Health",
        key="settings_system_active_tab",
    )

    _metric_strip(
        [
            ("Overall Status", system["overall_status"], "All systems operational", "good"),
            ("CPU Usage", system["cpu"], "Normal", "info"),
            ("Memory Usage", system["memory"], "Normal", "info"),
            ("Disk Usage", system["disk"], "Normal", "info"),
            ("Services", f"{_count_where(services, 'status', 'Running')} / {len(services)}", "Running", "good"),
            ("Errors (24h)", system["errors_24h"], "down 6", "danger"),
            ("Alerts (24h)", system["alerts_24h"], "down 11", "warn"),
        ]
    )
    _render_settings_result_banner(
        "system",
        fallback_title="System Controls Ready",
        fallback_message="Use the filters and action buttons below to inspect services and issue audited maintenance actions.",
    )

    if active_tab != "System Health":
        _render_system_secondary_tab(active_tab, system)
        _render_page_frame_end()
        return

    filters = st.columns([1.6, 1, 1, 1.4], gap="small")
    query = filters[0].text_input("Search services", placeholder="Service, component, version...", key="settings_system_query")
    status_filter = filters[1].selectbox("Status", ["All", *_unique(services, "status")], key="settings_system_status")
    component_filter = filters[2].selectbox("Component", ["All", *_unique(services, "component")], key="settings_system_component")
    if filters[3].button("Run Diagnostics", key="settings_system_run_diagnostics", use_container_width=True):
        _write_settings_audit("run_diagnostics", page="system", detail={"status": system["overall_status"]})
        st.session_state["settings_last_diagnostics"] = datetime.now(timezone.utc).isoformat()
        st.toast("Diagnostics request recorded.")

    filtered = _filter_records(
        services,
        query=query,
        query_fields=["service_name", "service_id", "component", "version"],
        exact_filters={"status": status_filter, "component": component_filter},
    )
    selected_service = _select_record(filtered, label_field="service_name", key="settings_selected_service", empty_message="No services match the current filters.")
    _write_settings_page_context(
        source_page="settings",
        target_page="system",
        entry_reason="inspect_service",
        entry_context={
            "active_tab": active_tab,
            "selected_service_id": (selected_service or {}).get("service_id"),
            "selected_service_name": (selected_service or {}).get("service_name"),
            "selected_service_status": (selected_service or {}).get("status"),
        },
    )
    _current_page_context_summary(
        "System",
        active_tab,
        str((selected_service or {}).get("service_name") or "None"),
        str((selected_service or {}).get("service_id") or "-"),
    )

    left, mid, right = st.columns([0.30, 0.42, 0.28], gap="medium")
    with left:
        _render_services_table(filtered, selected_service)
        _action_bar_system(selected_service)
    with mid:
        _render_system_metrics(system)
        _render_recent_events(system["recent_events"])
    with right:
        _render_system_detail(system, selected_service)
        _render_service_editor(selected_service)

    _render_page_frame_end()


def _render_settings_theme() -> None:
    st.html(
        """
        <style>
        :root {
          --set-bg:#050d16;
          --set-panel:#071726;
          --set-panel-2:#0a1d2e;
          --set-line:#1b3a52;
          --set-line-soft:rgba(95,142,176,.24);
          --set-text:#dce7ef;
          --set-muted:#9fb0bf;
          --set-cyan:#32b7ff;
          --set-blue:#0b4da3;
          --set-green:#4bd968;
          --set-red:#ff493f;
          --set-amber:#ffb020;
          --set-magenta:#b33ac8;
        }
        .settings-r5-page {margin-top:-.35rem;color:var(--set-text);font-family:"IBM Plex Sans","Aptos","Segoe UI",sans-serif;}
        .settings-r5-header {display:flex;align-items:flex-start;justify-content:space-between;border-bottom:1px solid var(--set-line-soft);padding:.1rem 0 .45rem;margin-bottom:.35rem;}
        .settings-r5-title h2 {font-size:1.05rem;line-height:1.15;margin:0;color:var(--set-text);font-weight:900;letter-spacing:.01em;}
        .settings-r5-title p {margin:.18rem 0 0;color:var(--set-muted);font-size:.70rem;}
        .settings-r5-live {font-size:.66rem;font-weight:900;color:var(--set-green);border:1px solid rgba(75,217,104,.25);background:rgba(75,217,104,.10);padding:.18rem .42rem;border-radius:4px;margin-top:.1rem;}
        .settings-strip {display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:.42rem;margin:.42rem 0 .52rem;}
        .settings-stat {min-height:58px;border:1px solid var(--set-line);border-radius:4px;background:linear-gradient(180deg,rgba(9,28,45,.96),rgba(5,17,29,.96));padding:.48rem .58rem;box-shadow:inset 0 1px 0 rgba(255,255,255,.03);}
        .settings-stat__label {font-size:.62rem;color:#a4b5c5;font-weight:750;}
        .settings-stat__value {font-size:1.18rem;color:#fff;font-weight:900;margin-top:.18rem;letter-spacing:.01em;}
        .settings-stat__delta {font-size:.58rem;margin-top:.08rem;font-weight:800;}
        .settings-stat.good .settings-stat__delta,.settings-stat.good .settings-stat__value.accent {color:var(--set-green);}
        .settings-stat.warn .settings-stat__delta,.settings-stat.warn .settings-stat__value.accent {color:var(--set-amber);}
        .settings-stat.danger .settings-stat__delta,.settings-stat.danger .settings-stat__value.accent {color:var(--set-red);}
        .settings-stat.info .settings-stat__delta,.settings-stat.info .settings-stat__value.accent {color:var(--set-cyan);}
        .settings-table-wrap,.settings-side-card,.settings-mid-card {border:1px solid var(--set-line);border-radius:5px;background:linear-gradient(180deg,rgba(8,25,40,.96),rgba(4,14,24,.98));overflow:hidden;}
        .settings-table {width:100%;border-collapse:collapse;font-size:.68rem;}
        .settings-table thead th {background:rgba(9,27,43,.86);color:#a9bbca;text-align:left;font-size:.58rem;text-transform:none;font-weight:800;padding:.44rem .48rem;border-bottom:1px solid var(--set-line);}
        .settings-table tbody td {padding:.42rem .48rem;border-bottom:1px solid rgba(95,142,176,.17);color:#dceaf5;vertical-align:middle;}
        .settings-table tbody tr.selected {background:linear-gradient(90deg,rgba(18,93,173,.72),rgba(8,34,56,.92));}
        .settings-table tbody tr:hover {background:rgba(29,84,126,.28);}
        .settings-badge {display:inline-flex;align-items:center;border-radius:3px;padding:.12rem .32rem;font-size:.55rem;font-weight:900;line-height:1;border:1px solid transparent;}
        .settings-badge.good {background:rgba(75,217,104,.16);border-color:rgba(75,217,104,.28);color:var(--set-green);}
        .settings-badge.warn {background:rgba(255,176,32,.14);border-color:rgba(255,176,32,.3);color:var(--set-amber);}
        .settings-badge.danger {background:rgba(255,73,63,.17);border-color:rgba(255,73,63,.32);color:var(--set-red);}
        .settings-badge.info {background:rgba(50,183,255,.16);border-color:rgba(50,183,255,.3);color:var(--set-cyan);}
        .settings-badge.magenta {background:rgba(179,58,200,.18);border-color:rgba(179,58,200,.32);color:#ff8dff;}
        .settings-toggle {display:inline-block;width:28px;height:14px;border-radius:999px;background:#4bd968;box-shadow:inset 0 0 0 1px rgba(255,255,255,.2);position:relative;}
        .settings-toggle::after {content:"";position:absolute;right:2px;top:2px;width:10px;height:10px;border-radius:50%;background:#dfffe6;}
        .settings-toggle.off {background:#6a7988;}
        .settings-toggle.off::after {left:2px;right:auto;background:#d9e0e8;}
        .settings-actions {display:flex;gap:.28rem;justify-content:flex-end;}
        .settings-icon-btn {width:21px;height:20px;border:1px solid rgba(129,169,202,.38);border-radius:3px;color:#d7e7f5;display:inline-flex;align-items:center;justify-content:center;font-size:.62rem;background:rgba(12,31,50,.6);}
        .settings-side-card {padding:.72rem;}
        .settings-side-head {display:flex;align-items:flex-start;justify-content:space-between;padding-bottom:.5rem;border-bottom:1px solid rgba(95,142,176,.2);margin-bottom:.55rem;}
        .settings-side-head h3 {font-size:.82rem;margin:0;color:#fff;font-weight:900;}
        .settings-side-head span {font-size:.62rem;color:var(--set-green);font-weight:900;}
        .settings-section-title {font-size:.62rem;color:#c5d4e1;font-weight:900;text-transform:uppercase;margin:.48rem 0 .35rem;}
        .settings-kv {display:grid;grid-template-columns:.9fr 1.1fr;gap:.5rem;font-size:.62rem;border-bottom:1px solid rgba(95,142,176,.14);padding:.25rem 0;color:#9fb1c2;}
        .settings-kv strong {font-weight:800;color:#f2f8ff;text-align:right;}
        .settings-chip-row {display:flex;gap:.28rem;flex-wrap:wrap;margin:.25rem 0;}
        .settings-quality-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.35rem;margin:.38rem 0;}
        .settings-quality {border:1px solid rgba(95,142,176,.24);border-radius:4px;padding:.4rem;background:rgba(6,20,33,.8);}
        .settings-quality span {display:block;font-size:.56rem;color:#9fb1c2;}
        .settings-quality strong {display:block;font-size:.92rem;color:#fff;margin-top:.1rem;}
        .settings-quality em {display:block;font-size:.56rem;color:var(--set-green);font-style:normal;}
        .settings-progress {height:5px;background:rgba(95,142,176,.22);border-radius:999px;overflow:hidden;min-width:70px;}
        .settings-progress span {display:block;height:100%;background:linear-gradient(90deg,var(--set-green),#97ee68);}
        .settings-metrics-chart {height:210px;border:1px solid rgba(95,142,176,.24);border-radius:4px;background:
          linear-gradient(180deg,rgba(255,255,255,.04) 1px,transparent 1px) 0 0/100% 25%,
          linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px) 0 0/12.5% 100%,
          radial-gradient(circle at 18% 58%,rgba(50,183,255,.35) 0 2px,transparent 2px),
          radial-gradient(circle at 36% 45%,rgba(255,176,32,.35) 0 2px,transparent 2px),
          radial-gradient(circle at 52% 70%,rgba(179,58,200,.36) 0 2px,transparent 2px),
          radial-gradient(circle at 72% 36%,rgba(255,73,63,.36) 0 2px,transparent 2px),
          linear-gradient(180deg,rgba(8,25,40,.96),rgba(4,14,24,.98));
          position:relative;overflow:hidden;}
        .settings-metrics-chart::before {content:"";position:absolute;inset:18px 14px 24px;background:
          linear-gradient(110deg,transparent 0 5%,rgba(50,183,255,.9) 5% 6%,transparent 6% 22%,rgba(255,176,32,.9) 22% 23%,transparent 23% 41%,rgba(255,73,63,.9) 41% 42%,transparent 42% 66%,rgba(179,58,200,.9) 66% 67%,transparent 67%);
          clip-path:polygon(0 58%,10% 52%,20% 63%,30% 44%,42% 50%,52% 72%,64% 38%,75% 48%,88% 35%,100% 42%,100% 46%,88% 39%,75% 52%,64% 42%,52% 76%,42% 54%,30% 48%,20% 67%,10% 56%,0 62%);}
        .settings-event-row {display:grid;grid-template-columns:58px 48px 1fr;gap:.45rem;font-size:.62rem;border-bottom:1px solid rgba(95,142,176,.14);padding:.3rem 0;color:#cbd8e3;}
        .settings-footer-note {color:#7890a5;font-size:.58rem;margin-top:.34rem;}
        </style>
        """
    )


def _render_page_frame_start(*, title: str, subtitle: str, active_label: str) -> None:
    st.html(
        f"""
        <div class="settings-r5-page">
          <div class="settings-r5-header">
            <div class="settings-r5-title"><h2>{_esc(title)}</h2><p>{_esc(subtitle)}</p></div>
            <div class="settings-r5-live">{_esc(active_label)}</div>
          </div>
        </div>
        """
    )


def _render_settings_context_strip(active_tab: str, selection_label: str, selection_value: str, action_hint: str) -> None:
    st.html(
        f"""
        <div class="settings-mid-card" style="padding:.58rem .68rem;margin:.1rem 0 .45rem;">
          <div class="settings-section-title" style="margin-top:0;">Current Context</div>
          <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.4rem;">
            <div class="settings-kv"><span>Page</span><strong>{_esc(active_tab)}</strong></div>
            <div class="settings-kv"><span>Selection</span><strong>{_esc(selection_label)}</strong></div>
            <div class="settings-kv"><span>Value</span><strong>{_esc(selection_value)}</strong></div>
            <div class="settings-kv"><span>Action</span><strong>{_esc(action_hint)}</strong></div>
          </div>
        </div>
        """
    )


def _set_settings_result(page: str, *, title: str, message: str, tone: str) -> None:
    st.session_state.setdefault("settings_page_results", {})[page] = {
        "title": title,
        "message": message,
        "tone": tone,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def _tone_hex(tone: str) -> str:
    mapping = {
        "good": "#4bd968",
        "warn": "#ffb020",
        "danger": "#ff493f",
        "info": "#32b7ff",
        "magenta": "#b33ac8",
    }
    return mapping.get(str(tone or "").lower(), "#32b7ff")


def _render_page_frame_end() -> None:
    st.html('<div class="settings-footer-note">Settings changes are registry-first and audit logged. Settings never directly change gate allow state.</div>')


def _render_settings_result_banner(page: str, *, fallback_title: str, fallback_message: str) -> None:
    result = st.session_state.get("settings_page_results", {})
    page_result = result.get(page) if isinstance(result, dict) else {}
    if not isinstance(page_result, dict) or not page_result:
        page_result = {
            "title": fallback_title,
            "message": fallback_message,
            "tone": "info",
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
    tone = str(page_result.get("tone") or "info")
    title = str(page_result.get("title") or fallback_title)
    message = str(page_result.get("message") or fallback_message)
    updated_at = str(page_result.get("updated_at") or "-")
    st.html(
        f"""
        <div class="settings-mid-card" style="padding:.58rem .68rem;margin:.1rem 0 .45rem;border-left:4px solid {_tone_hex(tone)};">
          <div class="settings-section-title" style="margin-top:0;">Last Action Result</div>
          <div class="settings-kv"><span>State</span><strong>{_esc(title)}</strong></div>
          <div class="settings-kv"><span>Message</span><strong>{_esc(message)}</strong></div>
          <div class="settings-kv"><span>Updated</span><strong>{_esc(updated_at)}</strong></div>
        </div>
        """
    )


def _render_top_actions(actions: list[tuple[str, str]], *, payload: Any, export_name: str, page: str) -> None:
    cols = st.columns([1] * len(actions) + [6], gap="small")
    for idx, (label, key) in enumerate(actions):
        if "Export" in label or "Download" in label:
            cols[idx].download_button(
                label,
                data=json.dumps(payload, ensure_ascii=False, indent=2),
                file_name=export_name,
                mime="application/json",
                key=key,
                use_container_width=True,
            )
            continue
        if cols[idx].button(label, key=key, use_container_width=True):
            action = _key(label).lower()
            result_title = f"{label} completed" if label.startswith("+") else f"{label} queued"
            result_message = f"{label} request recorded."
            if "new_rule" in key:
                st.session_state["settings_alert_rule_draft"] = {"rule_id": f"draft_{_utc_compact()}", "status": "Testing"}
                result_title = "Draft created"
                result_message = "New alert rule draft created locally."
            if "add" in key:
                st.session_state["settings_source_draft"] = {"source_id": f"draft_source_{_utc_compact()}", "status": "Testing"}
                result_title = "Source draft created"
                result_message = "New source draft created locally."
            if "diagnostics" in key:
                st.session_state["settings_last_diagnostics"] = datetime.now(timezone.utc).isoformat()
                result_title = "Diagnostics recorded"
                result_message = "Diagnostics request recorded."
            _write_settings_audit(action, page=page)
            _set_settings_result(page, title=result_title, message=result_message, tone="info")
            st.toast(f"{label} request recorded.")


def _render_subtabs(labels: list[str], active: str, *, key: str) -> str:
    return st.selectbox(
        "Settings section",
        labels,
        index=labels.index(active) if active in labels else 0,
        key=key,
    )


def _metric_strip(items: list[tuple[str, Any, str, str]]) -> None:
    st.html(
        '<div class="settings-strip">'
        + "".join(
            f"""
            <div class="settings-stat {_esc(tone)}">
              <div class="settings-stat__label">{_esc(label)}</div>
              <div class="settings-stat__value {'accent' if tone in {'good','warn','danger','info'} else ''}">{_esc(value)}</div>
              <div class="settings-stat__delta">{_esc(delta)}</div>
            </div>
            """
            for label, value, delta, tone in items
        )
        + "</div>"
    )


def _select_record(records: list[dict[str, Any]], *, label_field: str, key: str, empty_message: str) -> dict[str, Any] | None:
    if not records:
        st.warning(empty_message)
        return None
    labels = [str(record.get(label_field) or record.get("rule_id") or record.get("source_id") or record.get("service_id") or "-") for record in records]
    selected_label = st.selectbox("Selected row", labels, key=key, label_visibility="collapsed")
    return records[labels.index(selected_label)]


def _render_alert_rules_table(records: list[dict[str, Any]], selected: dict[str, Any] | None) -> None:
    selected_id = str((selected or {}).get("rule_id") or "")
    rows = []
    for index, rule in enumerate(records[:14], start=1):
        row_class = "selected" if str(rule.get("rule_id")) == selected_id else ""
        rows.append(
            f"""
            <tr class="{row_class}">
              <td>{index}</td>
              <td><strong>{_esc(rule.get('rule_name'))}</strong></td>
              <td>{_badge(rule.get('type'), _type_tone(rule.get('type')))}</td>
              <td>{_esc(rule.get('target'))}</td>
              <td>{_badge(rule.get('severity'), _severity_tone(rule.get('severity')))}</td>
              <td><code>{_esc(rule.get('condition'))}</code></td>
              <td>{_esc(rule.get('throttle'))}</td>
              <td><div class="settings-chip-row">{''.join(_mini_action(action) for action in rule.get('actions', []))}</div></td>
              <td>{_toggle(rule.get('status') == 'Enabled')}</td>
              <td>{_esc(rule.get('last_triggered'))}</td>
              <td><div class="settings-actions">{_icon('E')}{_icon('C')}{_icon('D')}</div></td>
            </tr>
            """
        )
    _html_table(
        ["", "Rule Name", "Type", "Target", "Severity", "Condition", "Throttle", "Actions", "Status", "Last Triggered", "Actions"],
        rows,
        empty="No alert rules match the current filters.",
    )


def _render_sources_table(records: list[dict[str, Any]], selected: dict[str, Any] | None) -> None:
    selected_id = str((selected or {}).get("source_id") or "")
    rows = []
    for source in records[:14]:
        row_class = "selected" if str(source.get("source_id")) == selected_id else ""
        rows.append(
            f"""
            <tr class="{row_class}">
              <td><strong>{_esc(source.get('source_name'))}</strong></td>
              <td>{_esc(source.get('provider'))}</td>
              <td>{_esc(source.get('source_type'))}</td>
              <td>{_esc(source.get('coverage_label'))}</td>
              <td>{_progress(source.get('precision_score'), suffix=f"{_float(source.get('precision_score'), default=0):.2f}")}</td>
              <td>{_esc(source.get('freshness_label'))}</td>
              <td>{_badge(source.get('status'), _status_tone(source.get('status')))}</td>
              <td>{_esc(source.get('last_update', '14:27:12'))}</td>
              <td><div class="settings-actions">{_icon('V')}{_icon('E')}{_icon('T')}{_icon('P')}</div></td>
            </tr>
            """
        )
    _html_table(
        ["Source Name", "Provider", "Type", "Coverage", "Precision Score", "Freshness", "Status", "Last Update", "Actions"],
        rows,
        empty="No sources match the current filters.",
    )


def _render_services_table(records: list[dict[str, Any]], selected: dict[str, Any] | None) -> None:
    selected_id = str((selected or {}).get("service_id") or "")
    rows = []
    for service in records[:12]:
        row_class = "selected" if str(service.get("service_id")) == selected_id else ""
        rows.append(
            f"""
            <tr class="{row_class}">
              <td><strong>{_esc(service.get('service_name'))}</strong></td>
              <td>{_badge(service.get('status'), _status_tone(service.get('status')))}</td>
              <td>{_esc(service.get('uptime'))}</td>
              <td>{_esc(service.get('version'))}</td>
            </tr>
            """
        )
    _html_table(["Service Status", "Status", "Uptime", "Version"], rows, empty="No services match the current filters.")


def _html_table(headers: list[str], rows: list[str], *, empty: str) -> None:
    if not rows:
        st.warning(empty)
        return
    st.html(
        '<div class="settings-table-wrap"><table class="settings-table"><thead><tr>'
        + "".join(f"<th>{_esc(header)}</th>" for header in headers)
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def _html_table_raw(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        rows = [["-", "-", "-"]]
    return (
        '<div class="settings-table-wrap"><table class="settings-table"><thead><tr>'
        + "".join(f"<th>{_esc(header)}</th>" for header in headers)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>" + "".join(f"<td>{_esc(cell)}</td>" for cell in row) + "</tr>"
            for row in rows
        )
        + "</tbody></table></div>"
    )


def _section_card(title: str, body: str) -> str:
    return f"<div class='settings-side-card'><div class='settings-section-title'>{_esc(title)}</div>{body}</div>"


def _render_alert_rule_detail(rule: dict[str, Any] | None, ops_alerts: list[dict[str, Any]]) -> None:
    rule = rule or {}
    recent = ops_alerts[:3] or [
        {"generated_at": "2026-04-24 14:33", "primary_reason": "NY Rainfall > 50mm", "severity": "18.2%"},
        {"generated_at": "2026-04-24 14:28", "primary_reason": "Tokyo Snowfall > 10cm", "severity": "16.7%"},
        {"generated_at": "2026-04-24 13:58", "primary_reason": "Houston Temp > 30C", "severity": "15.6%"},
    ]
    st.html(
        f"""
        <div class="settings-side-card">
          <div class="settings-side-head"><h3>{_esc(rule.get('rule_name', 'Rule Detail'))}</h3><span>{_esc(rule.get('status','-'))}</span></div>
          <div class="settings-section-title">Rule Overview</div>
          {_kv('Type', rule.get('type'))}
          {_kv('Severity', _badge(rule.get('severity'), _severity_tone(rule.get('severity'))), raw=True)}
          {_kv('Target', rule.get('target'))}
          {_kv('Created', '2026-03-18 11:22 UTC')}
          {_kv('Updated', '2026-04-21 09:33 UTC')}
          <div class="settings-section-title">Condition</div>
          <div style="font-size:.64rem;color:#dceaf5;border-top:1px solid rgba(95,142,176,.16);border-bottom:1px solid rgba(95,142,176,.16);padding:.42rem 0;"><code>{_esc(rule.get('condition','-'))}</code></div>
          <div class="settings-section-title">Throttle & Suppression</div>
          {_kv('Throttle window', rule.get('throttle'))}
          {_kv('Max alerts / window', '1 per market')}
          {_kv('Suppress if', 'Market is paused')}
          <div class="settings-section-title">Actions</div>
          <div class="settings-chip-row">{''.join(_action_chip(action) for action in rule.get('actions', []))}</div>
          <div class="settings-section-title">Recent Triggers</div>
          {''.join(_trigger_row(item) for item in recent)}
        </div>
        """
    )


def _render_alerts_rules_secondary_tab(tab: str, rules: list[dict[str, Any]], ops_alerts: list[dict[str, Any]]) -> None:
    if tab == "Notification Channels":
        channels = _notification_channel_rows()
        selected = _select_record(channels, label_field="channel", key="settings_selected_channel", empty_message="No notification channels available.")
        left, right = st.columns([0.68, 0.32], gap="medium")
        with left:
            st.html(_section_card("Notification Channel Registry", _html_table_raw(["Channel", "Status", "Scope", "Latency", "24h"], [[row["channel"], row["status"], row["scope"], row["latency"], row["sent_24h"]] for row in channels])))
        with right:
            _render_notification_channel_editor(selected)
        return
    if tab == "Routing Policies":
        policies = [[rule.get("rule_name"), ", ".join(rule.get("actions", [])), rule.get("severity"), rule.get("throttle")] for rule in rules]
        st.html(_section_card("Routing Policies", _html_table_raw(["Rule", "Channels", "Severity", "Throttle"], policies)))
        return
    if tab == "Snooze Schedule":
        schedules = [
            ["source_down", "Market paused", "30m", "auto_expire"],
            ["data_freshness_stale", "Known source lag", "1h", "manual_ack"],
            ["liquidity_drop", "Low activity window", "24h", "watch_only"],
        ]
        st.html(_section_card("Snooze / Suppression Schedule", _html_table_raw(["Rule", "Reason", "Window", "Closure"], schedules)))
        return
    history = []
    for item in ops_alerts[:12]:
        history.append([
            str(item.get("generated_at") or item.get("event_at") or "-")[:19],
            item.get("severity") or "-",
            item.get("primary_reason") or item.get("message") or "-",
            item.get("component") or "alert_router",
        ])
    if not history:
        history = [["2026-04-24 14:33", "critical", "NY Rainfall > 50mm", "alert_router"]]
    st.html(_section_card("Alert History", _html_table_raw(["Time", "Severity", "Reason", "Component"], history)))


def _render_source_detail(source: dict[str, Any] | None) -> None:
    source = source or {}
    st.html(
        f"""
        <div class="settings-side-card">
          <div class="settings-side-head"><h3>{_esc(source.get('source_name','Source Detail'))}</h3><span>{_esc(source.get('status','-'))}</span></div>
          <div class="settings-section-title">Source Overview</div>
          {_kv('Provider', source.get('provider'))}
          {_kv('Type', source.get('source_type'))}
          {_kv('Endpoint', 'https://example.source/api')}
          {_kv('Update Interval', '5 minutes')}
          {_kv('Since', '2026-02-14 08:00 UTC')}
          <div class="settings-section-title">Quality Metrics (24h)</div>
          <div class="settings-quality-grid">
            {_quality('Precision Score', f"{_float(source.get('precision_score'), default=0):.2f}", 'Excellent')}
            {_quality('Freshness', source.get('freshness_label'), 'LIVE' if source.get('status') == 'Active' else 'Check')}
            {_quality('Uptime', '99.8%', 'Excellent')}
            {_quality('Error Rate', '0.02%', 'Excellent')}
          </div>
          <div class="settings-section-title">Coverage</div>
          {_kv('Markets Covered', f"{int(_float(source.get('coverage_ratio'), default=0) * 100)} / 100")}
          {_progress(source.get('coverage_ratio'), suffix=source.get('coverage_label'))}
          {_kv('Parameters', 'Temperature, Wind, Precip, Pressure, Visibility')}
          <div class="settings-section-title">Recent Issues</div>
          <div class="settings-kv"><span>Status</span><strong style="color:#4bd968;text-align:left;">No issues in the last 24 hours</strong></div>
        </div>
        """
    )


def _render_data_sources_secondary_tab(tab: str, sources: list[dict[str, Any]]) -> None:
    if tab == "Source Groups":
        groups = [
            ["Official Observation Stack", "METAR, official_obs", "P1", "Active"],
            ["Forecast Stack", "ECMWF, HRRR, GFS", "P1/P2", "Active"],
            ["Fallback Stack", "Open-Meteo, custom_s3", "P3", "Degraded"],
        ]
        st.html(_section_card("Source Groups / Fallback Chain", _html_table_raw(["Group", "Sources", "Priority", "Status"], groups)))
        return
    if tab == "Measurement Mappings":
        mappings = _measurement_mapping_rows()
        selected = _select_record(mappings, label_field="variable", key="settings_selected_mapping", empty_message="No measurement mappings available.")
        left, right = st.columns([0.68, 0.32], gap="medium")
        with left:
            st.html(_section_card("Measurement Mappings", _html_table_raw(["Variable", "Raw", "Canonical", "Rounding", "Policy"], [[row["variable"], row["raw"], row["canonical"], row["rounding"], row["policy"]] for row in mappings])))
        with right:
            _render_measurement_mapping_editor(selected)
        return
    if tab == "Refresh Schedules":
        schedules = [[source.get("source_name"), source.get("freshness_label"), "5m", source.get("status")] for source in sources[:12]]
        st.html(_section_card("Refresh Schedules", _html_table_raw(["Source", "Current Freshness", "Cadence", "Status"], schedules)))
        return
    rules = [
        ["missing_value", "B", "field level", "warn"],
        ["stale_source", "B", "source level", "warn"],
        ["unit_mismatch", "C", "measurement", "block compare"],
        ["outlier_raw", "B", "observation", "review"],
    ]
    st.html(_section_card("Data Quality Rules", _html_table_raw(["Rule", "Grade", "Scope", "Action"], rules)))


def _render_system_metrics(system: dict[str, Any]) -> None:
    st.html(
        f"""
        <div class="settings-mid-card" style="padding:.65rem;">
          <div class="settings-section-title">System Metrics (Last 24h)</div>
          <div class="settings-metrics-chart"></div>
          <div class="settings-chip-row">
            {_action_chip('CPU %')} {_action_chip('Memory %')} {_action_chip('Disk %')} {_action_chip('Network I/O')}
          </div>
        </div>
        """
    )


def _render_system_secondary_tab(tab: str, system: dict[str, Any]) -> None:
    if tab == "Performance":
        st.html(_section_card("Performance", "<div class='settings-metrics-chart'></div>"))
        return
    if tab == "Configuration":
        config = [
            ["Environment", system.get("system_information", {}).get("environment")],
            ["Version", system.get("system_information", {}).get("version")],
            ["Region", system.get("system_information", {}).get("region")],
            ["Auto Refresh", "15s"],
            ["Gateway Mode", "dry-run only"],
        ]
        st.html(_section_card("Runtime Configuration", _html_table_raw(["Key", "Value"], config)))
        return
    if tab == "Users & Access":
        users = _user_access_rows()
        selected = _select_record(users, label_field="user", key="settings_selected_user", empty_message="No users available.")
        left, right = st.columns([0.68, 0.32], gap="medium")
        with left:
            st.html(_section_card("Users & Access", _html_table_raw(["User", "Role", "Status"], [[row["user"], row["role"], row["status"]] for row in users])))
        with right:
            _render_user_access_editor(selected)
        return
    if tab == "Maintenance":
        st.html(_section_card("Maintenance", _html_table_raw(["Action", "Gate", "Audit"], [["Restart Services", "confirm required", "yes"], ["Clear Cache", "allowed", "yes"], ["Run Diagnostics", "allowed", "yes"], ["Download Logs", "allowed", "yes"]])))
        return
    events = system.get("recent_events") or []
    rows = [[item.get("time") or item.get("generated_at") or "-", item.get("severity") or "-", item.get("event") or item.get("message") or "-"] for item in events]
    st.html(_section_card("Audit Logs", _html_table_raw(["Time", "Severity", "Event"], rows)))


def _render_recent_events(events: list[dict[str, Any]]) -> None:
    rows = []
    for event in events[:7]:
        rows.append(
            f"""
            <div class="settings-event-row">
              <span>{_esc(event.get('time') or event.get('generated_at') or '-')}</span>
              {_badge(event.get('severity', 'INFO'), _severity_tone(event.get('severity', 'INFO')))}
              <span>{_esc(event.get('event') or event.get('primary_reason') or event.get('message') or '-')}</span>
            </div>
            """
        )
    st.html(f'<div class="settings-mid-card" style="padding:.65rem;margin-top:.55rem;"><div class="settings-section-title">Recent Events</div>{"".join(rows)}</div>')


def _render_system_detail(system: dict[str, Any], service: dict[str, Any] | None) -> None:
    service = service or {}
    info = system.get("system_information", {})
    st.html(
        f"""
        <div class="settings-side-card">
          <div class="settings-side-head"><h3>System Information</h3><span>{_esc(system.get('overall_status'))}</span></div>
          {_kv('Environment', info.get('environment'))}
          {_kv('Version', info.get('version'))}
          {_kv('Region', info.get('region'))}
          {_kv('Deployed At', info.get('deployed_at'))}
          {_kv('Uptime', info.get('uptime'))}
          <div class="settings-section-title">Selected Service</div>
          {_kv('Service', service.get('service_name'))}
          {_kv('Status', _badge(service.get('status'), _status_tone(service.get('status'))), raw=True)}
          {_kv('Health Score', f"{_float(service.get('health_score'), default=0) * 100:.0f}%")}
          <div class="settings-section-title">Quick Actions</div>
          <div class="settings-chip-row">{_action_chip('Restart Services')}{_action_chip('Clear Cache')}{_action_chip('Run Diagnostics')}{_action_chip('Download Logs')}</div>
        </div>
        """
    )


def _render_alert_rule_editor(rule: dict[str, Any] | None) -> None:
    rule = rule or {}
    rule_id = str(rule.get("rule_id") or "")
    st.markdown("**Rule Controls**")
    if not rule_id:
        st.caption("Select a rule to edit local registry overrides.")
        return
    status = st.selectbox(
        "Rule Status",
        ["Enabled", "Disabled", "Testing"],
        index=["Enabled", "Disabled", "Testing"].index(str(rule.get("status") or "Enabled")) if str(rule.get("status") or "Enabled") in {"Enabled", "Disabled", "Testing"} else 0,
        key=f"settings_rule_status_edit_{_key(rule_id)}",
    )
    severity = st.selectbox(
        "Rule Severity",
        ["Critical", "High", "Medium", "Low"],
        index=["Critical", "High", "Medium", "Low"].index(str(rule.get("severity") or "Medium")) if str(rule.get("severity") or "Medium") in {"Critical", "High", "Medium", "Low"} else 2,
        key=f"settings_rule_severity_edit_{_key(rule_id)}",
    )
    throttle = st.text_input(
        "Throttle Window",
        value=str(rule.get("throttle") or "5m"),
        key=f"settings_rule_throttle_edit_{_key(rule_id)}",
    )
    actions = st.multiselect(
        "Notification Channels",
        ["Telegram", "Dashboard", "Ops Log", "Email", "Webhook"],
        default=[item for item in (rule.get("actions") or []) if item in {"Telegram", "Dashboard", "Ops Log", "Email", "Webhook"}],
        key=f"settings_rule_actions_edit_{_key(rule_id)}",
    )
    cols = st.columns(2, gap="small")
    if cols[0].button("Save Rule Changes", key=f"settings_rule_save_{_key(rule_id)}", use_container_width=True):
        _store_record_override(
            state_key="settings_alert_rule_overrides",
            record_id=rule_id,
            patch={"status": status, "severity": severity, "throttle": throttle, "actions": actions},
        )
        st.session_state.setdefault("settings_alert_rule_status", {})[rule_id] = status
        _write_settings_audit("update_rule_config", page="alerts_rules", detail={"rule_id": rule_id, "fields": ["status", "severity", "throttle", "actions"]})
        _set_settings_result("alerts_rules", title="Rule updated", message=f"{rule.get('rule_name', rule_id)} local overrides saved.", tone="good")
        st.rerun()
    if cols[1].button("Reset Rule Overrides", key=f"settings_rule_reset_{_key(rule_id)}", use_container_width=True):
        _clear_record_override(state_key="settings_alert_rule_overrides", record_id=rule_id)
        st.session_state.setdefault("settings_alert_rule_status", {}).pop(rule_id, None)
        _write_settings_audit("reset_rule_override", page="alerts_rules", detail={"rule_id": rule_id})
        _set_settings_result("alerts_rules", title="Rule reset", message=f"{rule.get('rule_name', rule_id)} reverted to base registry values.", tone="info")
        st.rerun()


def _render_source_editor(source: dict[str, Any] | None) -> None:
    source = source or {}
    source_id = str(source.get("source_id") or "")
    st.markdown("**Source Controls**")
    if not source_id:
        st.caption("Select a source to edit local registry overrides.")
        return
    status_options = ["Active", "Degraded", "Down", "Testing"]
    priority_options = ["P1", "P2", "P3", "CRITICAL"]
    status = st.selectbox(
        "Source Status",
        status_options,
        index=status_options.index(str(source.get("status") or "Active")) if str(source.get("status") or "Active") in status_options else 0,
        key=f"settings_source_status_edit_{_key(source_id)}",
    )
    priority = st.selectbox(
        "Priority Level",
        priority_options,
        index=priority_options.index(str(source.get("priority_level") or "P1").upper()) if str(source.get("priority_level") or "P1").upper() in priority_options else 0,
        key=f"settings_source_priority_edit_{_key(source_id)}",
    )
    freshness = st.number_input(
        "Freshness Minutes",
        min_value=0,
        max_value=1440,
        value=int(_float(source.get("freshness_minutes"), default=5)),
        step=1,
        key=f"settings_source_freshness_edit_{_key(source_id)}",
    )
    cols = st.columns(2, gap="small")
    if cols[0].button("Save Source Changes", key=f"settings_source_save_{_key(source_id)}", use_container_width=True):
        _store_record_override(
            state_key="settings_source_overrides",
            record_id=source_id,
            patch={"status": status, "priority_level": priority, "freshness_minutes": freshness, "freshness_label": f"{freshness}m"},
        )
        st.session_state.setdefault("settings_source_status_overrides", {})[source_id] = status
        _write_settings_audit("update_source_config", page="data_sources", detail={"source_id": source_id, "fields": ["status", "priority_level", "freshness_minutes"]})
        _set_settings_result("data_sources", title="Source updated", message=f"{source.get('source_name', source_id)} local overrides saved.", tone="good")
        st.rerun()
    if cols[1].button("Reset Source Overrides", key=f"settings_source_reset_{_key(source_id)}", use_container_width=True):
        _clear_record_override(state_key="settings_source_overrides", record_id=source_id)
        st.session_state.setdefault("settings_source_status_overrides", {}).pop(source_id, None)
        _write_settings_audit("reset_source_override", page="data_sources", detail={"source_id": source_id})
        _set_settings_result("data_sources", title="Source reset", message=f"{source.get('source_name', source_id)} reverted to base registry values.", tone="info")
        st.rerun()


def _render_service_editor(service: dict[str, Any] | None) -> None:
    service = service or {}
    service_id = str(service.get("service_id") or "")
    st.markdown("**Service Controls**")
    if not service_id:
        st.caption("Select a service to edit local runtime overrides.")
        return
    status_options = ["Running", "Degraded", "Down", "Testing"]
    status = st.selectbox(
        "Service Status",
        status_options,
        index=status_options.index(str(service.get("status") or "Running")) if str(service.get("status") or "Running") in status_options else 0,
        key=f"settings_service_status_edit_{_key(service_id)}",
    )
    version = st.text_input(
        "Service Version",
        value=str(service.get("version") or "v3.2.0"),
        key=f"settings_service_version_edit_{_key(service_id)}",
    )
    component = st.text_input(
        "Service Component",
        value=str(service.get("component") or "-"),
        key=f"settings_service_component_edit_{_key(service_id)}",
    )
    cols = st.columns(2, gap="small")
    if cols[0].button("Save Service Changes", key=f"settings_service_save_{_key(service_id)}", use_container_width=True):
        _store_record_override(
            state_key="settings_service_overrides",
            record_id=service_id,
            patch={"status": status, "version": version, "component": component},
        )
        st.session_state.setdefault("settings_service_status_overrides", {})[service_id] = status
        _write_settings_audit("update_service_config", page="system", detail={"service_id": service_id, "fields": ["status", "version", "component"]})
        _set_settings_result("system", title="Service updated", message=f"{service.get('service_name', service_id)} local overrides saved.", tone="good")
        st.rerun()
    if cols[1].button("Reset Service Overrides", key=f"settings_service_reset_{_key(service_id)}", use_container_width=True):
        _clear_record_override(state_key="settings_service_overrides", record_id=service_id)
        st.session_state.setdefault("settings_service_status_overrides", {}).pop(service_id, None)
        _write_settings_audit("reset_service_override", page="system", detail={"service_id": service_id})
        _set_settings_result("system", title="Service reset", message=f"{service.get('service_name', service_id)} reverted to base runtime values.", tone="info")
        st.rerun()


def _render_notification_channel_editor(channel: dict[str, Any] | None) -> None:
    channel = channel or {}
    channel_id = str(channel.get("channel") or "")
    st.markdown("**Channel Controls**")
    if not channel_id:
        st.caption("Select a notification channel to edit local routing overrides.")
        return
    status = st.selectbox(
        "Channel Status",
        ["Enabled", "Disabled", "Testing"],
        index=["Enabled", "Disabled", "Testing"].index(str(channel.get("status") or "Enabled")) if str(channel.get("status") or "Enabled") in {"Enabled", "Disabled", "Testing"} else 0,
        key=f"settings_channel_status_{_key(channel_id)}",
    )
    scope = st.text_input("Scope", value=str(channel.get("scope") or "All severities"), key=f"settings_channel_scope_{_key(channel_id)}")
    latency = st.text_input("Latency", value=str(channel.get("latency") or "<1s"), key=f"settings_channel_latency_{_key(channel_id)}")
    cols = st.columns(2, gap="small")
    if cols[0].button("Save Channel", key=f"settings_channel_save_{_key(channel_id)}", use_container_width=True):
        _store_record_override(
            state_key="settings_notification_channel_overrides",
            record_id=channel_id,
            patch={"status": status, "scope": scope, "latency": latency},
        )
        _write_settings_audit("update_notification_channel", page="alerts_rules", detail={"channel": channel_id, "fields": ["status", "scope", "latency"]})
        _set_settings_result("alerts_rules", title="Channel updated", message=f"{channel_id} local overrides saved.", tone="good")
        st.rerun()
    if cols[1].button("Reset Channel", key=f"settings_channel_reset_{_key(channel_id)}", use_container_width=True):
        _clear_record_override(state_key="settings_notification_channel_overrides", record_id=channel_id)
        _write_settings_audit("reset_notification_channel", page="alerts_rules", detail={"channel": channel_id})
        _set_settings_result("alerts_rules", title="Channel reset", message=f"{channel_id} reverted to base routing values.", tone="info")
        st.rerun()


def _render_measurement_mapping_editor(mapping: dict[str, Any] | None) -> None:
    mapping = mapping or {}
    mapping_id = str(mapping.get("variable") or "")
    st.markdown("**Mapping Controls**")
    if not mapping_id:
        st.caption("Select a measurement mapping to edit local policy overrides.")
        return
    canonical = st.text_input("Canonical Unit", value=str(mapping.get("canonical") or ""), key=f"settings_mapping_canonical_{_key(mapping_id)}")
    rounding = st.text_input("Rounding", value=str(mapping.get("rounding") or ""), key=f"settings_mapping_rounding_{_key(mapping_id)}")
    policy = st.text_input("Policy Ref", value=str(mapping.get("policy") or ""), key=f"settings_mapping_policy_{_key(mapping_id)}")
    cols = st.columns(2, gap="small")
    if cols[0].button("Save Mapping", key=f"settings_mapping_save_{_key(mapping_id)}", use_container_width=True):
        _store_record_override(
            state_key="settings_measurement_mapping_overrides",
            record_id=mapping_id,
            patch={"canonical": canonical, "rounding": rounding, "policy": policy},
        )
        _write_settings_audit("update_measurement_mapping", page="data_sources", detail={"variable": mapping_id, "fields": ["canonical", "rounding", "policy"]})
        _set_settings_result("data_sources", title="Mapping updated", message=f"{mapping_id} local mapping overrides saved.", tone="good")
        st.rerun()
    if cols[1].button("Reset Mapping", key=f"settings_mapping_reset_{_key(mapping_id)}", use_container_width=True):
        _clear_record_override(state_key="settings_measurement_mapping_overrides", record_id=mapping_id)
        _write_settings_audit("reset_measurement_mapping", page="data_sources", detail={"variable": mapping_id})
        _set_settings_result("data_sources", title="Mapping reset", message=f"{mapping_id} reverted to base policy mapping.", tone="info")
        st.rerun()


def _render_user_access_editor(user: dict[str, Any] | None) -> None:
    user = user or {}
    user_id = str(user.get("user") or "")
    st.markdown("**User Controls**")
    if not user_id:
        st.caption("Select a user to edit local access overrides.")
        return
    role = st.selectbox(
        "Role",
        ["Operator", "Service", "Read-only", "Admin", "Auditor"],
        index=["Operator", "Service", "Read-only", "Admin", "Auditor"].index(str(user.get("role") or "Operator")) if str(user.get("role") or "Operator") in {"Operator", "Service", "Read-only", "Admin", "Auditor"} else 0,
        key=f"settings_user_role_{_key(user_id)}",
    )
    status = st.selectbox(
        "Status",
        ["Active", "Disabled", "Testing"],
        index=["Active", "Disabled", "Testing"].index(str(user.get("status") or "Active")) if str(user.get("status") or "Active") in {"Active", "Disabled", "Testing"} else 0,
        key=f"settings_user_status_{_key(user_id)}",
    )
    cols = st.columns(2, gap="small")
    if cols[0].button("Save User", key=f"settings_user_save_{_key(user_id)}", use_container_width=True):
        _store_record_override(
            state_key="settings_user_access_overrides",
            record_id=user_id,
            patch={"role": role, "status": status},
        )
        _write_settings_audit("update_user_access", page="system", detail={"user": user_id, "fields": ["role", "status"]})
        _set_settings_result("system", title="User updated", message=f"{user_id} local access overrides saved.", tone="good")
        st.rerun()
    if cols[1].button("Reset User", key=f"settings_user_reset_{_key(user_id)}", use_container_width=True):
        _clear_record_override(state_key="settings_user_access_overrides", record_id=user_id)
        _write_settings_audit("reset_user_access", page="system", detail={"user": user_id})
        _set_settings_result("system", title="User reset", message=f"{user_id} reverted to base access settings.", tone="info")
        st.rerun()


def _action_bar_alert_rule(rule: dict[str, Any] | None) -> None:
    rule = rule or {}
    rule_id = str(rule.get("rule_id") or "none")
    is_critical = str(rule.get("severity") or "").lower() == "critical"
    confirm_disable = True
    if is_critical and rule:
        confirm_disable = st.checkbox(
            "Confirm critical rule disable",
            key=f"settings_rule_confirm_disable_{_key(rule_id)}",
            help="HMI gate: disabling a critical rule is a high-risk configuration action and must be deliberate.",
        )
    disable_decision = decide_action_visibility(
        "disable_critical_rule",
        page="alerts_rules",
        context={"confirmed": confirm_disable},
    ) if is_critical else None
    cols = st.columns(5, gap="small")
    if cols[0].button("Test Rule", key=f"settings_rule_test_{_key(rule_id)}", use_container_width=True, disabled=not rule):
        _write_settings_audit("test_rule", page="alerts_rules", detail={"rule_id": rule_id})
        _set_settings_result(
            "alerts_rules",
            title="Rule test queued",
            message=f"Test queued for {rule.get('rule_name', rule_id)}.",
            tone="info",
        )
        st.toast(f"Test queued for {rule.get('rule_name', rule_id)}.")
    if cols[1].button("Enable", key=f"settings_rule_enable_{_key(rule_id)}", use_container_width=True, disabled=not rule):
        st.session_state.setdefault("settings_alert_rule_status", {})[rule_id] = "Enabled"
        _write_settings_audit("enable_rule", page="alerts_rules", detail={"rule_id": rule_id})
        _set_settings_result(
            "alerts_rules",
            title="Rule enabled",
            message=f"{rule.get('rule_name', rule_id)} is now Enabled.",
            tone="good",
        )
        st.rerun()
    if cols[2].button(
        "Disable",
        key=f"settings_rule_disable_{_key(rule_id)}",
        use_container_width=True,
        disabled=(not rule or (disable_decision.disabled if disable_decision else False)),
        help=(disable_decision.reason if disable_decision and disable_decision.disabled else None),
    ):
        st.session_state.setdefault("settings_alert_rule_status", {})[rule_id] = "Disabled"
        _write_settings_audit("disable_rule", page="alerts_rules", detail={"rule_id": rule_id, "requires_confirmation": is_critical})
        _set_settings_result(
            "alerts_rules",
            title="Rule disabled",
            message=f"{rule.get('rule_name', rule_id)} is now Disabled.",
            tone="warn" if is_critical else "info",
        )
        st.rerun()
    cols[3].download_button("Export Rule", data=json.dumps(rule, indent=2, ensure_ascii=False), file_name=f"{_key(rule_id)}.json", mime="application/json", key=f"settings_rule_export_{_key(rule_id)}", use_container_width=True, disabled=not rule)
    if cols[4].button("New Draft", key="settings_rule_new_draft", use_container_width=True):
        st.session_state["settings_alert_rule_draft"] = {"rule_id": f"draft_{_utc_compact()}", "status": "Testing"}
        _write_settings_audit("new_rule_draft", page="alerts_rules")
        _set_settings_result(
            "alerts_rules",
            title="Draft created",
            message="New draft rule created locally.",
            tone="info",
        )
        st.toast("Draft rule created locally.")


def _action_bar_source(source: dict[str, Any] | None) -> None:
    source = source or {}
    source_id = str(source.get("source_id") or "none")
    source_priority = str(source.get("priority_level") or "").upper()
    is_critical_source = source_priority in {"P1", "CRITICAL"}
    confirm_disable = True
    if is_critical_source and source:
        confirm_disable = st.checkbox(
            "Confirm critical source disable",
            key=f"settings_source_confirm_disable_{_key(source_id)}",
            help="HMI gate: disabling a P1 source can degrade evidence freshness and must be deliberate.",
        )
    disable_decision = decide_action_visibility(
        "disable_critical_source",
        page="data_sources",
        context={"confirmed": confirm_disable},
    ) if is_critical_source else None
    cols = st.columns(5, gap="small")
    if cols[0].button("Test Connection", key=f"settings_source_test_{_key(source_id)}", use_container_width=True, disabled=not source):
        _write_settings_audit("test_source_connection", page="data_sources", detail={"source_id": source_id})
        _set_settings_result(
            "data_sources",
            title="Connection test queued",
            message=f"Connection test queued for {source.get('source_name', source_id)}.",
            tone="info",
        )
        st.toast(f"Connection test queued for {source.get('source_name', source_id)}.")
    if cols[1].button("Refresh Now", key=f"settings_source_refresh_{_key(source_id)}", use_container_width=True, disabled=not source):
        _write_settings_audit("refresh_source", page="data_sources", detail={"source_id": source_id})
        _set_settings_result(
            "data_sources",
            title="Refresh requested",
            message=f"Refresh request recorded for {source.get('source_name', source_id)}.",
            tone="info",
        )
        st.toast("Refresh request recorded.")
    if cols[2].button("Enable", key=f"settings_source_enable_{_key(source_id)}", use_container_width=True, disabled=not source):
        st.session_state.setdefault("settings_source_status_overrides", {})[source_id] = "Active"
        _write_settings_audit("enable_source", page="data_sources", detail={"source_id": source_id})
        _set_settings_result(
            "data_sources",
            title="Source enabled",
            message=f"{source.get('source_name', source_id)} is now Active.",
            tone="good",
        )
        st.rerun()
    if cols[3].button(
        "Disable",
        key=f"settings_source_disable_{_key(source_id)}",
        use_container_width=True,
        disabled=(not source or (disable_decision.disabled if disable_decision else False)),
        help=(disable_decision.reason if disable_decision and disable_decision.disabled else None),
    ):
        st.session_state.setdefault("settings_source_status_overrides", {})[source_id] = "Down"
        _write_settings_audit("disable_source", page="data_sources", detail={"source_id": source_id, "requires_confirmation": is_critical_source})
        _set_settings_result(
            "data_sources",
            title="Source disabled",
            message=f"{source.get('source_name', source_id)} is now Down.",
            tone="warn" if is_critical_source else "info",
        )
        st.rerun()
    cols[4].download_button("Export Source", data=json.dumps(source, indent=2, ensure_ascii=False), file_name=f"{_key(source_id)}.json", mime="application/json", key=f"settings_source_export_{_key(source_id)}", use_container_width=True, disabled=not source)


def _action_bar_system(service: dict[str, Any] | None) -> None:
    service = service or {}
    service_id = str(service.get("service_id") or "none")
    confirm_maintenance = st.checkbox(
        "Confirm maintenance action",
        key=f"settings_service_confirm_maintenance_{_key(service_id)}",
        disabled=not service,
        help="Required for restart, cache-clear, or degradation actions. This records an audit event; it does not bypass runtime gates.",
    )
    maintenance_decision = decide_action_visibility(
        "system_maintenance",
        page="system",
        context={"confirmed": confirm_maintenance},
    )
    cols = st.columns(5, gap="small")
    if cols[0].button(
        "Restart",
        key=f"settings_service_restart_{_key(service_id)}",
        use_container_width=True,
        disabled=(not service or maintenance_decision.disabled),
        help=maintenance_decision.reason if maintenance_decision.disabled else None,
    ):
        st.session_state.setdefault("settings_service_status_overrides", {})[service_id] = "Running"
        _write_settings_audit("restart_service", page="system", detail={"service_id": service_id, "requires_confirmation": True})
        _set_settings_result(
            "system",
            title="Restart requested",
            message=f"Restart request recorded for {service.get('service_name', service_id)}.",
            tone="warn",
        )
        st.toast(f"Restart request recorded for {service.get('service_name', service_id)}.")
    if cols[1].button("View Logs", key=f"settings_service_logs_{_key(service_id)}", use_container_width=True, disabled=not service):
        _write_settings_audit("view_service_logs", page="system", detail={"service_id": service_id})
        _set_settings_result(
            "system",
            title="Logs opened",
            message=f"Service logs view requested for {service.get('service_name', service_id)}.",
            tone="info",
        )
        _write_settings_page_context(
            source_page="system",
            target_page="history",
            entry_reason="view_service_logs",
            entry_context={"service_id": service_id, "service_name": service.get("service_name")},
        )
        st.session_state["dashboard_active_view"] = "history"
        st.rerun()
    if cols[2].button(
        "Clear Cache",
        key=f"settings_service_clear_cache_{_key(service_id)}",
        use_container_width=True,
        disabled=(not service or maintenance_decision.disabled),
        help=maintenance_decision.reason if maintenance_decision.disabled else None,
    ):
        _write_settings_audit("clear_cache", page="system", detail={"service_id": service_id, "requires_confirmation": True})
        _set_settings_result(
            "system",
            title="Cache clear requested",
            message=f"Cache clear request recorded for {service.get('service_name', service_id)}.",
            tone="warn",
        )
        st.toast("Cache clear request recorded.")
    if cols[3].button(
        "Mark Degraded",
        key=f"settings_service_degraded_{_key(service_id)}",
        use_container_width=True,
        disabled=(not service or maintenance_decision.disabled),
        help=maintenance_decision.reason if maintenance_decision.disabled else None,
    ):
        st.session_state.setdefault("settings_service_status_overrides", {})[service_id] = "Degraded"
        _write_settings_audit("mark_service_degraded", page="system", detail={"service_id": service_id, "requires_confirmation": True})
        _set_settings_result(
            "system",
            title="Service marked degraded",
            message=f"{service.get('service_name', service_id)} marked Degraded locally.",
            tone="warn",
        )
        st.rerun()
    cols[4].download_button("Export Service", data=json.dumps(service, indent=2, ensure_ascii=False), file_name=f"{_key(service_id)}.json", mime="application/json", key=f"settings_service_export_{_key(service_id)}", use_container_width=True, disabled=not service)


def _build_alert_rule_rows() -> list[dict[str, Any]]:
    policy_files = _load_policy_files()
    rows: list[dict[str, Any]] = []
    for path in policy_files:
        payload = _load_json(path)
        policy_id = str(payload.get("policy_id") or path.stem)
        actions = _actions_for_policy(path.stem)
        rows.append(
            {
                "rule_id": policy_id,
                "rule_name": path.stem.replace("_", " ").title(),
                "type": _type_for_policy(path.stem),
                "target": "All Markets" if "state" in path.stem else "Console",
                "severity": "Critical" if "state" in path.stem else ("High" if "action" in path.stem else "Medium"),
                "condition": path.name,
                "throttle": "5m" if "state" in path.stem else "policy",
                "actions": actions,
                "status": "Enabled",
                "last_triggered": "2m ago" if "state" in path.stem else "-",
                "policy_ref": policy_id,
                "path": str(path),
            }
        )
    if rows:
        return rows
    return [
        _rule_fallback("price_move_alert_15m", "Price Move Alert (15m)", "Price", "Critical", "|delta price| >= 15% in 15m", "5m", "2m ago"),
        _rule_fallback("model_edge_spike", "Model Edge Spike", "Model Edge", "High", "Edge >= 0.20", "10m", "7m ago"),
        _rule_fallback("anomaly_detected", "Anomaly Detected", "Anomaly", "High", "Anomaly Score >= 0.70", "5m", "9m ago"),
        _rule_fallback("data_freshness_stale", "Data Freshness Stale", "Data Quality", "Medium", "Freshness > 60 minutes", "30m", "15m ago"),
        _rule_fallback("source_down", "Source Down", "Data Health", "Critical", "Source Status = DOWN", "0m", "3m ago"),
        _rule_fallback("validation_coverage_low", "Validation Coverage Low", "Validation", "Medium", "Coverage < 80%", "30m", "32m ago"),
        _rule_fallback("liquidity_drop", "Liquidity Drop", "Liquidity", "Low", "Liquidity < $60k", "1h", "-"),
    ]


def _build_source_rows() -> list[dict[str, Any]]:
    payload = _load_json(SOURCE_POLICY_STATUS_JSON)
    raw_sources = payload.get("sources") if isinstance(payload, dict) else []
    raw_sources = raw_sources if isinstance(raw_sources, list) else []
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_sources):
        if not isinstance(item, dict):
            continue
        source_name = str(item.get("source_name") or item.get("source_id") or f"source_{idx}")
        freshness_minutes = _minutes(item.get("freshness_minutes") or item.get("freshness_seconds"))
        precision = _float(item.get("precision_score"), default=_precision_from_status(item.get("status")))
        coverage = _float(item.get("coverage_ratio"), default=0.78)
        rows.append(
            {
                "source_id": str(item.get("source_id") or _key(source_name)),
                "source_name": source_name,
                "provider": str(item.get("provider") or source_name.split()[0] or "-"),
                "source_type": str(item.get("source_type") or item.get("primary_use") or "Observation"),
                "primary_use": str(item.get("primary_use") or "-"),
                "priority_level": str(item.get("priority_level") or item.get("priority") or "P1"),
                "precision_score": round(precision, 2),
                "freshness_minutes": freshness_minutes,
                "freshness_label": f"{freshness_minutes}m",
                "coverage_ratio": coverage,
                "coverage_label": f"{coverage * 100:.0f}%",
                "status": _source_status(item),
                "fallback_policy": str(item.get("fallback_policy") or "-"),
                "policy_ref": str(item.get("policy_ref") or "source_policy_status.v1"),
                "last_update": str(item.get("last_update") or "14:27:12"),
            }
        )
    if rows:
        return rows
    return [
        _source_fallback("metar_airports", "METAR (Airports)", "NOAA", "Observation", 0.95, 8, 0.78, "Active"),
        _source_fallback("ecmwf_hres", "ECMWF (HRES)", "ECMWF", "Forecast", 0.92, 15, 0.92, "Active"),
        _source_fallback("hrrr", "HRRR", "NOAA", "Forecast", 0.88, 12, 0.85, "Active"),
        _source_fallback("gfs", "GFS", "NOAA", "Forecast", 0.86, 21, 0.92, "Active"),
        _source_fallback("environment_canada", "Environment Canada", "EC", "Observation", 0.82, 19, 0.34, "Active"),
        _source_fallback("weather_gov_alerts", "Weather.gov Alerts", "NOAA", "Alerts", 0.90, 5, 1.00, "Active"),
        _source_fallback("open_meteo", "Open-Meteo API", "Open-Meteo", "Observation", 0.75, 47, 0.40, "Degraded"),
        _source_fallback("custom_s3", "Custom S3 Bucket", "Internal", "Custom", 0.0, 92, 0.15, "Degraded"),
    ]


def _build_system_state() -> dict[str, Any]:
    unified = _load_json(UNIFIED_STATUS_JSON)
    monitoring = _load_json(MONITORING_STATUS_JSON)
    raw_services = monitoring.get("workers") if isinstance(monitoring.get("workers"), list) else monitoring.get("services")
    raw_services = raw_services if isinstance(raw_services, list) else []
    services = []
    for idx, item in enumerate(raw_services):
        if not isinstance(item, dict):
            continue
        name = str(item.get("label") or item.get("worker") or item.get("service_name") or f"Service {idx + 1}")
        services.append(
            {
                "service_id": str(item.get("service_id") or item.get("worker") or _key(name)),
                "service_name": name,
                "component": str(item.get("component") or "Runtime"),
                "status": _service_status(item),
                "uptime": str(item.get("uptime") or "12d 4h"),
                "last_restart": str(item.get("last_restart") or item.get("last_success_at") or "-"),
                "version": str(item.get("version") or "v3.2.0"),
                "health_score": _float(item.get("health_score"), default=0.98),
            }
        )
    if not services:
        services = [
            _service_fallback("data_ingestion", "Data Ingestion Service", "Pipeline"),
            _service_fallback("scanner_engine", "Scanner Engine", "Scanner"),
            _service_fallback("comparison_engine", "Comparison Engine", "Comparison"),
            _service_fallback("alert_engine", "Alert Engine", "Alerting"),
            _service_fallback("anomaly_engine", "Anomaly Engine", "Anomaly"),
            _service_fallback("opportunity_engine", "Opportunity Engine", "Opportunity"),
            _service_fallback("validation_engine", "Validation Engine", "Validation"),
            _service_fallback("gateway_service", "Gateway Service", "Gateway"),
        ]
    return {
        "overall_status": str(monitoring.get("overall_status") or unified.get("overall_status") or "Healthy").title(),
        "cpu": str(unified.get("cpu_usage") or "24%"),
        "memory": str(unified.get("memory_usage") or "61%"),
        "disk": str(unified.get("disk_usage") or "48%"),
        "errors_24h": str(unified.get("errors_24h") or "3"),
        "alerts_24h": str(unified.get("alerts_24h") or "14"),
        "services": services,
        "recent_events": _system_events(unified, monitoring),
        "system_information": {
            "environment": str(unified.get("environment") or "Production"),
            "version": str(unified.get("version") or "v3.2.0"),
            "region": str(unified.get("region") or "us-east-1"),
            "deployed_at": str(unified.get("generated_at") or "2026-04-20 02:14 UTC"),
            "uptime": str(monitoring.get("uptime") or "12d 4h 23m"),
        },
    }


def _rule_fallback(rule_id: str, name: str, rule_type: str, severity: str, condition: str, throttle: str, last: str) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "rule_name": name,
        "type": rule_type,
        "target": "All Markets" if rule_type not in {"Data Health", "Data Quality"} else "All Sources",
        "severity": severity,
        "condition": condition,
        "throttle": throttle,
        "actions": ["Telegram", "Dashboard", "Ops Log"] if severity in {"Critical", "High"} else ["Dashboard", "Ops Log"],
        "status": "Enabled" if rule_type != "Liquidity" else "Disabled",
        "last_triggered": last,
        "policy_ref": "alert_rule_registry.default.v1",
        "path": "-",
    }


def _source_fallback(source_id: str, name: str, provider: str, source_type: str, precision: float, freshness: int, coverage: float, status: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_name": name,
        "provider": provider,
        "source_type": source_type,
        "primary_use": source_type,
        "priority_level": "P1",
        "precision_score": precision,
        "freshness_minutes": freshness,
        "freshness_label": f"{freshness}m",
        "coverage_ratio": coverage,
        "coverage_label": f"{coverage * 100:.0f}%",
        "status": status,
        "fallback_policy": "standard fallback chain",
        "policy_ref": "source_policy_status.v1",
        "last_update": "14:27:12",
    }


def _service_fallback(service_id: str, name: str, component: str) -> dict[str, Any]:
    return {
        "service_id": service_id,
        "service_name": name,
        "component": component,
        "status": "Running",
        "uptime": "12d 4h",
        "last_restart": "2026-04-24T02:12:00Z",
        "version": "v3.2.0",
        "health_score": 0.99,
    }


def _notification_channel_rows() -> list[dict[str, Any]]:
    rows = [
        {"channel": "Telegram", "status": "Enabled", "scope": "Critical, High", "latency": "2s", "sent_24h": "34 sent"},
        {"channel": "Dashboard", "status": "Enabled", "scope": "All severities", "latency": "<1s", "sent_24h": "108 rendered"},
        {"channel": "Ops Log", "status": "Enabled", "scope": "All events", "latency": "<1s", "sent_24h": "182 written"},
        {"channel": "Email", "status": "Testing", "scope": "Critical only", "latency": "12s", "sent_24h": "4 sent"},
        {"channel": "Webhook", "status": "Disabled", "scope": "-", "latency": "-", "sent_24h": "-"},
    ]
    _apply_record_overrides(rows, state_key="settings_notification_channel_overrides", id_field="channel")
    return rows


def _measurement_mapping_rows() -> list[dict[str, Any]]:
    rows = [
        {"variable": "temperature", "raw": "raw F/C", "canonical": "celsius", "rounding": "1 decimal", "policy": "temperature_policy.v1"},
        {"variable": "rainfall", "raw": "mm/in", "canonical": "mm", "rounding": "1 decimal", "policy": "rainfall_policy.v1"},
        {"variable": "wind", "raw": "mph/kmh/ms", "canonical": "m/s", "rounding": "1 decimal", "policy": "wind_policy.v1"},
    ]
    _apply_record_overrides(rows, state_key="settings_measurement_mapping_overrides", id_field="variable")
    return rows


def _user_access_rows() -> list[dict[str, Any]]:
    rows = [
        {"user": "operator_local", "role": "Operator", "status": "Active"},
        {"user": "system", "role": "Service", "status": "Active"},
        {"user": "auditor", "role": "Read-only", "status": "Testing"},
    ]
    _apply_record_overrides(rows, state_key="settings_user_access_overrides", id_field="user")
    return rows


def _filter_records(
    records: list[dict[str, Any]],
    *,
    query: str,
    query_fields: list[str],
    exact_filters: dict[str, str],
    contains_filters: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    needle = query.strip().lower()
    contains_filters = contains_filters or {}
    filtered: list[dict[str, Any]] = []
    for record in records:
        if needle and needle not in " ".join(str(record.get(field) or "") for field in query_fields).lower():
            continue
        skip = False
        for field, expected in exact_filters.items():
            if expected != "All" and str(record.get(field) or "") != expected:
                skip = True
                break
        if skip:
            continue
        for field, expected in contains_filters.items():
            if expected == "All":
                continue
            value = record.get(field)
            if isinstance(value, list):
                skip = expected not in value
            else:
                skip = expected not in str(value or "")
            if skip:
                break
        if not skip:
            filtered.append(record)
    return filtered


def _apply_record_overrides(records: list[dict[str, Any]], *, state_key: str, id_field: str) -> None:
    overrides = st.session_state.setdefault(state_key, {})
    if not isinstance(overrides, dict):
        return
    for record in records:
        record_id = str(record.get(id_field) or "")
        patch = overrides.get(record_id)
        if record_id and isinstance(patch, dict):
            record.update(patch)


def _store_record_override(*, state_key: str, record_id: str, patch: dict[str, Any]) -> None:
    bucket = st.session_state.setdefault(state_key, {})
    if not isinstance(bucket, dict):
        bucket = {}
        st.session_state[state_key] = bucket
    bucket[str(record_id)] = dict(patch)


def _clear_record_override(*, state_key: str, record_id: str) -> None:
    bucket = st.session_state.setdefault(state_key, {})
    if isinstance(bucket, dict):
        bucket.pop(str(record_id), None)


def _write_settings_audit(action: str, *, page: str, detail: dict[str, Any] | None = None) -> None:
    path = OUTPUT_DIR / "ui_action_audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": "ui_action_event.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "page": page,
        "action": action,
        "market_id": "",
        "operator_id": "operator_local",
        "action_result": "recorded",
        "requires_confirmation": bool((detail or {}).get("requires_confirmation")),
        "detail": detail or {},
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _write_settings_page_context(
    *,
    source_page: str,
    target_page: str,
    entry_reason: str,
    entry_context: dict[str, Any] | None = None,
) -> None:
    payload = {
        "schema_version": "page_context.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_page": source_page,
        "target_page": target_page,
        "selected_market_id": None,
        "selected_signal_id": None,
        "selected_row_id": "",
        "entry_reason": entry_reason,
        "entry_context": entry_context if isinstance(entry_context, dict) else {},
        "upstream_refs": {},
    }
    st.session_state["dashboard_page_context"] = payload
    PAGE_CONTEXT_JSON.parent.mkdir(parents=True, exist_ok=True)
    PAGE_CONTEXT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _current_page_context_summary(page: str, active_tab: str, selection_label: str, selection_value: str) -> None:
    _render_settings_context_strip(active_tab, selection_label, selection_value, f"Page: {page}")


def _load_policy_files() -> list[Path]:
    if not UI_POLICY_REGISTRY_DIR.exists():
        return []
    return sorted([path for path in UI_POLICY_REGISTRY_DIR.glob("*.json") if path.is_file()])


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    except Exception:
        return []
    return rows


def _unique(records: list[dict[str, Any]], key: str) -> list[str]:
    values = [str(record.get(key) or "-") for record in records]
    return sorted({value for value in values if value and value != "-"})


def _count_where(records: list[dict[str, Any]], key: str, value: str) -> int:
    return sum(1 for record in records if str(record.get(key) or "") == value)


def _severity_count(records: list[dict[str, Any]], severity: str) -> int:
    count = _count_where(records, "severity", severity)
    return count if count else (7 if severity == "Critical" else 0)


def _average_float(records: list[dict[str, Any]], key: str) -> float:
    values = [_float(record.get(key), default=-1) for record in records]
    values = [value for value in values if value >= 0]
    return sum(values) / len(values) if values else 0.0


def _average_minutes(records: list[dict[str, Any]], key: str) -> str:
    value = _average_float(records, key)
    return f"{value:.0f}" if value else "-"


def _actions_for_policy(stem: str) -> list[str]:
    if "navigation" in stem:
        return ["Dashboard", "Ops Log"]
    if "visibility" in stem or "action" in stem:
        return ["Dashboard", "Telegram", "Ops Log"]
    return ["Dashboard", "Ops Log"]


def _type_for_policy(stem: str) -> str:
    if "action" in stem:
        return "Action"
    if "navigation" in stem:
        return "Navigation"
    if "legend" in stem or "color" in stem:
        return "Legend"
    if "state" in stem:
        return "State"
    return "Policy"


def _source_status(item: dict[str, Any]) -> str:
    raw = str(item.get("status") or "").lower()
    if raw in {"fresh", "active", "live", "ok", "healthy"}:
        return "Active"
    if raw in {"stale", "degraded", "warning"}:
        return "Degraded"
    if raw in {"down", "unavailable", "failed"}:
        return "Down"
    return "Active"


def _service_status(item: dict[str, Any]) -> str:
    raw = str(item.get("status") or "").lower()
    if raw in {"running", "live", "ok", "healthy", "fresh", "active"}:
        return "Running"
    if raw in {"degraded", "stale", "warning"}:
        return "Degraded"
    if raw in {"down", "failed", "unavailable"}:
        return "Down"
    return "Running"


def _precision_from_status(status: Any) -> float:
    normalized = str(status or "").lower()
    if normalized in {"fresh", "active", "live", "ok", "healthy"}:
        return 0.90
    if normalized in {"stale", "degraded", "warning"}:
        return 0.68
    if normalized in {"down", "unavailable", "failed"}:
        return 0.30
    return 0.75


def _minutes(value: Any) -> int:
    number = _float(value, default=18.0)
    if number > 180:
        number = number / 60.0
    return max(0, int(round(number)))


def _float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _system_events(unified: dict[str, Any], monitoring: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for source in (unified, monitoring):
        raw_events = source.get("recent_events") if isinstance(source.get("recent_events"), list) else []
        for event in raw_events:
            if isinstance(event, dict):
                events.append(event)
    if events:
        return events
    return [
        {"time": "14:32:11", "severity": "INFO", "event": "Data ingestion service restarted successfully"},
        {"time": "14:18:09", "severity": "WARN", "event": "High response time on ECMWF"},
        {"time": "13:55:32", "severity": "INFO", "event": "Backup completed successfully"},
        {"time": "12:44:21", "severity": "ERROR", "event": "Weather.gov alerts delayed (retrying)"},
        {"time": "11:23:07", "severity": "INFO", "event": "Configuration updated by operator_local"},
    ]


def _status_tone(value: Any) -> str:
    text = str(value or "").lower()
    if text in {"active", "running", "healthy", "enabled", "pass"}:
        return "good"
    if text in {"degraded", "testing", "warn", "warning"}:
        return "warn"
    if text in {"down", "disabled", "critical", "error", "failed"}:
        return "danger"
    return "info"


def _severity_tone(value: Any) -> str:
    text = str(value or "").lower()
    if text in {"critical", "red", "error"}:
        return "danger"
    if text in {"high", "medium", "warn", "warning"}:
        return "warn"
    if text in {"low", "info"}:
        return "info"
    return "good"


def _type_tone(value: Any) -> str:
    text = str(value or "").lower()
    if "quality" in text or "validation" in text:
        return "magenta"
    if "price" in text or "liquidity" in text:
        return "warn"
    if "anomaly" in text:
        return "info"
    return "good"


def _badge(value: Any, tone: str = "info") -> str:
    return f"<span class='settings-badge {_esc(tone)}'>{_esc(value)}</span>"


def _toggle(enabled: bool) -> str:
    return f"<span class='settings-toggle {'off' if not enabled else ''}'></span>"


def _icon(label: str) -> str:
    return f"<span class='settings-icon-btn'>{_esc(label)}</span>"


def _mini_action(label: str) -> str:
    return f"<span class='settings-icon-btn' title='{_esc(label)}'>{_esc(str(label)[:1])}</span>"


def _action_chip(label: Any) -> str:
    return f"<span class='settings-badge info'>{_esc(label)}</span>"


def _progress(value: Any, *, suffix: Any = "") -> str:
    number = _float(value, default=0)
    if number > 1:
        number = number / 100
    width = max(0, min(100, int(number * 100)))
    return f"<div style='display:flex;align-items:center;gap:.4rem;'><div class='settings-progress'><span style='width:{width}%'></span></div><span>{_esc(suffix)}</span></div>"


def _quality(label: Any, value: Any, note: Any) -> str:
    return f"<div class='settings-quality'><span>{_esc(label)}</span><strong>{_esc(value)}</strong><em>{_esc(note)}</em></div>"


def _kv(label: Any, value: Any, *, raw: bool = False) -> str:
    rendered_value = str(value) if raw else _esc(value)
    return f"<div class='settings-kv'><span>{_esc(label)}</span><strong>{rendered_value}</strong></div>"


def _trigger_row(item: dict[str, Any]) -> str:
    ts = item.get("generated_at") or item.get("event_at") or "-"
    reason = item.get("primary_reason") or item.get("message") or "-"
    severity = item.get("severity") or item.get("score") or "15.6%"
    return f"<div class='settings-kv'><span>{_esc(str(ts)[0:16])}</span><strong>{_esc(reason)} <span style='color:#ff493f'>{_esc(severity)}</span></strong></div>"


def _key(value: Any) -> str:
    token = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value or "").strip())
    return token.strip("_") or "item"


def _utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%H%M%S")


def _esc(value: Any) -> str:
    text = str(value if value is not None else "-")
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
