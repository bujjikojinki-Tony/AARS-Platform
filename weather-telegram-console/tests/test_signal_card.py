from weather_telegram_console.bot.formatters.signal_card import format_signal_card


def test_format_signal_card():
    payload = {
        "market_id": "sample_market_001",
        "location_name": "Central Park",
        "target_date": "2026-04-12",
        "variable_name": "daily_max_temperature",
        "model_value": 28.1,
        "model_band": "28",
        "market_band": "27",
        "edge_direction": "divergent",
        "edge_strength": 1.0,
        "execution_mode": "manual_advisory",
        "probability_mode": "heuristic_not_calibrated",
        "execution_constraint": "manual_advisory_only",
        "manual_order_required": True,
        "autonomous_execution_allowed": False,
        "manual_trade_ticket": {
            "recommended_side": "buy",
            "limit_price": 0.61,
            "size": 10,
        },
        "confidence": {
            "score": 0.91,
            "level": "high",
            "reasons": ["market_context_available", "forecast_stable"],
        },
        "action_hint": "approve_small",
    }

    text = format_signal_card(
        payload,
        approval_status="已审批",
        approval_expires_at="2026-04-12T12:15:00+00:00",
    )

    assert "Weather Signal Alert" in text
    assert "Central Park" in text
    assert "approve_small" in text
    assert "已审批" in text
    assert "manual_advisory" in text
    assert "heuristic_not_calibrated" in text
    assert "BOT提醒与记录，不代表自动下单" in text
