from weather_telegram_console.bot.formatters.operations_monitor_card import format_operations_monitor_card


def test_format_operations_monitor_card() -> None:
    text = format_operations_monitor_card(
        {
            "global_summary": {
                "markets_scanned": 18,
                "focus_markets_count": 4,
                "fresh_ratio": "0.56",
                "high_alert_markets": 2,
                "gate_blocked_markets": 1,
                "ops_alert_count": 3,
            },
            "focus_markets": [
                {"city": "Shanghai", "market_family": "temperature_daily_max", "focus_reason": "selected, alert=amber"},
                {"city": "Miami", "market_family": "temperature_daily_max", "focus_reason": "opp=0.89"},
            ],
            "system_health": {
                "scanner_health": {"status": "healthy", "scanned_markets": 18, "fresh_markets": 10, "stale_markets": 8},
                "source_health": {
                    "overall_status": "blocked",
                    "counts": {"fresh": 5, "stale": 1, "unavailable": 7},
                    "problem_sources": [{"source_name": "polymarket_clob", "freshness_status": "unavailable", "status_reason": "past_stale_threshold"}],
                },
                "queue_health": {"accepted_count": 0, "suppressed_count": 0},
                "family_scan_health": {"market_family": "temperature_daily_max", "family_risk_summary": "stable"},
            },
            "selected_market_quick_detail": {
                "market_id": "397991",
                "market_question": "Highest temperature in Shanghai on April 22?",
                "recommended_operator_action": "review_market",
                "execution_boundary": "dry_run_only",
            },
            "ops_alerts": [{"component": "scanner", "severity": "amber", "primary_reason": "backlog"}],
            "summary": {"primary_warning": "scanner degraded"},
        }
    )

    assert "AARS Operations Monitor" in text
    assert "Markets Scanned" in text
    assert "Focus Markets" in text
    assert "Scanner Health" in text
    assert "Source Health" in text
    assert "Selected Market" in text
    assert "scanner" in text.lower()
