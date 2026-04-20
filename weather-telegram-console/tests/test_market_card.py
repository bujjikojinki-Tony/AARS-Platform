from weather_telegram_console.bot.formatters.market_card import format_market_card


def test_format_market_card() -> None:
    text = format_market_card(
        {
            "market_id": "mkt_123",
            "market_question": "Will NYC hit 95F?",
            "location_name": "New York City",
            "target_date": "2026-07-04",
            "variable_name": "temperature_max",
            "yes_price": 0.41,
            "no_price": 0.59,
            "market_probability": 0.41,
            "market_band": "91-95F",
            "model_value": 93.2,
            "model_band": "91-95F",
            "confidence_score": 0.77,
            "confidence_adjusted_gap": 0.06,
            "comparison_status": "aligned",
            "action_hint": "watch",
            "comparison_reason": "Bands aligned.",
            "rule_status": "eligible",
            "promotion_state": {
                "schema_version": "promotion_state.v1",
                "probability_mode": "shadow_calibrated_candidate",
                "base_probability_mode": "heuristic_not_calibrated",
                "execution_constraint": "dry_run_only",
                "base_execution_constraint": "manual_advisory_only",
                "promotion_reason": "candidate_thresholds_passed",
                "demotion_reason": None,
            },
            "market_snapshot_ref": "2026-04-18T09:00:00+00:00",
            "forecast_snapshot_ref": "2026-04-18T09:05:00+00:00",
            "compact_gate_stack": {
                "resolver_gate": "blocked",
                "resolver_gate_reasons": ["resolver_confidence_low"],
            },
            "advisory_summary": {
                "event_count": 1,
                "latest_event_type": "operator_acknowledged_manual_advisory",
                "latest_created_at": "2026-04-18T09:10:00+00:00",
                "latest_decision": "operator_acknowledged",
                "latest_gate_status": None,
                "latest_price": 0.44,
                "latest_size": 12,
            },
            "data_availability": {
                "manual_advisory_audit_available": True,
            },
        }
    )

    assert "AARS Market Snapshot" in text
    assert "Will NYC hit 95F?" in text
    assert "93.2" in text
    assert "Bands aligned." in text
    assert "Promotion State" in text
    assert "candidate_thresholds_passed" in text
    assert "2026-04-18T09:05:00+00:00" in text
    assert "Resolver Gate" in text
    assert "resolver_confidence_low" in text
    assert "audit events recorded" in text


def test_format_market_card_shows_missing_audit_file_hint() -> None:
    text = format_market_card(
        {
            "market_id": "mkt_404",
            "advisory_summary": {"event_count": 0},
            "data_availability": {"manual_advisory_audit_available": False},
        }
    )

    assert "manual advisory audit file is not available" in text
