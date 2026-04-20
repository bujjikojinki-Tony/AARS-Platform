from weather_telegram_console.bot.formatters.status_card import format_status_card


def test_format_status_card() -> None:
    report = {
        "overall_status": "guarded",
        "generated_at": "2026-04-18T09:00:00+00:00",
        "current_market": {
            "market_id": "678686",
            "market_question": "Will 2026 be the hottest year on record?",
            "comparison_status": "aligned",
            "action_hint": "watch",
        },
        "monitoring": {
            "overall_status": "healthy",
            "worker_count": 3,
            "counts": {"healthy": 3, "warning": 0, "stale": 0, "missing": 0},
            "workers": [
                {"label": "Market", "status": "healthy"},
                {"label": "Forecast", "status": "healthy"},
            ],
        },
        "probability": {
            "contract_version": "probability_contract.v1",
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
            "calibration_status": "not_calibrated",
            "confidence_adjusted_edge": 0.04,
            "promotion_state": {
                "schema_version": "promotion_state.v1",
                "probability_mode": "heuristic_not_calibrated",
                "base_probability_mode": "heuristic_not_calibrated",
                "execution_constraint": "manual_advisory_only",
                "base_execution_constraint": "manual_advisory_only",
                "promotion_reason": "thresholds_not_met",
                "demotion_reason": "validation_freshness_unhealthy",
                "approved_for_live": False,
            },
        },
        "execution": {
            "status": "blocked",
            "ready_for_live": False,
            "decision": "LIVE_EXECUTION_BLOCKED",
            "blocking_count": 2,
        },
        "operator": {
            "can_bot_trade": False,
            "human_action_required": True,
            "execution_mode": "manual_advisory_only",
            "operator_mode": "dry_run_guarded",
            "mode_badge": {"label": "DRY-RUN GUARDED"},
        },
        "gate_stack": {
            "data_gate": "pass",
            "resolver_gate": "blocked",
            "probability_gate": "blocked",
            "freshness_gate": "pass",
            "authorization_gate": "blocked",
            "execution_gate": "blocked",
        },
        "block_reasons": [
            "probability_mode:heuristic_not_calibrated",
            "execution:blocked",
        ],
    }

    text = format_status_card(report)

    assert "AARS Unified Status" in text
    assert "heuristic_not_calibrated" in text
    assert "LIVE_EXECUTION_BLOCKED" in text
    assert "Will 2026 be the hottest year on record?" in text
    assert "DRY-RUN GUARDED" in text
    assert "probability_contract.v1" in text
    assert "Promotion State" in text
    assert "validation_freshness_unhealthy" in text
    assert "Gate Stack" in text
    assert "Authorization Gate" in text
