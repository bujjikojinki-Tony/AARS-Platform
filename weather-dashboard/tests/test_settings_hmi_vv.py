from __future__ import annotations

import json

import weather_dashboard.ui.settings_pages as settings_pages


def test_settings_audit_events_include_hmi_vv_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings_pages, "OUTPUT_DIR", tmp_path)

    settings_pages._write_settings_audit(
        "disable_source",
        page="data_sources",
        detail={"source_id": "metar_airports", "requires_confirmation": True},
    )

    [event_line] = (tmp_path / "ui_action_audit.jsonl").read_text(encoding="utf-8").splitlines()
    event = json.loads(event_line)

    assert event["schema_version"] == "ui_action_event.v1"
    assert event["page"] == "data_sources"
    assert event["action"] == "disable_source"
    assert event["operator_id"] == "operator_local"
    assert event["action_result"] == "recorded"
    assert event["requires_confirmation"] is True
    assert event["detail"]["source_id"] == "metar_airports"


def test_settings_page_context_persists_navigation_contract(tmp_path, monkeypatch) -> None:
    context_path = tmp_path / "page_context.json"
    monkeypatch.setattr(settings_pages, "PAGE_CONTEXT_JSON", context_path)

    settings_pages._write_settings_page_context(
        source_page="system",
        target_page="history",
        entry_reason="view_service_logs",
        entry_context={"service_id": "scanner_engine"},
    )

    context = json.loads(context_path.read_text(encoding="utf-8"))

    assert context["schema_version"] == "page_context.v1"
    assert context["source_page"] == "system"
    assert context["target_page"] == "history"
    assert context["selected_market_id"] is None
    assert context["entry_reason"] == "view_service_logs"
    assert context["entry_context"]["service_id"] == "scanner_engine"


def test_settings_page_context_includes_selected_object_context(tmp_path, monkeypatch) -> None:
    context_path = tmp_path / "page_context.json"
    monkeypatch.setattr(settings_pages, "PAGE_CONTEXT_JSON", context_path)

    settings_pages._write_settings_page_context(
        source_page="settings",
        target_page="alerts_rules",
        entry_reason="inspect_rule",
        entry_context={
            "active_tab": "Alert Rules",
            "selected_rule_id": "primary_state_policy.default.v1",
            "selected_rule_name": "Primary State Policy",
            "selected_rule_type": "state",
        },
    )

    context = json.loads(context_path.read_text(encoding="utf-8"))

    assert context["schema_version"] == "page_context.v1"
    assert context["source_page"] == "settings"
    assert context["target_page"] == "alerts_rules"
    assert context["entry_context"]["active_tab"] == "Alert Rules"
    assert context["entry_context"]["selected_rule_id"] == "primary_state_policy.default.v1"
    assert context["entry_context"]["selected_rule_name"] == "Primary State Policy"


def test_settings_action_result_state_is_persisted(monkeypatch) -> None:
    monkeypatch.setitem(settings_pages.st.session_state, "settings_page_results", {})

    settings_pages._set_settings_result(
        "alerts_rules",
        title="Rule enabled",
        message="Primary State Policy is now Enabled.",
        tone="good",
    )

    result = settings_pages.st.session_state["settings_page_results"]["alerts_rules"]
    assert result["title"] == "Rule enabled"
    assert result["message"] == "Primary State Policy is now Enabled."
    assert result["tone"] == "good"
    assert "updated_at" in result


def test_settings_record_overrides_are_applied_and_reset(monkeypatch) -> None:
    monkeypatch.setitem(
        settings_pages.st.session_state,
        "settings_alert_rule_overrides",
        {
            "price_move_alert_15m": {
                "status": "Testing",
                "severity": "High",
                "throttle": "15m",
            }
        },
    )
    records = [
        {
            "rule_id": "price_move_alert_15m",
            "rule_name": "Price Move Alert (15m)",
            "status": "Enabled",
            "severity": "Critical",
            "throttle": "5m",
        }
    ]

    settings_pages._apply_record_overrides(records, state_key="settings_alert_rule_overrides", id_field="rule_id")

    assert records[0]["status"] == "Testing"
    assert records[0]["severity"] == "High"
    assert records[0]["throttle"] == "15m"

    settings_pages._clear_record_override(state_key="settings_alert_rule_overrides", record_id="price_move_alert_15m")

    assert settings_pages.st.session_state["settings_alert_rule_overrides"] == {}


def test_settings_store_record_override_persists_patch(monkeypatch) -> None:
    monkeypatch.setitem(settings_pages.st.session_state, "settings_source_overrides", {})

    settings_pages._store_record_override(
        state_key="settings_source_overrides",
        record_id="metar_airports",
        patch={"status": "Degraded", "freshness_minutes": 12},
    )

    stored = settings_pages.st.session_state["settings_source_overrides"]["metar_airports"]
    assert stored["status"] == "Degraded"
    assert stored["freshness_minutes"] == 12


def test_secondary_settings_registries_apply_local_overrides(monkeypatch) -> None:
    monkeypatch.setitem(
        settings_pages.st.session_state,
        "settings_notification_channel_overrides",
        {"Telegram": {"status": "Testing", "latency": "5s"}},
    )
    monkeypatch.setitem(
        settings_pages.st.session_state,
        "settings_measurement_mapping_overrides",
        {"temperature": {"canonical": "fahrenheit", "rounding": "integer"}},
    )
    monkeypatch.setitem(
        settings_pages.st.session_state,
        "settings_user_access_overrides",
        {"auditor": {"role": "Auditor", "status": "Active"}},
    )

    channels = settings_pages._notification_channel_rows()
    mappings = settings_pages._measurement_mapping_rows()
    users = settings_pages._user_access_rows()

    telegram = next(row for row in channels if row["channel"] == "Telegram")
    temperature = next(row for row in mappings if row["variable"] == "temperature")
    auditor = next(row for row in users if row["user"] == "auditor")

    assert telegram["status"] == "Testing"
    assert telegram["latency"] == "5s"
    assert temperature["canonical"] == "fahrenheit"
    assert temperature["rounding"] == "integer"
    assert auditor["role"] == "Auditor"
    assert auditor["status"] == "Active"
