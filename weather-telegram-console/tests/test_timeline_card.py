from weather_telegram_console.bot.formatters.timeline_card import format_timeline_card


def test_format_timeline_card() -> None:
    text = format_timeline_card(
        "mkt_123",
        [
            {
                "timestamp": "2026-04-18T09:00:00+00:00",
                "comparison_status": "aligned",
                "action_hint": "watch",
                "market_band": "91-95F",
                "model_band": "91-95F",
                "model_value": 93.1,
                "confidence_adjusted_gap": 0.03,
                "confidence_score": 0.81,
                "market_snapshot_ref": "2026-04-18T08:59:00+00:00",
                "forecast_snapshot_ref": "2026-04-18T08:58:00+00:00",
            },
            {
                "timestamp": "2026-04-18T08:00:00+00:00",
                "comparison_status": "edge_yes",
                "action_hint": "review_manual_trade",
                "market_band": "86-90F",
                "model_band": "91-95F",
                "model_value": 92.7,
                "confidence_adjusted_gap": 0.07,
                "confidence_score": 0.84,
                "market_snapshot_ref": "2026-04-18T07:59:00+00:00",
                "forecast_snapshot_ref": "2026-04-18T07:58:00+00:00",
            },
        ],
    )

    assert "AARS Market Timeline" in text
    assert "mkt_123" in text
    assert "review_manual_trade" in text
    assert "2026-04-18T09:00:00+00:00" in text
    assert "m_ref=`2026-04-18T08:59:00+00:00`" in text
