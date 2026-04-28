from pathlib import Path

from weather_dashboard.ui.execution_gate_panel import (
    build_execution_gate_state,
    build_order_intent,
    build_readiness_operator_checklist,
    create_local_test_approval,
    ensure_market_in_dev_whitelist,
    build_telegram_approval_signal,
    load_production_readiness_report,
    load_latest_approval_status,
    write_order_intent,
)


def test_execution_gate_blocks_without_authorization(tmp_path: Path):
    whitelist = tmp_path / "whitelist_markets.yaml"
    whitelist.write_text("markets:\n  - m1\n", encoding="utf-8")

    state = build_execution_gate_state(
        market_snapshot={
            "market_id": "m1",
            "favored_side": "yes",
            "yes_price": 0.61,
        },
        forecast_snapshot={"market_id": "m1"},
        resolver_rule={"market_id": "m1", "resolver_status": "matched"},
        probability_state={
            "market_id": "m1",
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
        },
        comparison_row={"market_id": "m1", "comparison_status": "aligned"},
        bot_authorized=False,
        whitelist_path=whitelist,
    )

    assert state["data_aligned"] is True
    assert state["can_write_intent"] is False
    assert state["probability_mode"] == "heuristic_not_calibrated"
    assert state["promotion_state"] == "heuristic_not_calibrated"
    assert state["promotion_reason"] == "-"
    assert state["demotion_reason"] == "-"
    assert "bot_not_authorized" in state["blockers"]


def test_execution_gate_blocks_when_resolver_source_is_not_exact(tmp_path: Path):
    whitelist = tmp_path / "whitelist_markets.yaml"
    whitelist.write_text("markets:\n  - m1\n", encoding="utf-8")

    state = build_execution_gate_state(
        market_snapshot={
            "market_id": "m1",
            "favored_side": "yes",
            "yes_price": 0.61,
        },
        forecast_snapshot={"market_id": "m1"},
        resolver_rule={
            "market_id": "m1",
            "resolver_status": "matched",
            "source_match_grade": "family_only",
            "official_vs_proxy_source": "fallback",
        },
        probability_state={
            "market_id": "m1",
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
        },
        comparison_row={"market_id": "m1", "comparison_status": "aligned"},
        bot_authorized=True,
        whitelist_path=whitelist,
    )

    assert state["data_aligned"] is False
    assert "resolver_source_not_exact" in state["blockers"]


def test_execution_gate_blocks_when_validation_quality_is_not_green(tmp_path: Path):
    whitelist = tmp_path / "whitelist_markets.yaml"
    whitelist.write_text("markets:\n  - m1\n", encoding="utf-8")

    state = build_execution_gate_state(
        market_snapshot={"market_id": "m1", "favored_side": "yes", "yes_price": 0.61},
        forecast_snapshot={"market_id": "m1"},
        resolver_rule={"market_id": "m1", "resolver_status": "matched", "source_match_grade": "exact_station", "official_vs_proxy_source": "official"},
        probability_state={
            "market_id": "m1",
            "probability_mode": "live_approved",
            "execution_constraint": "live_execution_allowed",
        },
        comparison_row={"market_id": "m1", "comparison_status": "aligned"},
        validation_freshness_status={"status": "warning"},
        label_coverage_report={"status": "blocked"},
        bot_authorized=True,
        whitelist_path=whitelist,
    )

    assert "validation_freshness_warning" in state["blockers"]
    assert "label_coverage_blocked" in state["blockers"]


def test_execution_gate_writes_valid_pending_intent(tmp_path: Path):
    whitelist = tmp_path / "whitelist_markets.yaml"
    whitelist.write_text("markets:\n  - m1\n", encoding="utf-8")

    state = build_execution_gate_state(
        market_snapshot={
            "market_id": "m1",
            "favored_side": "yes",
            "yes_price": 0.61,
        },
        forecast_snapshot={"market_id": "m1"},
        resolver_rule={"market_id": "m1", "resolver_status": "matched"},
        probability_state={
            "market_id": "m1",
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
        },
        comparison_row={"market_id": "m1", "comparison_status": "aligned"},
        bot_authorized=True,
        whitelist_path=whitelist,
    )

    intent = build_order_intent(state)
    pending_path = write_order_intent(
        intent=intent,
        pending_intents_dir=tmp_path / "pending_intents",
        latest_intent_path=tmp_path / "dashboard_intent_preview.json",
    )

    assert state["gateway_ready"] is True
    assert intent["market_id"] == "m1"
    assert intent["schema_version"] == "execution_intent.v1"
    assert intent["side"] == "buy"
    assert intent["price"] == 0.61
    assert intent["decision_ref"].startswith("decision_dashboard_m1_")
    assert intent["authorization_ref"] == "approval_required"
    assert intent["probability_mode"] == "heuristic_not_calibrated"
    assert intent["contract_version"] == "probability_contract.v1"
    assert intent["probability_contract"]["probability_mode"] == "heuristic_not_calibrated"
    assert intent["probability_contract"]["execution_constraint"] == "manual_advisory_only"
    assert pending_path.exists()
    assert (tmp_path / "dashboard_intent_preview.json").exists()


def test_execution_gate_writes_telegram_approval_signal(tmp_path: Path):
    intent = {
        "intent_id": "intent_dashboard_123",
        "market_id": "m1",
        "signal_id": "dashboard_m1_123",
        "side": "buy",
        "price": 0.61,
        "size": 10.0,
    }
    signal_path = tmp_path / "dashboard_approval_signal.json"
    audit_path = tmp_path / "manual_advisory_audit.jsonl"

    pending_path = write_order_intent(
        intent=intent,
        pending_intents_dir=tmp_path / "pending_intents",
        latest_intent_path=tmp_path / "dashboard_intent_preview.json",
        telegram_signal_path=signal_path,
        manual_advisory_audit_path=audit_path,
        gate={"gate_status": "READY"},
        market_snapshot={"market_id": "m1", "location_name": "Central Park", "market_band": "28"},
        forecast_snapshot={"market_id": "m1", "target_date": "2026-04-12", "model_band": "28"},
        probability_state={
            "confidence_adjusted_edge": 0.12,
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
        },
        comparison_row={"action_hint": "approve_small"},
    )

    assert pending_path.exists()
    assert signal_path.exists()
    text = signal_path.read_text(encoding="utf-8")
    assert "intent_dashboard_123" in text
    assert "dashboard_m1_123" in text
    assert "heuristic_not_calibrated" in text
    audit_text = audit_path.read_text(encoding="utf-8")
    assert "manual_advisory_signal_created" in audit_text
    assert "manual_order_required" in audit_text


def test_build_telegram_approval_signal_uses_intent_identity():
    signal = build_telegram_approval_signal(
        intent={
            "intent_id": "intent_dashboard_123",
            "market_id": "m1",
            "signal_id": "dashboard_m1_123",
            "side": "buy",
            "price": 0.61,
            "size": 10.0,
        },
        gate={"gate_status": "READY"},
        probability_state={
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
        },
    )

    assert signal["signal_id"] == "dashboard_m1_123"
    assert signal["intent_id"] == "intent_dashboard_123"
    assert signal["execution_mode"] == "manual_advisory"
    assert signal["probability_mode"] == "heuristic_not_calibrated"
    assert signal["execution_constraint"] == "manual_advisory_only"
    assert signal["probability_contract"]["contract_version"] == "probability_contract.v1"
    assert signal["approval_context"]["probability_contract"]["probability_mode"] == "heuristic_not_calibrated"
    assert signal["manual_order_required"] is True
    assert signal["autonomous_execution_allowed"] is False
    assert signal["approval_context"]["intent_id"] == "intent_dashboard_123"
    assert signal["approval_context"]["approval_purpose"] == "operator_review_not_auto_execution"


def test_dev_whitelist_add_is_idempotent(tmp_path: Path):
    path = tmp_path / "whitelist_markets.yaml"

    first = ensure_market_in_dev_whitelist(path, "m1")
    second = ensure_market_in_dev_whitelist(path, "m1")

    text = path.read_text(encoding="utf-8")
    assert first is True
    assert second is False
    assert text.count("- m1") == 1


def test_create_local_test_approval(tmp_path: Path):
    db_path = tmp_path / "weather_telegram_console.db"
    intent = {
        "intent_id": "intent_1",
        "signal_id": "sig_1",
    }

    approval = create_local_test_approval(db_path=db_path, intent=intent)

    assert db_path.exists()
    assert approval["intent_id"] == "intent_1"
    assert approval["signal_id"] == "sig_1"
    assert approval["decision"] == "approve_small"


def test_load_latest_approval_status_by_intent_id(tmp_path: Path):
    db_path = tmp_path / "weather_telegram_console.db"
    intent = {
        "intent_id": "intent_1",
        "signal_id": "sig_1",
    }
    approval = create_local_test_approval(db_path=db_path, intent=intent)

    loaded = load_latest_approval_status(
        db_path=db_path,
        intent_id="intent_1",
        signal_id=None,
    )

    assert loaded is not None
    assert loaded["approval_id"] == approval["approval_id"]
    assert loaded["status"] == "已审批"


def test_load_production_readiness_report(tmp_path: Path):
    path = tmp_path / "production_readiness_report.json"
    path.write_text(
        '{"ready_for_live": false, "decision": "LIVE_EXECUTION_BLOCKED"}',
        encoding="utf-8",
    )

    loaded = load_production_readiness_report(path)

    assert loaded is not None
    assert loaded["decision"] == "LIVE_EXECUTION_BLOCKED"


def test_build_readiness_operator_checklist_groups_statuses():
    groups = build_readiness_operator_checklist(
        {
            "decision": "LIVE_EXECUTION_BLOCKED",
            "checks": [
                {
                    "name": "live_mode_policy",
                    "status": "blocked",
                    "message": "Live-mode policy is disabled.",
                    "details": {"enabled": False},
                },
                {
                    "name": "approval_probe",
                    "status": "warning",
                    "message": "Approval expired.",
                    "details": {"reason": "latest_approval_expired"},
                },
                {
                    "name": "position_exposure",
                    "status": "passed",
                    "message": "Snapshot available.",
                    "details": {"total_notional": 0.0},
                },
            ],
        }
    )

    assert groups["counts"]["blocked"] == 1
    assert groups["counts"]["warning"] == 1
    assert groups["counts"]["passed"] == 1
    assert groups["blocked"][0]["name"] == "live_mode_policy"
    assert "Live execution is blocked" in groups["operator_note"]
